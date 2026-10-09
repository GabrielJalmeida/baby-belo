
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


TipoMovimentacao = Literal[
    "ENTRADA",
    "SAIDA",
    "AJUSTE_ENTRADA",
    "AJUSTE_SAIDA",
]


class MovimentacaoCreate(BaseModel):
    item_id: int = Field(gt=0)
    tipo: TipoMovimentacao
    quantidade: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=4,
    )
    motivo: str | None = Field(default=None, max_length=255)
    observacao: str | None = None
    ocorrida_em: datetime | None = None

    @field_validator("motivo", mode="before")
    @classmethod
    def normalize_reason(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError(
                    "O motivo não pode ser uma string vazia."
                )

        return value

    @field_validator("observacao", mode="before")
    @classmethod
    def normalize_observation(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            return value or None

        return value

    @field_validator("ocorrida_em")
    @classmethod
    def require_timezone(cls, value):
        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "A data da movimentação deve incluir fuso horário."
            )

        return value


class MovimentacaoResponse(BaseModel):
    id: int
    empresa_id: int
    item_id: int
    tipo: TipoMovimentacao
    quantidade: Decimal
    motivo: str | None
    observacao: str | None
    ocorrida_em: datetime

    model_config = {"from_attributes": True}


class SaldoResponse(BaseModel):
    empresa_id: int
    item_id: int
    saldo_atual: Decimal