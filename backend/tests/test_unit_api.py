from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.core.unit_models import Unidade
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_user_company_membership(db, role="OWNER"):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"unit-{uuid4().hex}@example.com",
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


def cleanup(db, user, company, membership):
    db.query(Unidade).filter(
        Unidade.empresa_id == company.id
    ).delete()

    db.delete(membership)
    db.delete(company)
    db.delete(user)
    db.commit()


def test_create_unit_requires_authentication():
    response = client.post(
        "/api/v1/unidades",
        json={
            "nome": "Unidade",
            "simbolo": "UN",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_unit():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(
            db,
            "OWNER",
        )

        token = create_access_token(subject=str(user.id))

        response = client.post(
            "/api/v1/unidades",
            json={
                "nome": "Unidade",
                "simbolo": "UN",
                "permite_decimal": False,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 201

        body = response.json()

        assert body["empresa_id"] == company.id
        assert body["nome"] == "Unidade"
        assert body["simbolo"] == "UN"
        assert body["permite_decimal"] is False
        assert body["ativo"] is True

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_create_unit():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(
            db,
            "VIEWER",
        )

        token = create_access_token(subject=str(user.id))

        response = client.post(
            "/api/v1/unidades",
            json={
                "nome": "Unidade",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 403

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_list_units_returns_only_active_units_of_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(db)
        other_user, other_company, other_membership = (
            create_user_company_membership(db)
        )

        unit_a = Unidade(
            empresa_id=company.id,
            nome="Unidade A",
            simbolo="UN",
            permite_decimal=False,
            ativo=True,
        )

        unit_inactive = Unidade(
            empresa_id=company.id,
            nome="Unidade Inativa",
            simbolo="UI",
            ativo=False,
        )

        unit_other = Unidade(
            empresa_id=other_company.id,
            nome="Unidade Outro",
            simbolo="OUT",
        )

        db.add_all([
            unit_a,
            unit_inactive,
            unit_other,
        ])

        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/api/v1/unidades",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200

        body = response.json()

        names = {
            unit["nome"]
            for unit in body
        }

        assert "Unidade A" in names
        assert "Unidade Inativa" not in names
        assert "Unidade Outro" not in names

        cleanup(db, user, company, membership)

        db.query(Unidade).filter(
            Unidade.empresa_id == other_company.id
        ).delete()

        db.delete(other_membership)
        db.delete(other_company)
        db.delete(other_user)
        db.commit()

    finally:
        db.close()


def test_operator_can_update_unit():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(
            db,
            "OPERATOR",
        )

        unit = Unidade(
            empresa_id=company.id,
            nome="Caixa",
            simbolo="CX",
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/unidades/{unit.id}",
            json={
                "nome": "Caixa Atualizada",
                "simbolo": "CXA",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["nome"] == "Caixa Atualizada"
        assert body["simbolo"] == "CXA"

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_update_unit():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(
            db,
            "VIEWER",
        )

        unit = Unidade(
            empresa_id=company.id,
            nome="Caixa",
            simbolo="CX",
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/unidades/{unit.id}",
            json={
                "nome": "Não permitido",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 403

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_cannot_access_unit_from_another_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(db)
        _, other_company, other_membership = (
            create_user_company_membership(db)
        )

        unit = Unidade(
            empresa_id=other_company.id,
            nome="Unidade Privada",
            simbolo="UP",
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            f"/api/v1/unidades/{unit.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 404

        cleanup(db, user, company, membership)

        db.delete(unit)
        db.flush()

        db.delete(other_membership)
        db.delete(other_company)
        db.commit()

    finally:
        db.close()


def test_patch_unit_with_empty_payload_keeps_values_unchanged():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(db)

        unit = Unidade(
            empresa_id=company.id,
            nome="Caixa",
            simbolo="CX",
            permite_decimal=False,
            ativo=True,
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/unidades/{unit.id}",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200

        body = response.json()
        assert body["nome"] == "Caixa"
        assert body["simbolo"] == "CX"
        assert body["permite_decimal"] is False
        assert body["ativo"] is True

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_patch_unit_can_clear_nullable_symbol():
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(db)

        unit = Unidade(
            empresa_id=company.id,
            nome="Caixa",
            simbolo="CX",
            permite_decimal=False,
            ativo=True,
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/unidades/{unit.id}",
            json={"simbolo": None},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["simbolo"] is None

        cleanup(db, user, company, membership)

    finally:
        db.close()


@pytest.mark.parametrize(
    "field",
    ["nome", "permite_decimal", "ativo"],
)
def test_patch_unit_rejects_null_for_non_nullable_fields(field):
    db = SessionLocal()

    try:
        user, company, membership = create_user_company_membership(db)

        unit = Unidade(
            empresa_id=company.id,
            nome="Caixa",
            simbolo="CX",
            permite_decimal=False,
            ativo=True,
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/unidades/{unit.id}",
            json={field: None},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 422

        db.refresh(unit)
        assert unit.nome == "Caixa"
        assert unit.simbolo == "CX"
        assert unit.permite_decimal is False
        assert unit.ativo is True

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_list_units_supports_limit_and_offset():
    db = SessionLocal()
    user = company = membership = None

    try:
        user, company, membership = create_user_company_membership(db)

        units = [
            Unidade(
                empresa_id=company.id,
                nome=f"Unidade {number}",
                simbolo="UN",
                permite_decimal=False,
                ativo=True,
            )
            for number in range(5)
        ]

        db.add_all(units)
        db.commit()

        token = create_access_token(subject=str(user.id))
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Company-ID": str(company.id),
        }

        full_response = client.get(
            "/api/v1/unidades",
            headers=headers,
        )

        assert full_response.status_code == 200
        full_ids = [unit["id"] for unit in full_response.json()]
        assert len(full_ids) == 5

        page_response = client.get(
            "/api/v1/unidades?limit=2&offset=1",
            headers=headers,
        )

        assert page_response.status_code == 200
        page_ids = [unit["id"] for unit in page_response.json()]
        assert page_ids == full_ids[1:3]

    finally:
        if user is not None and company is not None and membership is not None:
            cleanup(db, user, company, membership)
        db.close()


def test_list_units_rejects_invalid_pagination_parameters():
    db = SessionLocal()
    user = company = membership = None

    try:
        user, company, membership = create_user_company_membership(db)

        token = create_access_token(subject=str(user.id))
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Company-ID": str(company.id),
        }

        invalid_queries = [
            "limit=0",
            "limit=101",
            "offset=-1",
        ]

        for query in invalid_queries:
            response = client.get(
                f"/api/v1/unidades?{query}",
                headers=headers,
            )

            assert response.status_code == 422, query

    finally:
        if user is not None and company is not None and membership is not None:
            cleanup(db, user, company, membership)
        db.close()


def test_cannot_update_unit_from_another_company():
    db = SessionLocal()
    user = company = membership = None
    other_user = other_company = other_membership = None
    unit = None

    try:
        user, company, membership = create_user_company_membership(db)
        other_user, other_company, other_membership = (
            create_user_company_membership(db)
        )

        unit = Unidade(
            empresa_id=other_company.id,
            nome="Unidade Privada",
            simbolo="UP",
            permite_decimal=False,
            ativo=True,
        )

        db.add(unit)
        db.commit()

        token = create_access_token(subject=str(user.id))
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Company-ID": str(company.id),
        }

        response = client.patch(
            f"/api/v1/unidades/{unit.id}",
            json={"nome": "Alterada indevidamente"},
            headers=headers,
        )

        assert response.status_code == 404

        db.refresh(unit)
        assert unit.nome == "Unidade Privada"

    finally:
        if (
            user is not None
            and company is not None
            and membership is not None
        ):
            cleanup(db, user, company, membership)

        if (
            other_user is not None
            and other_company is not None
            and other_membership is not None
        ):
            cleanup(
                db,
                other_user,
                other_company,
                other_membership,
            )

        db.close()
