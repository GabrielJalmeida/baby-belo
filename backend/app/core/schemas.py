from pydantic import BaseModel, Field


class EmpresaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=160)


class EmpresaResponse(BaseModel):
    id: int
    nome: str
    ativo: bool

    model_config = {"from_attributes": True}

class EmpresaUpdate(BaseModel):
    nome: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )
    ativo: bool | None = None