from datetime import timedelta

import pytest

from app.shared.config import settings
from app.shared.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    password = "SenhaTeste123!"

    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("SenhaErrada123!", hashed_password)


def test_create_and_decode_access_token():
    token = create_access_token(subject="123")

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject="123",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError, match="Token inválido"):
        decode_access_token(token)


def test_token_signature_cannot_be_changed():
    token = create_access_token(subject="123")

    parts = token.split(".")
    assert len(parts) == 3

    tampered_token = f"{parts[0]}.{parts[1]}.assinatura-alterada"

    with pytest.raises(ValueError, match="Token inválido"):
        decode_access_token(tampered_token)