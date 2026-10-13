import pytest
from pydantic import ValidationError

from app.shared.config import Settings


DATABASE_URL = (
    "postgresql+psycopg://test:test@localhost:5432/test"
)
VALID_SECRET_KEY = "s" * 64


def criar_settings(**overrides) -> Settings:
    values = {
        "database_url": DATABASE_URL,
        "secret_key": VALID_SECRET_KEY,
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


@pytest.mark.parametrize(
    ("algorithm", "key_length"),
    [
        ("HS256", 31),
        ("HS384", 47),
        ("HS512", 63),
    ],
)
def test_settings_rejects_short_secret_for_algorithm(
    algorithm,
    key_length,
):
    with pytest.raises(
        ValidationError,
        match="ao menos",
    ):
        criar_settings(
            algorithm=algorithm,
            secret_key="s" * key_length,
        )


@pytest.mark.parametrize(
    ("algorithm", "key_length"),
    [
        ("HS256", 32),
        ("HS384", 48),
        ("HS512", 64),
    ],
)
def test_settings_accepts_minimum_secret_for_algorithm(
    algorithm,
    key_length,
):
    config = criar_settings(
        algorithm=algorithm,
        secret_key="s" * key_length,
        access_token_expire_minutes=30,
    )

    assert config.algorithm == algorithm
    assert len(config.secret_key.encode("utf-8")) == key_length
    assert config.access_token_expire_minutes == 30


@pytest.mark.parametrize(
    "algorithm",
    [
        "none",
        "RS256",
        "ES256",
        "hs256",
        "",
    ],
)
def test_settings_rejects_unsupported_algorithm(algorithm):
    with pytest.raises(ValidationError):
        criar_settings(algorithm=algorithm)


def test_settings_keeps_default_token_expiration():
    config = criar_settings()

    assert config.access_token_expire_minutes == 30
    assert config.algorithm == "HS256"


def test_settings_accepts_valid_security_configuration():
    config = criar_settings(
        secret_key="s" * 32,
        algorithm="HS256",
        access_token_expire_minutes=30,
    )

    assert config.secret_key == "s" * 32
    assert config.algorithm == "HS256"
    assert config.access_token_expire_minutes == 30