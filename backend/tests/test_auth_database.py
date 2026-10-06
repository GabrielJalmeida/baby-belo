import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.shared.config import settings


TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/estoque_flex_auth_test"

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)


def test_auth_tables_exist():
    inspector = inspect(engine)

    tables = set(inspector.get_table_names(schema="auth"))

    assert "usuarios" in tables
    assert "empresa_usuarios" in tables


def test_auth_foreign_keys_are_correct():
    inspector = inspect(engine)

    foreign_keys = inspector.get_foreign_keys(
        "empresa_usuarios",
        schema="auth",
    )

    relationships = {
        (fk["constrained_columns"][0], fk["referred_schema"], fk["referred_table"], fk["referred_columns"][0])
        for fk in foreign_keys
    }

    assert (
        "empresa_id",
        "core",
        "empresas",
        "id",
    ) in relationships

    assert (
        "usuario_id",
        "auth",
        "usuarios",
        "id",
    ) in relationships


def test_valid_user_company_relationship():
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            company_id = connection.execute(
                text(
                    """
                    INSERT INTO core.empresas (nome)
                    VALUES ('Empresa AUTH Teste')
                    RETURNING id
                    """
                )
            ).scalar_one()

            user_id = connection.execute(
                text(
                    """
                    INSERT INTO auth.usuarios (
                        nome,
                        email,
                        senha_hash
                    )
                    VALUES (
                        'Usuário AUTH Teste',
                        'auth.teste@example.com',
                        'hash-de-teste'
                    )
                    RETURNING id
                    """
                )
            ).scalar_one()

            connection.execute(
                text(
                    """
                    INSERT INTO auth.empresa_usuarios (
                        empresa_id,
                        usuario_id,
                        papel
                    )
                    VALUES (
                        :empresa_id,
                        :usuario_id,
                        'OWNER'
                    )
                    """
                ),
                {
                    "empresa_id": company_id,
                    "usuario_id": user_id,
                },
            )

            transaction.commit()

        except Exception:
            transaction.rollback()
            raise


def test_invalid_role_is_rejected():
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            company_id = connection.execute(
                text(
                    """
                    INSERT INTO core.empresas (nome)
                    VALUES ('Empresa Papel Inválido')
                    RETURNING id
                    """
                )
            ).scalar_one()

            user_id = connection.execute(
                text(
                    """
                    INSERT INTO auth.usuarios (
                        nome,
                        email,
                        senha_hash
                    )
                    VALUES (
                        'Usuário Papel Inválido',
                        'papel.invalido@example.com',
                        'hash-de-teste'
                    )
                    RETURNING id
                    """
                )
            ).scalar_one()

            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        text(
                            """
                            INSERT INTO auth.empresa_usuarios (
                                empresa_id,
                                usuario_id,
                                papel
                            )
                            VALUES (
                                :empresa_id,
                                :usuario_id,
                                'ADMIN'
                            )
                            """
                        ),
                        {
                            "empresa_id": company_id,
                            "usuario_id": user_id,
                        },
                    )

        finally:
            transaction.rollback()


def test_nonexistent_company_is_rejected():
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            user_id = connection.execute(
                text(
                    """
                    INSERT INTO auth.usuarios (
                        nome,
                        email,
                        senha_hash
                    )
                    VALUES (
                        'Usuário FK Teste',
                        'fk.teste@example.com',
                        'hash-de-teste'
                    )
                    RETURNING id
                    """
                )
            ).scalar_one()

            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        text(
                            """
                            INSERT INTO auth.empresa_usuarios (
                                empresa_id,
                                usuario_id,
                                papel
                            )
                            VALUES (
                                999999999999,
                                :usuario_id,
                                'OPERATOR'
                            )
                            """
                        ),
                        {
                            "usuario_id": user_id,
                        },
                    )

        finally:
            transaction.rollback()


def test_email_is_case_insensitive_unique():
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            connection.execute(
                text(
                    """
                    INSERT INTO auth.usuarios (
                        nome,
                        email,
                        senha_hash
                    )
                    VALUES (
                        'Usuário Email Original',
                        'Usuario@Exemplo.com',
                        'hash-de-teste'
                    )
                    """
                )
            )

            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        text(
                            """
                            INSERT INTO auth.usuarios (
                                nome,
                                email,
                                senha_hash
                            )
                            VALUES (
                                'Usuário Email Duplicado',
                                'usuario@exemplo.com',
                                'hash-de-teste'
                            )
                            """
                        )
                    )

        finally:
            transaction.rollback()