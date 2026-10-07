from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.service import AuthService
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_test_user(db: Session):
    email = f"auth-{uuid4().hex}@example.com"

    user = AuthService.create_user(
        db=db,
        nome="Usuário Teste",
        email=email,
        senha="senha-segura-123",
    )

    db.commit()

    return user


def delete_test_user(db: Session, user_id: int):
    user = AuthService.get_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is not None:
        db.delete(user)
        db.commit()


def test_me_requires_authentication():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user():
    db = SessionLocal()

    try:
        user = create_test_user(db)

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == user.id
        assert body["nome"] == "Usuário Teste"
        assert body["email"] == user.email
        assert body["ativo"] is True

        delete_test_user(db, user.id)

    finally:
        db.close()


def test_me_rejects_invalid_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401


def test_me_rejects_expired_token():
    db = SessionLocal()

    try:
        user = create_test_user(db)

        token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 401

        delete_test_user(db, user.id)

    finally:
        db.close()


def test_me_rejects_inactive_user():
    db = SessionLocal()

    try:
        user = create_test_user(db)

        user.ativo = False
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 401

        delete_test_user(db, user.id)

    finally:
        db.close()


def test_me_rejects_nonexistent_user():
    token = create_access_token(subject="999999999")

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401