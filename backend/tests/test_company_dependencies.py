from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.company_service import CompanyAccessService
from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


app = FastAPI()


@app.get("/test-company")
def company_endpoint(
    membership: EmpresaUsuario = Depends(get_current_company_membership),
):
    return {
        "empresa_id": membership.empresa_id,
        "usuario_id": membership.usuario_id,
        "papel": membership.papel,
    }


client = TestClient(app)


def create_user_and_company(db):
    user = AuthService.create_user(
        db=db,
        nome="Usuário Contexto",
        email=f"context-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )

    company = Empresa(
        nome=f"Empresa Contexto {uuid4().hex}",
        ativo=True,
    )

    db.add(company)
    db.flush()

    membership = EmpresaUsuario(
        empresa_id=company.id,
        usuario_id=user.id,
        papel="OPERATOR",
        ativo=True,
    )

    db.add(membership)
    db.commit()

    return user, company, membership


def test_company_context_requires_header():
    response = client.get("/test-company")

    assert response.status_code == 401


def test_company_context_returns_membership():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["empresa_id"] == company.id
        assert body["usuario_id"] == user.id
        assert body["papel"] == "OPERATOR"

        db.delete(membership)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()


def test_company_context_rejects_missing_company_header():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 400

        db.delete(membership)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()


def test_company_context_rejects_company_without_access():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)

        other_company = Empresa(
            nome=f"Outra Empresa {uuid4().hex}",
            ativo=True,
        )

        db.add(other_company)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(other_company.id),
            },
        )

        assert response.status_code == 403

        db.delete(membership)
        db.delete(other_company)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()


def test_company_context_rejects_inactive_membership():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)

        membership.ativo = False
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 403

        db.delete(membership)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()