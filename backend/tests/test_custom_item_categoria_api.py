from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import or_, select

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade
from app.custom.models import (
    Campo,
    CampoOpcao,
    Categoria,
    ItemCategoria,
    ValorItem,
)
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_user_company_membership(db, role="OWNER"):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"item-categoria-{uuid4().hex}@example.com",
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
    db.add(membership)
    db.commit()

    return user, company, membership


def create_category(db, company, nome=None):
    categoria = Categoria(
        empresa_id=company.id,
        nome=nome or f"Categoria {uuid4().hex}",
        ativo=True,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def create_item(db, company):
    unit = Unidade(
        empresa_id=company.id,
        nome=f"Unidade {uuid4().hex}",
        simbolo="UN",
        permite_decimal=True,
        ativo=True,
    )
    db.add(unit)
    db.flush()

    item = Item(
        empresa_id=company.id,
        unidade_id=unit.id,
        nome=f"Item {uuid4().hex}",
        descricao=None,
        estoque_minimo=Decimal("0"),
        ativo=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def auth_headers(user, company):
    token = create_access_token(subject=str(user.id))
    return {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }


def cleanup(db, records):
    for user, company, membership in records:
        empresa_id = company.id

        item_ids = select(Item.id).where(
            Item.empresa_id == empresa_id,
        )
        campo_ids = select(Campo.id).where(
            Campo.empresa_id == empresa_id,
        )

        db.query(ValorItem).filter(
            or_(
                ValorItem.item_id.in_(item_ids),
                ValorItem.campo_id.in_(campo_ids),
            )
        ).delete(synchronize_session=False)

        db.query(CampoOpcao).filter(
            CampoOpcao.campo_id.in_(campo_ids),
        ).delete(synchronize_session=False)

        db.query(ItemCategoria).filter(
            ItemCategoria.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(Campo).filter(
            Campo.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(Categoria).filter(
            Categoria.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(Item).filter(
            Item.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(Unidade).filter(
            Unidade.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.delete(membership)
        db.delete(company)
        db.delete(user)

    db.commit()


def assign_category_request(user, company, item, categoria):
    return client.put(
        f"/api/v1/custom/itens/{item.id}/categoria",
        json={"categoria_id": categoria.id},
        headers=auth_headers(user, company),
    )


def test_assign_category_requires_authentication():
    response = client.put(
        "/api/v1/custom/itens/1/categoria",
        json={"categoria_id": 1},
    )

    assert response.status_code == 401


def test_owner_can_assign_category_to_item():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item = create_item(db, company)
        categoria = create_category(db, company)

        response = assign_category_request(
            user, company, item, categoria
        )

        assert response.status_code == 200
        body = response.json()
        assert body["item_id"] == item.id
        assert body["categoria_id"] == categoria.id
        assert body["empresa_id"] == company.id

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_assign_category():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))

        item = create_item(db, company)
        categoria = create_category(db, company)

        response = assign_category_request(
            user, company, item, categoria
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_assign_category_rejects_item_from_another_company():
    db = SessionLocal()
    records = []

    try:
        user_a, company_a, membership_a = (
            create_user_company_membership(db)
        )
        records.append((user_a, company_a, membership_a))

        user_b, company_b, membership_b = (
            create_user_company_membership(db)
        )
        records.append((user_b, company_b, membership_b))

        item_b = create_item(db, company_b)
        categoria_a = create_category(db, company_a)

        response = assign_category_request(
            user_a, company_a, item_b, categoria_a
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_assign_category_rejects_category_from_another_company():
    db = SessionLocal()
    records = []

    try:
        user_a, company_a, membership_a = (
            create_user_company_membership(db)
        )
        records.append((user_a, company_a, membership_a))

        user_b, company_b, membership_b = (
            create_user_company_membership(db)
        )
        records.append((user_b, company_b, membership_b))

        item_a = create_item(db, company_a)
        categoria_b = create_category(db, company_b)

        response = assign_category_request(
            user_a, company_a, item_a, categoria_b
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_repeating_same_assignment_is_idempotent():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item = create_item(db, company)
        categoria = create_category(db, company)

        primeira = assign_category_request(
            user, company, item, categoria
        )
        segunda = assign_category_request(
            user, company, item, categoria
        )

        assert primeira.status_code == 200
        assert segunda.status_code == 200
        assert (
            primeira.json()["categoria_id"]
            == segunda.json()["categoria_id"]
        )

        quantidade = db.query(ItemCategoria).filter(
            ItemCategoria.item_id == item.id,
        ).count()

        assert quantidade == 1

    finally:
        cleanup(db, records)
        db.close()


def test_category_can_change_before_custom_values_exist():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item = create_item(db, company)
        categoria_a = create_category(db, company)
        categoria_b = create_category(db, company)

        primeira = assign_category_request(
            user, company, item, categoria_a
        )
        assert primeira.status_code == 200

        segunda = assign_category_request(
            user, company, item, categoria_b
        )

        assert segunda.status_code == 200
        assert segunda.json()["categoria_id"] == categoria_b.id

    finally:
        cleanup(db, records)
        db.close()


def test_category_cannot_change_after_custom_values_exist():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item = create_item(db, company)
        categoria_a = create_category(db, company)
        categoria_b = create_category(db, company)

        primeira = assign_category_request(
            user, company, item, categoria_a
        )
        assert primeira.status_code == 200

        campo = Campo(
            empresa_id=company.id,
            categoria_id=categoria_a.id,
            nome=f"Material {uuid4().hex}",
            tipo_dado="TEXTO_CURTO",
            obrigatorio=False,
            configuracao={},
            ordem_exibicao=0,
            ativo=True,
        )
        db.add(campo)
        db.flush()

        valor = ValorItem(
            item_id=item.id,
            campo_id=campo.id,
            valor_texto="Madeira",
        )
        db.add(valor)
        db.commit()

        response = assign_category_request(
            user, company, item, categoria_b
        )

        assert response.status_code == 409

        associacao = db.query(ItemCategoria).filter(
            ItemCategoria.item_id == item.id,
        ).one()

        assert associacao.categoria_id == categoria_a.id

    finally:
        cleanup(db, records)
        db.close()


def test_get_item_category_returns_association():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item = create_item(db, company)
        categoria = create_category(db, company)

        created = assign_category_request(
            user, company, item, categoria
        )
        assert created.status_code == 200

        response = client.get(
            f"/api/v1/custom/itens/{item.id}/categoria",
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200
        assert response.json()["categoria_id"] == categoria.id

    finally:
        cleanup(db, records)
        db.close()


def test_get_item_category_returns_not_found_when_unassigned():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item = create_item(db, company)

        response = client.get(
            f"/api/v1/custom/itens/{item.id}/categoria",
            headers=auth_headers(user, company),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()