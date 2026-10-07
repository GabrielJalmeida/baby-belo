from uuid import uuid4

from app.auth.company_service import CompanyAccessService
from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.shared.database import SessionLocal


def create_test_user_and_company(db):
    user = AuthService.create_user(
        db=db,
        nome="Usuário Empresa",
        email=f"company-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )

    company = Empresa(
        nome=f"Empresa {uuid4().hex}",
        ativo=True,
    )

    db.add(company)
    db.flush()

    return user, company


def test_user_can_access_active_company():
    db = SessionLocal()

    try:
        user, company = create_test_user_and_company(db)

        membership = EmpresaUsuario(
            empresa_id=company.id,
            usuario_id=user.id,
            papel="OPERATOR",
            ativo=True,
        )

        db.add(membership)
        db.commit()

        result = CompanyAccessService.get_active_membership(
            db=db,
            user_id=user.id,
            company_id=company.id,
        )

        assert result is not None
        assert result.empresa_id == company.id
        assert result.usuario_id == user.id
        assert result.papel == "OPERATOR"

        db.delete(membership)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()


def test_user_cannot_access_company_without_membership():
    db = SessionLocal()

    try:
        user, company = create_test_user_and_company(db)

        db.commit()

        result = CompanyAccessService.get_active_membership(
            db=db,
            user_id=user.id,
            company_id=company.id,
        )

        assert result is None

        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()


def test_user_cannot_access_inactive_membership():
    db = SessionLocal()

    try:
        user, company = create_test_user_and_company(db)

        membership = EmpresaUsuario(
            empresa_id=company.id,
            usuario_id=user.id,
            papel="OPERATOR",
            ativo=False,
        )

        db.add(membership)
        db.commit()

        result = CompanyAccessService.get_active_membership(
            db=db,
            user_id=user.id,
            company_id=company.id,
        )

        assert result is None

        db.delete(membership)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()


def test_user_cannot_access_inactive_company():
    db = SessionLocal()

    try:
        user, company = create_test_user_and_company(db)

        company.ativo = False

        membership = EmpresaUsuario(
            empresa_id=company.id,
            usuario_id=user.id,
            papel="OPERATOR",
            ativo=True,
        )

        db.add(membership)
        db.commit()

        result = CompanyAccessService.get_active_membership(
            db=db,
            user_id=user.id,
            company_id=company.id,
        )

        assert result is None

        db.delete(membership)
        db.delete(company)
        db.delete(user)
        db.commit()

    finally:
        db.close()