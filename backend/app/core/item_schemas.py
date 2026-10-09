
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ItemCreate(BaseModel):
    unidade_id: int = Field(gt=0)
    nome: str = Field(min_length=1, max_length=160)
    descricao: str | None = None
    estoque_minimo: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=18,
        decimal_places=4,
    )

    @field_validator("nome", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if not isinstance(value, str):
            return value

        value = value.strip()

        if not value:
            raise ValueError("O nome do item não pode ficar vazio.")

        return value

    @field_validator("descricao")
    @classmethod
    def normalize_description(cls, value):
        if value is None:
            return None

        value = value.strip()
        return value or None


class ItemUpdate(BaseModel):
    unidade_id: int | None = Field(default=None, gt=0)
    nome: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )
    descricao: str | None = None
    estoque_minimo: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=4,
    )
    ativo: bool | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if value is None:
            raise ValueError("O nome do item não pode ser nulo.")

        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError("O nome do item não pode ficar vazio.")

        return value

    @field_validator(
        "unidade_id",
        "estoque_minimo",
        "ativo",
        mode="before",
    )
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("O campo não pode ser nulo.")

        return value

    @field_validator("descricao")
    @classmethod
    def normalize_description(cls, value):
        if value is None:
            return None

        value = value.strip()
        return value or None


class ItemResponse(BaseModel):
    id: int
    empresa_id: int
    unidade_id: int
    nome: str
    descricao: str | None
    estoque_minimo: Decimal
    ativo: bool

    model_config = {"from_attributes": True}