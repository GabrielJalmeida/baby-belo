from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.auth.models import Usuario
from app.auth.service import AuthService
from app.shared.database import SessionLocal


client = TestClient(app)


def test_login_returns_access_token():
    db = SessionLocal()
    user = None

    email = f"login-{uuid4().hex}@example.com"

    try:
        user = AuthService.create_user(
            db=db,
            nome="Usuário Login",
            email=email,
            senha="senha-segura-123",
        )
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": email,
                "password": "senha-segura-123",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert "access_token" in body
        assert body["access_token"]
        assert body["token_type"] == "bearer"

    finally:
        if user is not None:
            db.rollback()

            user_to_delete = db.get(Usuario, user.id)

            if user_to_delete is not None:
                db.delete(user_to_delete)
                db.commit()

        db.close()