from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]

JWT_HMAC_MIN_KEY_BYTES = {
    "HS256": 32,
    "HS384": 48,
    "HS512": 64,
}


class Settings(BaseSettings):
    cors_allowed_origins: list[str] = Field(default_factory=list)
    app_name: str = "Estoque Flex API"
    app_version: str = "0.1.0"

    database_url: str
    test_auth_database_url: str | None = None

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

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

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, secret_key: str) -> str:
        if not secret_key.strip():
            raise ValueError("SECRET_KEY não pode ficar vazia.")

        return secret_key

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, algorithm: str) -> str:
        if algorithm not in JWT_HMAC_MIN_KEY_BYTES:
            raise ValueError(
                "ALGORITHM deve ser HS256, HS384 ou HS512."
            )

        return algorithm

    @model_validator(mode="after")
    def validate_secret_key_length(self) -> "Settings":
        minimum_bytes = JWT_HMAC_MIN_KEY_BYTES[self.algorithm]
        actual_bytes = len(self.secret_key.encode("utf-8"))

        if actual_bytes < minimum_bytes:
            raise ValueError(
                f"SECRET_KEY deve possuir ao menos {minimum_bytes} "
                f"bytes UTF-8 para o algoritmo {self.algorithm}."
            )

        return self


settings = Settings()