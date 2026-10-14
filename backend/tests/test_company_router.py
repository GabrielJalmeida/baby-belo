from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_company_context(db):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"company-router-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )

    company = Empresa(
        nome=f"Empresa teste {uuid4().hex}",
        ativo=True,
    )
    db.add(company)
    db.flush()

    membership = EmpresaUsuario(
        empresa_id=company.id,
        usuario_id=user.id,
        papel="OWNER",
        ativo=True,
    )
    db.add(membership)
    db.commit()

    token = create_access_token(subject=str(user.id))

    return user, company, membership, {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }


def cleanup_company_context(db, user, company, membership):
    db.delete(membership)
    db.delete(company)
    db.delete(user)
    db.commit()


def test_company_routes_reject_non_positive_path_ids():
    db = SessionLocal()
    context = None

    try:
        context = create_company_context(db)
        user, company, membership, headers = context
        original_name = company.nome

        for company_id in (0, -1):
            get_response = client.get(
                f"/api/v1/empresas/{company_id}",
                headers=headers,
            )

            assert get_response.status_code == 422, (
                f"GET empresa ID {company_id}: "
                f"recebeu {get_response.status_code}: "
                f"{get_response.text}"
            )

            patch_response = client.patch(
                f"/api/v1/empresas/{company_id}",
                json={"nome": "Nome alterado indevidamente"},
                headers=headers,
            )

            assert patch_response.status_code == 422, (
                f"PATCH empresa ID {company_id}: "
                f"recebeu {patch_response.status_code}: "
                f"{patch_response.text}"
            )

        db.refresh(company)
        assert company.nome == original_name

    finally:
        if context is not None:
            cleanup_company_context(db, *context[:3])
        db.close()

def test_company_membership_route_returns_active_role():
    db = SessionLocal()
    context = None

    try:
        context = create_company_context(db)
        user, company, membership, headers = context
        membership.papel = "VIEWER"
        db.commit()

        response = client.get(
            f"/api/v1/empresas/{company.id}/membership",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {
            "empresa_id": company.id,
            "usuario_id": user.id,
            "papel": "VIEWER",
        }
    finally:
        if context is not None:
            cleanup_company_context(db, *context[:3])
        db.close()
