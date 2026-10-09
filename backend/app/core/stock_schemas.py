
from decimal import Decimal

from pydantic import BaseModel


class SaldoEstoqueResponse(BaseModel):
    item_id: int
    empresa_id: int
    item_nome: str
    unidade_id: int
    unidade_nome: str
    unidade_simbolo: str | None
    estoque_minimo: Decimal
    ativo: bool
    saldo_atual: Decimal


class EstoqueBaixoResponse(BaseModel):
    item_id: int
    empresa_id: int
    item_nome: str
    unidade_id: int
    unidade_nome: str
    unidade_simbolo: str | None
    estoque_minimo: Decimal
    saldo_atual: Decimal