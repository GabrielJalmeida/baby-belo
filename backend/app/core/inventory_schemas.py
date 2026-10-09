
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


StatusInventario = Literal[
    "ABERTO",
    "CONCLUIDO",
    "CANCELADO",
]


class InventarioCreate(BaseModel):
    observacao: str | None = None

    @field_validator("observacao", mode="before")
    @classmethod
    def normalize_observation(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            return value or None

        return value


class InventarioContagemUpdate(BaseModel):
    quantidade_contada: Decimal = Field(
        ge=0,
        max_digits=18,
        decimal_places=4,
    )


class InventarioItemResponse(BaseModel):
    inventario_id: int
    empresa_id: int
    item_id: int
    saldo_sistema: Decimal
    quantidade_contada: Decimal | None
    diferenca: Decimal | None
    contado_em: datetime | None

    model_config = {"from_attributes": True}


class InventarioResponse(BaseModel):
    id: int
    empresa_id: int
    status: StatusInventario
    observacao: str | None
    iniciado_em: datetime
    concluido_em: datetime | None
    cancelado_em: datetime | None

    model_config = {"from_attributes": True}


class InventarioDetalheResponse(InventarioResponse):
    itens: list[InventarioItemResponse]