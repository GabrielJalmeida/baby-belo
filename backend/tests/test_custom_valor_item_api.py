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
        email=f"valor-item-{uuid4().hex}@example.com",
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


def create_item_context(
    db,
    company,
    tipo_dado="TEXTO_CURTO",
    *,
    associar_categoria=True,
):
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

    categoria = Categoria(
        empresa_id=company.id,
        nome=f"Categoria {uuid4().hex}",
        ativo=True,
    )

    db.add_all([item, categoria])
    db.flush()

    if associar_categoria:
        db.add(
            ItemCategoria(
                item_id=item.id,
                categoria_id=categoria.id,
                empresa_id=company.id,
            )
        )
        db.flush()

    campo = Campo(
        empresa_id=company.id,
        categoria_id=categoria.id,
        nome=f"Campo {uuid4().hex}",
        tipo_dado=tipo_dado,
        obrigatorio=False,
        configuracao={},
        ordem_exibicao=0,
        ativo=True,
    )
    db.add(campo)
    db.flush()

    opcao = None

    if tipo_dado == "LISTA":
        opcao = CampoOpcao(
            campo_id=campo.id,
            valor=f"Opção {uuid4().hex}",
            ordem_exibicao=0,
            ativo=True,
        )
        db.add(opcao)
        db.flush()

    db.commit()
    db.refresh(item)
    db.refresh(campo)

    if opcao is not None:
        db.refresh(opcao)

    return item, categoria, campo, opcao


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


def create_value_request(user, company, item, campo, value):
    return client.post(
        f"/api/v1/custom/itens/{item.id}/valores",
        json={
            "campo_id": campo.id,
            **value,
        },
        headers=auth_headers(user, company),
    )


def test_create_value_requires_authentication():
    response = client.post(
        "/api/v1/custom/itens/1/valores",
        json={
            "campo_id": 1,
            "valor_texto": "Madeira",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_text_value():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        response = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["item_id"] == item.id
        assert body["campo_id"] == campo.id
        assert body["valor_texto"] == "Madeira"
        assert body["valor_inteiro"] is None

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_create_value():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        response = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_create_value_rejects_incompatible_type():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(
            db,
            company,
            tipo_dado="INTEIRO",
        )

        response = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Dez"},
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_create_value_requires_item_category():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(
            db,
            company,
            associar_categoria=False,
        )

        response = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )

        assert response.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_create_value_cannot_use_field_from_another_company():
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

        item_a, _, _, _ = create_item_context(db, company_a)
        _, _, campo_b, _ = create_item_context(db, company_b)

        response = create_value_request(
            user_a,
            company_a,
            item_a,
            campo_b,
            {"valor_texto": "Madeira"},
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_create_list_value_accepts_option_from_same_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, opcao = create_item_context(
            db,
            company,
            tipo_dado="LISTA",
        )

        response = create_value_request(
            user,
            company,
            item,
            campo,
            {"opcao_id": opcao.id},
        )

        assert response.status_code == 201
        assert response.json()["opcao_id"] == opcao.id

    finally:
        cleanup(db, records)
        db.close()


def test_create_duplicate_value_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        primeira = create_value_request(
            user, company, item, campo, {"valor_texto": "Madeira"}
        )
        segunda = create_value_request(
            user, company, item, campo, {"valor_texto": "Aço"}
        )

        assert primeira.status_code == 201
        assert segunda.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_list_values_returns_only_values_for_requested_item():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item_a, _, campo_a, _ = create_item_context(db, company)
        item_b, _, campo_b, _ = create_item_context(db, company)

        resposta_a = create_value_request(
            user, company, item_a, campo_a, {"valor_texto": "A"}
        )
        resposta_b = create_value_request(
            user, company, item_b, campo_b, {"valor_texto": "B"}
        )

        assert resposta_a.status_code == 201
        assert resposta_b.status_code == 201

        response = client.get(
            f"/api/v1/custom/itens/{item_a.id}/valores",
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["item_id"] == item_a.id
        assert body[0]["valor_texto"] == "A"

    finally:
        cleanup(db, records)
        db.close()


def test_get_value_does_not_expose_another_company_value():
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

        item_b, _, campo_b, _ = create_item_context(db, company_b)

        created = create_value_request(
            user_b,
            company_b,
            item_b,
            campo_b,
            {"valor_texto": "Privado"},
        )
        assert created.status_code == 201

        valor_id = created.json()["id"]

        response = client.get(
            f"/api/v1/custom/valores/{valor_id}",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_patch_value_updates_existing_value():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        created = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )
        assert created.status_code == 201

        valor_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/custom/valores/{valor_id}",
            json={"valor_texto": "Aço"},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200
        assert response.json()["valor_texto"] == "Aço"

    finally:
        cleanup(db, records)
        db.close()


def test_patch_value_rejects_incompatible_type():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        created = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )
        assert created.status_code == 201

        valor_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/custom/valores/{valor_id}",
            json={"valor_inteiro": 10},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_update_value():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        created = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )

        # A criação é proibida para VIEWER; criar diretamente no banco
        # permite testar a autorização específica do PATCH.
        db_value = ValorItem(
            item_id=item.id,
            campo_id=campo.id,
            valor_texto="Madeira",
        )
        db.add(db_value)
        db.commit()
        db.refresh(db_value)

        response = client.patch(
            f"/api/v1/custom/valores/{db_value.id}",
            json={"valor_texto": "Aço"},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_patch_empty_value_payload_is_rejected():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        item, _, campo, _ = create_item_context(db, company)

        created = create_value_request(
            user, company, item, campo, {"valor_texto": "Madeira"}
        )
        assert created.status_code == 201

        response = client.patch(
            f"/api/v1/custom/valores/{created.json()['id']}",
            json={},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_cannot_update_value_from_another_company():
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

        item_b, _, campo_b, _ = create_item_context(db, company_b)

        created = create_value_request(
            user_b,
            company_b,
            item_b,
            campo_b,
            {"valor_texto": "Privado"},
        )

        assert created.status_code == 201
        valor_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/custom/valores/{valor_id}",
            json={"valor_texto": "Alterado indevidamente"},
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

        verify_response = client.get(
            f"/api/v1/custom/valores/{valor_id}",
            headers=auth_headers(user_b, company_b),
        )

        assert verify_response.status_code == 200
        assert verify_response.json()["valor_texto"] == "Privado"

    finally:
        cleanup(db, records)
        db.close()

def test_cannot_change_field_type_when_values_exist():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item, categoria, campo, _ = create_item_context(
            db,
            company,
            tipo_dado="TEXTO_CURTO",
        )

        value_response = create_value_request(
            user,
            company,
            item,
            campo,
            {"valor_texto": "Madeira"},
        )

        assert value_response.status_code == 201, value_response.text

        response = client.patch(
            f"/api/v1/custom/campos/{campo.id}",
            json={"tipo_dado": "INTEIRO"},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 409, response.text

        db.refresh(campo)
        assert campo.tipo_dado == "TEXTO_CURTO"

    finally:
        cleanup(db, records)
        db.close()

def test_create_list_value_rejects_option_from_another_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        item, categoria, campo, _ = create_item_context(
            db,
            company,
            tipo_dado="LISTA",
        )

        outro_campo = Campo(
            empresa_id=company.id,
            categoria_id=categoria.id,
            nome=f"Outro campo {uuid4().hex}",
            tipo_dado="LISTA",
            obrigatorio=False,
            configuracao={},
            ordem_exibicao=1,
            ativo=True,
        )
        db.add(outro_campo)
        db.flush()

        outra_opcao = CampoOpcao(
            campo_id=outro_campo.id,
            valor=f"Opção {uuid4().hex}",
            ordem_exibicao=0,
            ativo=True,
        )
        db.add(outra_opcao)
        db.commit()

        response = create_value_request(
            user,
            company,
            item,
            campo,
            {"opcao_id": outra_opcao.id},
        )

        assert response.status_code == 422, response.text

        valor_id = db.scalar(
            select(ValorItem.id).where(
                ValorItem.item_id == item.id,
                ValorItem.campo_id == campo.id,
            )
        )
        assert valor_id is None

    finally:
        cleanup(db, records)
        db.close()
