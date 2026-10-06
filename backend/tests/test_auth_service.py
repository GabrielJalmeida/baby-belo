from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth.models import Usuario
from app.auth.service import AuthService
from app.shared.config import settings
from app.shared.security import verify_password


TEST_DATABASE_URL = (
    settings.database_url.rsplit("/", 1)[0]
    + "/estoque_flex_auth_test"
)

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)


def test_create_user_normalizes_email_and_hashes_password():
    with Session(engine) as db:
        user = AuthService.create_user(
            db=db,
            nome=" Gabriel Almeida ",
            email=" Gabriel@EXEMPLO.com ",
            senha="SenhaTeste123!",
        )

        assert user.id is not None
        assert user.nome == "Gabriel Almeida"
        assert user.email == "gabriel@exemplo.com"
        assert user.senha_hash != "SenhaTeste123!"
        assert verify_password("SenhaTeste123!", user.senha_hash)
        assert user.ativo is True

        db.rollback()


def test_authenticate_user_with_correct_password():
    with Session(engine) as db:
        AuthService.create_user(
            db=db,
            nome="Usuário Login",
            email="login@example.com",
            senha="SenhaCorreta123!",
        )

        user = AuthService.authenticate_user(
            db=db,
            email=" LOGIN@EXAMPLE.COM ",
            senha="SenhaCorreta123!",
        )

        assert user is not None
        assert user.email == "login@example.com"

        db.rollback()


def test_authenticate_user_rejects_wrong_password():
    with Session(engine) as db:
        AuthService.create_user(
            db=db,
            nome="Usuário Senha",
            email="senha@example.com",
            senha="SenhaCorreta123!",
        )

        user = AuthService.authenticate_user(
            db=db,
            email="senha@example.com",
            senha="SenhaErrada123!",
        )

        assert user is None

        db.rollback()


def test_authenticate_user_rejects_inactive_user():
    with Session(engine) as db:
        user = AuthService.create_user(
            db=db,
            nome="Usuário Inativo",
            email="inativo@example.com",
            senha="SenhaCorreta123!",
        )

        user.ativo = False
        db.flush()

        authenticated_user = AuthService.authenticate_user(
            db=db,
            email="inativo@example.com",
            senha="SenhaCorreta123!",
        )

        assert authenticated_user is None

        db.rollback()


def test_get_user_by_id():
    with Session(engine) as db:
        created_user = AuthService.create_user(
            db=db,
            nome="Usuário ID",
            email="usuario.id@example.com",
            senha="SenhaTeste123!",
        )

        user = AuthService.get_user_by_id(
            db=db,
            user_id=created_user.id,
        )

        assert user is not None
        assert user.id == created_user.id

        db.rollback()


def test_get_user_by_email():
    with Session(engine) as db:
        created_user = AuthService.create_user(
            db=db,
            nome="Usuário Email",
            email="usuario.email@example.com",
            senha="SenhaTeste123!",
        )

        user = AuthService.get_user_by_email(
            db=db,
            email="usuario.email@example.com",
        )

        assert user is not None
        assert user.id == created_user.id

        db.rollback()