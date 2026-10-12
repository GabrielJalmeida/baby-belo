import pytest
from pydantic import ValidationError

from app.shared.config import Settings


DATABASE_URL = (
    "postgresql+psycopg://test:test@localhost:5432/test"
)


def criar_settings(**overrides) -> Settings:
    values = {
        "database_url": DATABASE_URL,
        "secret_key": "test-secret",
    }
    values.update(overrides)

    return Settings(
        _env_file=None,
        **values,
    )


@pytest.mark.parametrize(
    "secret_key",
    [
        "",
        " ",
        "\t\n",
    ],
)
def test_settings_rejects_blank_secret_key(secret_key):
    with pytest.raises(ValidationError):
        criar_settings(secret_key=secret_key)


@pytest.mark.parametrize(
    "minutes",
    [
        0,
        -1,
    ],
)
def test_settings_rejects_non_positive_token_expiration(minutes):
    with pytest.raises(ValidationError):
        criar_settings(access_token_expire_minutes=minutes)


def test_settings_accepts_valid_security_configuration():
    config = criar_settings(
        secret_key="test-secret",
        access_token_expire_minutes=30,
    )

    assert config.secret_key == "test-secret"
    assert config.access_token_expire_minutes == 30


def test_settings_keeps_default_token_expiration():
    config = criar_settings()

    assert config.access_token_expire_minutes == 30
