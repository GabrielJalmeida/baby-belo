from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Usuario
from app.shared.security import get_password_hash, verify_password


class AuthService:
    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str,
    ) -> Usuario | None:
        statement = select(Usuario).where(
            Usuario.email == email
        )

        return db.scalar(statement)

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ) -> Usuario | None:
        statement = select(Usuario).where(
            Usuario.id == user_id
        )

        return db.scalar(statement)

    @staticmethod
    def create_user(
        db: Session,
        nome: str,
        email: str,
        senha: str,
    ) -> Usuario:
        normalized_email = email.strip().lower()

        user = Usuario(
            nome=nome.strip(),
            email=normalized_email,
            senha_hash=get_password_hash(senha),
            ativo=True,
        )

        db.add(user)
        db.flush()

        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        senha: str,
    ) -> Usuario | None:
        normalized_email = email.strip().lower()

        user = AuthService.get_user_by_email(
            db,
            normalized_email,
        )

        if user is None:
            return None

        if not user.ativo:
            return None

        if not verify_password(
            senha,
            user.senha_hash,
        ):
            return None

        return user