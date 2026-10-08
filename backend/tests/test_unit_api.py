from uuid import uuid4

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