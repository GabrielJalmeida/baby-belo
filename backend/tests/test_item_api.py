
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


def create_context(db, role="OWNER", permite_decimal=True):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"item-{uuid4().hex}@example.com",
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
        papel=role,
        ativo=True,
    )

    unit = Unidade(
        empresa_id=company.id,
        nome=f"Unidade {uuid4().hex[:12]}",
        simbolo="UN",
        permite_decimal=permite_decimal,
        ativo=True,
    )

    db.add_all([membership, unit])
    db.commit()

    token = create_access_token(subject=str(user.id))

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }

    return user, company, membership, unit, headers


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


def test_create_item_requires_authentication():
    response = client.post(
        "/api/v1/itens",
        json={
            "unidade_id": 1,
            "nome": "Papel A4",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_item():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(db)

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": "Papel A4",
                "descricao": "Resma de papel",
                "estoque_minimo": "2.5000",
            },
            headers=headers,
        )

        assert response.status_code == 201

        body = response.json()

        assert body["empresa_id"] == company.id
        assert body["unidade_id"] == unit.id
        assert body["nome"] == "Papel A4"
        assert body["descricao"] == "Resma de papel"
        assert Decimal(str(body["estoque_minimo"])) == Decimal("2.5000")
        assert body["ativo"] is True

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_create_item():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            role="VIEWER",
        )

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": "Papel A4",
            },
            headers=headers,
        )

        assert response.status_code == 403

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_list_items_returns_only_active_items_from_current_company():
    db = SessionLocal()
    first_context = None
    second_context = None

    try:
        first_context = create_context(db)
        second_context = create_context(db)

        user_a, company_a, membership_a, unit_a, headers_a = first_context
        _, company_b, _, unit_b, _ = second_context

        active_item = Item(
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item ativo",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        inactive_item = Item(
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item inativo",
            estoque_minimo=Decimal("0"),
            ativo=False,
        )

        other_item = Item(
            empresa_id=company_b.id,
            unidade_id=unit_b.id,
            nome="Item de outra empresa",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add_all([active_item, inactive_item, other_item])
        db.commit()

        response = client.get(
            "/api/v1/itens",
            headers=headers_a,
        )

        assert response.status_code == 200

        names = {item["nome"] for item in response.json()}

        assert "Item ativo" in names
        assert "Item inativo" not in names
        assert "Item de outra empresa" not in names

        cleanup_context(db, *first_context[:3])
        cleanup_context(db, *second_context[:3])

    finally:
        db.close()


def test_operator_can_update_item_partially():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            role="OPERATOR",
        )

        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel A4",
            descricao="Descrição antiga",
            estoque_minimo=Decimal("2.0000"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"descricao": None},
            headers=headers,
        )

        assert response.status_code == 200

        body = response.json()

        assert body["nome"] == "Papel A4"
        assert body["descricao"] is None
        assert Decimal(str(body["estoque_minimo"])) == Decimal("2.0000")

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_update_item():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            role="VIEWER",
        )

        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel A4",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"nome": "Nome não permitido"},
            headers=headers,
        )

        assert response.status_code == 403

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_cannot_access_item_from_another_company():
    db = SessionLocal()
    first_context = None
    second_context = None

    try:
        first_context = create_context(db)
        second_context = create_context(db)

        _, company_a, _, _, headers_a = first_context
        _, company_b, _, unit_b, _ = second_context

        item = Item(
            empresa_id=company_b.id,
            unidade_id=unit_b.id,
            nome="Item privado",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.get(
            f"/api/v1/itens/{item.id}",
            headers=headers_a,
        )

        assert response.status_code == 404

        cleanup_context(db, *first_context[:3])
        cleanup_context(db, *second_context[:3])

    finally:
        db.close()


def test_create_item_rejects_fractional_minimum_for_integer_unit():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            permite_decimal=False,
        )

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": "Caixas",
                "estoque_minimo": "1.5000",
            },
            headers=headers,
        )

        assert response.status_code == 422

        cleanup_context(db, user, company, membership)

    finally:
        db.close()