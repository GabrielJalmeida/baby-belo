
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_context(db):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"stock-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )

    company = Empresa(
        nome=f"Empresa {uuid4().hex}",
        ativo=True,
    )
    db.add(company)
    db.flush()

    membership = EmpresaUsuario(
        empresa_id=company.id,
        usuario_id=user.id,
        papel="OWNER",
        ativo=True,
    )

    unit = Unidade(
        empresa_id=company.id,
        nome=f"Unidade {uuid4().hex[:12]}",
        simbolo="UN",
        permite_decimal=True,
        ativo=True,
    )

    db.add_all([membership, unit])
    db.flush()

    item = Item(
        empresa_id=company.id,
        unidade_id=unit.id,
        nome="Item de teste",
        estoque_minimo=Decimal("2.0000"),
        ativo=True,
    )

    db.add(item)
    db.commit()

    token = create_access_token(subject=str(user.id))

    return user, company, membership, unit, item, {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }


def cleanup_context(db, user, company, membership):
    db.query(Item).filter(
        Item.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.query(Unidade).filter(
        Unidade.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.delete(membership)
    db.delete(company)
    db.delete(user)
    db.commit()


def test_list_balances_requires_authentication():
    response = client.get("/api/v1/estoque/saldos")

    assert response.status_code == 401


def test_list_balances_isolated_by_company():
    db = SessionLocal()
    context_a = None
    context_b = None

    try:
        context_a = create_context(db)
        context_b = create_context(db)

        user_a, company_a, membership_a, _, item_a, headers_a = context_a
        _, company_b, _, _, item_b, _ = context_b

        response = client.get(
            "/api/v1/estoque/saldos",
            headers=headers_a,
        )

        assert response.status_code == 200

        body = response.json()
        returned_ids = {row["item_id"] for row in body}

        assert item_a.id in returned_ids
        assert item_b.id not in returned_ids

        item_row = next(
            row for row in body
            if row["item_id"] == item_a.id
        )

        assert item_row["empresa_id"] == company_a.id
        assert Decimal(str(item_row["estoque_minimo"])) == Decimal("2.0000")
        assert Decimal(str(item_row["saldo_atual"])) == Decimal("0.0000")

        cleanup_context(db, user_a, company_a, membership_a)

        user_b, company_b, membership_b, _, _, _ = context_b
        cleanup_context(db, user_b, company_b, membership_b)

    finally:
        db.close()


def test_low_stock_returns_active_items_only_for_current_company():
    db = SessionLocal()
    context_a = None
    context_b = None

    try:
        context_a = create_context(db)
        context_b = create_context(db)

        user_a, company_a, membership_a, unit_a, item_a, headers_a = context_a
        _, company_b, _, _, item_b, _ = context_b

        inactive_item = Item(
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item inativo",
            estoque_minimo=Decimal("10.0000"),
            ativo=False,
        )

        db.add(inactive_item)
        db.commit()

        response = client.get(
            "/api/v1/estoque/baixo",
            headers=headers_a,
        )

        assert response.status_code == 200

        body = response.json()
        returned_ids = {row["item_id"] for row in body}

        # Saldo zero, estoque mínimo 2: item ativo precisa de reposição.
        assert item_a.id in returned_ids

        # Itens de outra empresa e inativos não entram no alerta.
        assert item_b.id not in returned_ids
        assert inactive_item.id not in returned_ids

        item_row = next(
            row for row in body
            if row["item_id"] == item_a.id
        )

        assert item_row["empresa_id"] == company_a.id
        assert Decimal(str(item_row["saldo_atual"])) <= Decimal(
            str(item_row["estoque_minimo"])
        )

        cleanup_context(db, user_a, company_a, membership_a)

        user_b, company_b, membership_b, _, _, _ = context_b
        cleanup_context(db, user_b, company_b, membership_b)

    finally:
        db.close()

def test_stock_lists_support_pagination_and_limit_maximum():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        user, company, membership, unit, first_item, headers = context

        extra_items = [
            Item(
                empresa_id=company.id,
                unidade_id=unit.id,
                nome=f"Item extra {uuid4().hex}",
                estoque_minimo=Decimal("2.0000"),
                ativo=True,
            )
            for _ in range(2)
        ]

        db.add_all(extra_items)
        db.commit()

        expected_ids = sorted(
            [first_item.id, *(item.id for item in extra_items)]
        )

        for endpoint in (
            "/api/v1/estoque/saldos",
            "/api/v1/estoque/baixo",
        ):
            response = client.get(
                endpoint,
                params={"limit": 1, "offset": 1},
                headers=headers,
            )

            assert response.status_code == 200, response.text
            assert [
                row["item_id"] for row in response.json()
            ] == [expected_ids[1]]

            invalid_limit = client.get(
                endpoint,
                params={"limit": 101},
                headers=headers,
            )

            assert invalid_limit.status_code == 422

    finally:
        if context is not None:
            cleanup_context(
                db,
                context[0],
                context[1],
                context[2],
            )
        db.close()
