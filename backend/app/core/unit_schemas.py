from pydantic import BaseModel, Field


class UnidadeCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    simbolo: str | None = Field(default=None, max_length=20)
    permite_decimal: bool = True


class UnidadeUpdate(BaseModel):
    nome: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
    )
    simbolo: str | None = Field(
        default=None,
        max_length=20,
    )
    permite_decimal: bool | None = None
    ativo: bool | None = None


class UnidadeResponse(BaseModel):
    id: int
    empresa_id: int
    nome: str
    simbolo: str | None
    permite_decimal: bool
    ativo: bool

    model_config = {"from_attributes": True}