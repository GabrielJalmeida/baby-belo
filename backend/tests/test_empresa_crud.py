from uuid import uuid4
import pytest

from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_user_and_company(db, role="OWNER"):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"crud-{uuid4().hex}@example.com",
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
    db.delete(membership)
    db.delete(company)
    db.delete(user)
    db.commit()


def test_get_company_returns_own_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)
        token = create_access_token(subject=str(user.id))

        response = client.get(
            f"/api/v1/empresas/{company.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["id"] == company.id
        assert response.json()["nome"] == company.nome

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_get_company_rejects_different_context():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)

        other_company = Empresa(
            nome=f"Outra {uuid4().hex}",
            ativo=True,
        )

        db.add(other_company)
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.get(
            f"/api/v1/empresas/{company.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(other_company.id),
            },
        )

        assert response.status_code == 403

        db.delete(other_company)
        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_owner_can_update_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)
        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json={
                "nome": "Empresa Atualizada",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["nome"] == "Empresa Atualizada"

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_operator_cannot_update_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(
            db,
            role="OPERATOR",
        )

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
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


def test_viewer_cannot_update_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(
            db,
            role="VIEWER",
        )

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
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


def test_owner_can_deactivate_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)
        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json={
                "ativo": False,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["ativo"] is False

        db.refresh(company)

        assert company.ativo is False

        cleanup(db, user, company, membership)

    finally:
        db.close()

def test_owner_can_reactivate_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)
        token = create_access_token(subject=str(user.id))

        deactivate_response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json={
                "ativo": False,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["ativo"] is False

        reactivate_response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json={
                "ativo": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["ativo"] is True

        db.refresh(company)

        assert company.ativo is True

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_reactivate_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(
            db,
            role="VIEWER",
        )

        company.ativo = False
        db.commit()

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json={
                "ativo": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 403

        db.refresh(company)

        assert company.ativo is False

        cleanup(db, user, company, membership)

    finally:
        db.close()


def test_patch_empty_payload_does_not_change_company():
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)
        original_name = company.nome
        original_active = company.ativo

        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json={},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["nome"] == original_name
        assert response.json()["ativo"] is original_active

        db.refresh(company)

        assert company.nome == original_name
        assert company.ativo is original_active

        cleanup(db, user, company, membership)

    finally:
        db.close()


@pytest.mark.parametrize(
    "payload",
    [
        {"nome": None},
        {"ativo": None},
    ],
)
def test_patch_rejects_explicit_null_values(payload):
    db = SessionLocal()

    try:
        user, company, membership = create_user_and_company(db)
        token = create_access_token(subject=str(user.id))

        response = client.patch(
            f"/api/v1/empresas/{company.id}",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company.id),
            },
        )

        assert response.status_code == 422

        cleanup(db, user, company, membership)

    finally:
        db.close()