from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_user(db, prefix: str):
    return AuthService.create_user(
        db=db,
        nome=f"Usuário {prefix}",
        email=f"{prefix}-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )


def delete_user(db, user):
    db.query(EmpresaUsuario).filter(
        EmpresaUsuario.usuario_id == user.id
    ).delete()

    db.delete(user)
    db.commit()


def test_create_company_requires_authentication():
    response = client.post(
        "/api/v1/empresas",
        json={"nome": "Empresa Teste"},
    )

    assert response.status_code == 401


def test_create_company_creates_owner_membership():
    db = SessionLocal()

    try:
        user = create_user(db, "create-company")
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.post(
            "/api/v1/empresas",
            json={"nome": "Empresa Teste"},
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 201

        body = response.json()

        assert body["nome"] == "Empresa Teste"
        assert body["ativo"] is True
        assert "id" in body

        membership = db.query(EmpresaUsuario).filter(
            EmpresaUsuario.usuario_id == user.id,
            EmpresaUsuario.empresa_id == body["id"],
        ).one()

        assert membership.papel == "OWNER"
        assert membership.ativo is True

        company = db.get(Empresa, body["id"])
        db.delete(membership)
        db.delete(company)
        db.commit()

        delete_user(db, user)

    finally:
        db.close()


def test_list_companies_returns_only_user_companies():
    db = SessionLocal()

    try:
        user = create_user(db, "list-companies")
        other_user = create_user(db, "other-user")

        company_a = Empresa(nome=f"Empresa A {uuid4().hex}")
        company_b = Empresa(nome=f"Empresa B {uuid4().hex}")
        company_other = Empresa(nome=f"Empresa Outro {uuid4().hex}")

        db.add_all([
            company_a,
            company_b,
            company_other,
        ])
        db.flush()

        membership_a = EmpresaUsuario(
            empresa_id=company_a.id,
            usuario_id=user.id,
            papel="OWNER",
        )

        membership_b = EmpresaUsuario(
            empresa_id=company_b.id,
            usuario_id=user.id,
            papel="OPERATOR",
        )

        membership_other = EmpresaUsuario(
            empresa_id=company_other.id,
            usuario_id=other_user.id,
            papel="OWNER",
        )

        db.add_all([
            membership_a,
            membership_b,
            membership_other,
        ])

        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/api/v1/empresas",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        body = response.json()

        company_ids = {
            company["id"]
            for company in body
        }

        assert company_a.id in company_ids
        assert company_b.id in company_ids
        assert company_other.id not in company_ids

        db.delete(membership_a)
        db.delete(membership_b)
        db.delete(membership_other)
        db.delete(company_a)
        db.delete(company_b)
        db.delete(company_other)
        db.delete(user)
        db.delete(other_user)
        db.commit()

    finally:
        db.close()


def test_list_companies_rejects_unauthenticated_request():
    response = client.get("/api/v1/empresas")

    assert response.status_code == 401