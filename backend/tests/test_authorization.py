from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.shared.authorization import require_role
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


app = FastAPI()


@app.get("/test-read")
def read_endpoint(
    membership: EmpresaUsuario = Depends(
        require_role("OWNER", "OPERATOR", "VIEWER")
    ),
):
    return {
        "empresa_id": membership.empresa_id,
        "papel": membership.papel,
    }


@app.post("/test-write")
def write_endpoint(
    membership: EmpresaUsuario = Depends(
        require_role("OWNER", "OPERATOR")
    ),
):
    return {
        "empresa_id": membership.empresa_id,
        "papel": membership.papel,
    }


client = TestClient(app)


def create_user(db, role: str):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {role}",
        email=f"{role.lower()}-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )

    company = Empresa(
        nome=f"Empresa {role} {uuid4().hex}",
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


def delete_data(db, user, company, membership):
    db.delete(membership)
    db.delete(company)
    db.delete(user)
    db.commit()


def test_role_dependency_requires_authentication():
    response = client.post("/test-write")

    assert response.status_code == 401


def test_owner_can_write():
    db = SessionLocal()

    try:
        user, company, membership = create_user(
            db,
            "OWNER",
        )

        token = create_access_token(
            subject=str(user.id),
        )

        response = client.post(
            "/test-write",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["papel"] == "OWNER"

        delete_data(db, user, company, membership)

    finally:
        db.close()


def test_operator_can_write():
    db = SessionLocal()

    try:
        user, company, membership = create_user(
            db,
            "OPERATOR",
        )

        token = create_access_token(
            subject=str(user.id),
        )

        response = client.post(
            "/test-write",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["papel"] == "OPERATOR"

        delete_data(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_write():
    db = SessionLocal()

    try:
        user, company, membership = create_user(
            db,
            "VIEWER",
        )

        token = create_access_token(
            subject=str(user.id),
        )

        response = client.post(
            "/test-write",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 403

        delete_data(db, user, company, membership)

    finally:
        db.close()


@pytest.mark.parametrize(
    "role",
    [
        "OWNER",
        "OPERATOR",
        "VIEWER",
    ],
)
def test_all_roles_can_read(role):
    db = SessionLocal()

    try:
        user, company, membership = create_user(
            db,
            role,
        )

        token = create_access_token(
            subject=str(user.id),
        )

        response = client.get(
            "/test-read",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["papel"] == role

        delete_data(db, user, company, membership)

    finally:
        db.close()


def test_require_role_rejects_invalid_role_configuration():
    with pytest.raises(ValueError):
        require_role("ADMIN")