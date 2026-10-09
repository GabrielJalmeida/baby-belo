from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
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
        email=f"opcao-{uuid4().hex}@example.com",
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


def create_category_and_field(
    db,
    company,
    tipo_dado="LISTA",
    campo_ativo=True,
):
    categoria = Categoria(
        empresa_id=company.id,
        nome=f"Categoria {uuid4().hex}",
        ativo=True,
    )

    db.add(categoria)
    db.flush()

    campo = Campo(
        empresa_id=company.id,
        categoria_id=categoria.id,
        nome=f"Campo {uuid4().hex}",
        tipo_dado=tipo_dado,
        obrigatorio=False,
        configuracao={},
        ordem_exibicao=0,
        ativo=campo_ativo,
    )

    db.add(campo)
    db.commit()
    db.refresh(campo)

    return categoria, campo


def auth_headers(user, company):
    token = create_access_token(subject=str(user.id))

    return {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }


def cleanup(db, records):
    for user, company, membership in records:
        empresa_id = company.id

        campo_ids = select(Campo.id).where(
            Campo.empresa_id == empresa_id,
        )

        db.query(ValorItem).filter(
            ValorItem.campo_id.in_(campo_ids),
        ).delete(synchronize_session=False)

        db.query(CampoOpcao).filter(
            CampoOpcao.campo_id.in_(campo_ids),
        ).delete(synchronize_session=False)

        db.query(Campo).filter(
            Campo.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(ItemCategoria).filter(
            ItemCategoria.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(Categoria).filter(
            Categoria.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.delete(membership)
        db.delete(company)
        db.delete(user)

    db.commit()


def test_create_option_requires_authentication():
    response = client.post(
        "/api/v1/custom/opcoes",
        json={
            "campo_id": 1,
            "valor": "Madeira",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_option():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        response = client.post(
            "/api/v1/custom/opcoes",
            json={
                "campo_id": campo.id,
                "valor": "  Madeira  ",
                "ordem_exibicao": 1,
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 201

        body = response.json()
        assert body["campo_id"] == campo.id
        assert body["valor"] == "Madeira"
        assert body["ordem_exibicao"] == 1
        assert body["ativo"] is True

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_create_option():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        response = client.post(
            "/api/v1/custom/opcoes",
            json={
                "campo_id": campo.id,
                "valor": "Madeira",
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_create_option_rejects_non_list_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(
            db,
            company,
            tipo_dado="TEXTO_CURTO",
        )

        response = client.post(
            "/api/v1/custom/opcoes",
            json={
                "campo_id": campo.id,
                "valor": "Madeira",
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_create_option_rejects_field_from_another_company():
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

        _, campo_b = create_category_and_field(db, company_b)

        response = client.post(
            "/api/v1/custom/opcoes",
            json={
                "campo_id": campo_b.id,
                "valor": "Madeira",
            },
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_list_options_returns_only_active_options():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        db.add_all(
            [
                CampoOpcao(
                    campo_id=campo.id,
                    valor="Madeira",
                    ordem_exibicao=1,
                    ativo=True,
                ),
                CampoOpcao(
                    campo_id=campo.id,
                    valor="Metal",
                    ordem_exibicao=2,
                    ativo=False,
                ),
            ]
        )
        db.commit()

        response = client.get(
            f"/api/v1/custom/campos/{campo.id}/opcoes",
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200

        valores = {item["valor"] for item in response.json()}

        assert "Madeira" in valores
        assert "Metal" not in valores

    finally:
        cleanup(db, records)
        db.close()


def test_list_options_rejects_non_list_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(
            db,
            company,
            tipo_dado="TEXTO_CURTO",
        )

        response = client.get(
            f"/api/v1/custom/campos/{campo.id}/opcoes",
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_list_options_cannot_access_field_from_another_company():
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

        _, campo_b = create_category_and_field(db, company_b)

        response = client.get(
            f"/api/v1/custom/campos/{campo_b.id}/opcoes",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_get_option_does_not_expose_another_company_option():
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

        _, campo_b = create_category_and_field(db, company_b)

        opcao = CampoOpcao(
            campo_id=campo_b.id,
            valor="Madeira",
        )
        db.add(opcao)
        db.commit()
        db.refresh(opcao)

        response = client.get(
            f"/api/v1/custom/opcoes/{opcao.id}",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_create_duplicate_option_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)
        headers = auth_headers(user, company)
        payload = {
            "campo_id": campo.id,
            "valor": "Madeira",
        }

        primeira = client.post(
            "/api/v1/custom/opcoes",
            json=payload,
            headers=headers,
        )
        segunda = client.post(
            "/api/v1/custom/opcoes",
            json=payload,
            headers=headers,
        )

        assert primeira.status_code == 201
        assert segunda.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_patch_option_updates_value_and_order():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        opcao = CampoOpcao(
            campo_id=campo.id,
            valor="Madeira",
            ordem_exibicao=0,
            ativo=True,
        )
        db.add(opcao)
        db.commit()
        db.refresh(opcao)

        response = client.patch(
            f"/api/v1/custom/opcoes/{opcao.id}",
            json={
                "valor": "Aço",
                "ordem_exibicao": 3,
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200

        body = response.json()
        assert body["valor"] == "Aço"
        assert body["ordem_exibicao"] == 3

    finally:
        cleanup(db, records)
        db.close()


def test_patch_option_can_reactivate_inactive_option():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        opcao = CampoOpcao(
            campo_id=campo.id,
            valor="Madeira",
            ativo=False,
        )
        db.add(opcao)
        db.commit()
        db.refresh(opcao)

        response = client.patch(
            f"/api/v1/custom/opcoes/{opcao.id}",
            json={"ativo": True},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200
        assert response.json()["ativo"] is True

    finally:
        cleanup(db, records)
        db.close()


def test_patch_duplicate_option_value_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        primeira = CampoOpcao(
            campo_id=campo.id,
            valor="Madeira",
        )
        segunda = CampoOpcao(
            campo_id=campo.id,
            valor="Metal",
        )
        db.add_all([primeira, segunda])
        db.commit()
        db.refresh(primeira)

        response = client.patch(
            f"/api/v1/custom/opcoes/{primeira.id}",
            json={"valor": "Metal"},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_update_option():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        opcao = CampoOpcao(
            campo_id=campo.id,
            valor="Madeira",
            ativo=True,
        )
        db.add(opcao)
        db.commit()
        db.refresh(opcao)

        response = client.patch(
            f"/api/v1/custom/opcoes/{opcao.id}",
            json={"ativo": False},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_patch_empty_option_payload_is_rejected():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        _, campo = create_category_and_field(db, company)

        opcao = CampoOpcao(
            campo_id=campo.id,
            valor="Madeira",
        )
        db.add(opcao)
        db.commit()
        db.refresh(opcao)

        response = client.patch(
            f"/api/v1/custom/opcoes/{opcao.id}",
            json={},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()