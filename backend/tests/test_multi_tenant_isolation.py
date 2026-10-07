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


def create_user(db, prefix: str):
    return AuthService.create_user(
        db=db,
        nome=f"Usuário {prefix}",
        email=f"{prefix}-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )


def create_company(db, prefix: str):
    company = Empresa(
        nome=f"Empresa {prefix} {uuid4().hex}",
        ativo=True,
    )

    db.add(company)
    db.flush()

    return company


def create_membership(db, user_id: int, company_id: int, role: str = "OPERATOR"):
    membership = EmpresaUsuario(
        empresa_id=company_id,
        usuario_id=user_id,
        papel=role,
        ativo=True,
    )

    db.add(membership)
    db.flush()

    return membership


def test_user_cannot_access_another_users_company():
    db = SessionLocal()

    try:
        user_a = create_user(db, "usuario-a")
        user_b = create_user(db, "usuario-b")

        company_a = create_company(db, "A")
        company_b = create_company(db, "B")

        membership_a = create_membership(
            db,
            user_a.id,
            company_a.id,
        )

        membership_b = create_membership(
            db,
            user_b.id,
            company_b.id,
        )

        db.commit()

        token_a = create_access_token(subject=str(user_a.id))
        token_b = create_access_token(subject=str(user_b.id))

        response_a_own = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-Company-ID": str(company_a.id),
            },
        )

        response_a_other = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-Company-ID": str(company_b.id),
            },
        )

        response_b_own = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token_b}",
                "X-Company-ID": str(company_b.id),
            },
        )

        response_b_other = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token_b}",
                "X-Company-ID": str(company_a.id),
            },
        )

        assert response_a_own.status_code == 200
        assert response_a_own.json()["empresa_id"] == company_a.id

        assert response_a_other.status_code == 403

        assert response_b_own.status_code == 200
        assert response_b_own.json()["empresa_id"] == company_b.id

        assert response_b_other.status_code == 403

        db.delete(membership_a)
        db.delete(membership_b)
        db.delete(company_a)
        db.delete(company_b)
        db.delete(user_a)
        db.delete(user_b)
        db.commit()

    finally:
        db.close()


def test_same_user_can_switch_between_authorized_companies():
    db = SessionLocal()

    try:
        user = create_user(db, "usuario-multi")

        company_a = create_company(db, "Multi-A")
        company_b = create_company(db, "Multi-B")

        membership_a = create_membership(
            db,
            user.id,
            company_a.id,
            role="OWNER",
        )

        membership_b = create_membership(
            db,
            user.id,
            company_b.id,
            role="VIEWER",
        )

        db.commit()

        token = create_access_token(subject=str(user.id))

        response_a = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company_a.id),
            },
        )

        response_b = client.get(
            "/test-company",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company_b.id),
            },
        )

        assert response_a.status_code == 200
        assert response_a.json()["empresa_id"] == company_a.id
        assert response_a.json()["papel"] == "OWNER"

        assert response_b.status_code == 200
        assert response_b.json()["empresa_id"] == company_b.id
        assert response_b.json()["papel"] == "VIEWER"

        db.delete(membership_a)
        db.delete(membership_b)
        db.delete(company_a)
        db.delete(company_b)
        db.delete(user)
        db.commit()

    finally:
        db.close()