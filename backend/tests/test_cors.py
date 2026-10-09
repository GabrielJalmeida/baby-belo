import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.shared.config import Settings, settings


client = TestClient(app)


def test_cors_preflight_allows_configured_origin():
    assert settings.cors_allowed_origins, (
        "Configure CORS_ALLOWED_ORIGINS no arquivo backend/.env."
    )

    origin = settings.cors_allowed_origins[0]

    response = client.options(
        "/api/v1/movimentacoes",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "authorization,content-type,x-company-id"
            ),
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin

    allowed_headers = response.headers[
        "access-control-allow-headers"
    ].lower()

    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers
    assert "x-company-id" in allowed_headers


def test_cors_preflight_rejects_unconfigured_origin():
    origin = "https://cors-denied.invalid"

    assert origin not in settings.cors_allowed_origins

    response = client.options(
        "/api/v1/movimentacoes",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "authorization,content-type,x-company-id"
            ),
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_settings_reject_wildcard():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://test:test@localhost/test",
            secret_key="test-secret",
            cors_allowed_origins=["*"],
        )