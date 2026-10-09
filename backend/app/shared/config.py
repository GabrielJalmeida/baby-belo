from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    cors_allowed_origins: list[str] = Field(default_factory=list)
    app_name: str = "Estoque Flex API"
    app_version: str = "0.1.0"

    database_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(
        cls,
        origins: list[str],
    ) -> list[str]:
        normalized = [
            origin.strip().rstrip("/")
            for origin in origins
            if origin.strip()
        ]

        if "*" in normalized:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS deve listar origens explícitas; "
                "'*' não é permitido."
            )

        return normalized


settings = Settings()