from pydantic import BaseModel, Field, field_validator


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

    @field_validator("nome", "ativo", mode="before")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("O campo não pode ser nulo.")
        return value