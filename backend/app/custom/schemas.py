from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


TipoDado = Literal[
    "TEXTO_CURTO",
    "TEXTO_LONGO",
    "INTEIRO",
    "DECIMAL",
    "DINHEIRO",
    "BOOLEANO",
    "DATA",
    "LISTA",
]


# ============================================================
# Bases comuns
# ============================================================

class CustomInput(BaseModel):
    """Configuração comum para dados recebidos pela API."""

    model_config = ConfigDict(extra="forbid")


class CustomRead(BaseModel):
    """Permite construir respostas a partir de objetos ORM."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# ============================================================
# Categorias
# ============================================================

class CategoriaCreate(CustomInput):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip()
        return valor

    @field_validator("descricao", mode="before")
    @classmethod
    def normalizar_descricao(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor


class CategoriaUpdate(CustomInput):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    descricao: str | None = None
    ativo: bool | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip()
        return valor

    @field_validator("descricao", mode="before")
    @classmethod
    def normalizar_descricao(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @model_validator(mode="after")
    def validar_atualizacao(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")

        if "nome" in self.model_fields_set and self.nome is None:
            raise ValueError("O nome não pode ser nulo.")

        return self


class CategoriaRead(CustomRead):
    id: int
    empresa_id: int
    nome: str
    descricao: str | None
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


# ============================================================
# Campos personalizados
# ============================================================

class CampoCreate(CustomInput):
    categoria_id: int = Field(gt=0)
    nome: str = Field(min_length=1, max_length=120)
    tipo_dado: TipoDado
    obrigatorio: bool = False
    configuracao: dict[str, Any] = Field(default_factory=dict)
    ordem_exibicao: int = 0
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip()
        return valor


class CampoUpdate(CustomInput):
    categoria_id: int | None = None
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    tipo_dado: TipoDado | None = None
    obrigatorio: bool | None = None
    configuracao: dict[str, Any] | None = None
    ordem_exibicao: int | None = None
    ativo: bool | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip()
        return valor

    @model_validator(mode="after")
    def validar_atualizacao(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")

        for nome in self.model_fields_set:
            if getattr(self, nome) is None:
                raise ValueError(
                    f"O campo '{nome}' não pode ser nulo."
                )

        if self.categoria_id is not None and self.categoria_id <= 0:
            raise ValueError("A categoria precisa ter um ID positivo.")

        return self


class CampoRead(CustomRead):
    id: int
    empresa_id: int
    categoria_id: int
    nome: str
    tipo_dado: TipoDado
    obrigatorio: bool
    configuracao: dict[str, Any]
    ordem_exibicao: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


# ============================================================
# Opções de campos do tipo LISTA
# ============================================================

class CampoOpcaoCreate(CustomInput):
    campo_id: int = Field(gt=0)
    valor: str = Field(min_length=1, max_length=150)
    ordem_exibicao: int = 0
    ativo: bool = True

    @field_validator("valor", mode="before")
    @classmethod
    def normalizar_valor(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip()
        return valor


class CampoOpcaoUpdate(CustomInput):
    valor: str | None = Field(default=None, min_length=1, max_length=150)
    ordem_exibicao: int | None = None
    ativo: bool | None = None

    @field_validator("valor", mode="before")
    @classmethod
    def normalizar_valor(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip()
        return valor

    @model_validator(mode="after")
    def validar_atualizacao(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")

        for nome in self.model_fields_set:
            if getattr(self, nome) is None:
                raise ValueError(
                    f"O campo '{nome}' não pode ser nulo."
                )

        return self


class CampoOpcaoRead(CustomRead):
    id: int
    campo_id: int
    valor: str
    ordem_exibicao: int
    ativo: bool


# ============================================================
# Associação entre item e categoria
# ============================================================

class ItemCategoriaCreate(CustomInput):
    categoria_id: int = Field(gt=0)


class ItemCategoriaRead(CustomRead):
    item_id: int
    categoria_id: int
    empresa_id: int


# ============================================================
# Valores dos campos personalizados
# ============================================================

class ValorItemDados(CustomInput):
    valor_texto: str | None = None
    valor_inteiro: int | None = Field(
        default=None,
        ge=-(2**63),
        le=(2**63) - 1,
    )
    valor_decimal: Decimal | None = Field(
        default=None,
        max_digits=18,
        decimal_places=4,
    )
    valor_monetario: Decimal | None = Field(
        default=None,
        max_digits=18,
        decimal_places=2,
    )
    valor_booleano: bool | None = None
    valor_data: date | None = None
    opcao_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validar_exatamente_um_valor(self):
        nomes = (
            "valor_texto",
            "valor_inteiro",
            "valor_decimal",
            "valor_monetario",
            "valor_booleano",
            "valor_data",
            "opcao_id",
        )

        preenchidos = [
            nome
            for nome in nomes
            if getattr(self, nome) is not None
        ]

        if len(preenchidos) != 1:
            raise ValueError(
                "Informe exatamente um tipo de valor por vez."
            )

        return self


class ValorItemCreate(ValorItemDados):
    campo_id: int = Field(gt=0)


class ValorItemRead(CustomRead):
    id: int
    item_id: int
    campo_id: int
    opcao_id: int | None
    valor_texto: str | None
    valor_inteiro: int | None
    valor_decimal: Decimal | None
    valor_monetario: Decimal | None
    valor_booleano: bool | None
    valor_data: date | None

class ValorItemUpdate(CustomInput):
    valor_texto: str | None = None
    valor_inteiro: int | None = Field(
        default=None,
        ge=-(2**63),
        le=(2**63) - 1,
    )
    valor_decimal: Decimal | None = Field(
        default=None,
        max_digits=18,
        decimal_places=4,
    )
    valor_monetario: Decimal | None = Field(
        default=None,
        max_digits=18,
        decimal_places=2,
    )
    valor_booleano: bool | None = None
    valor_data: date | None = None
    opcao_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validar_atualizacao(self):
        campos_valor = {
            "valor_texto",
            "valor_inteiro",
            "valor_decimal",
            "valor_monetario",
            "valor_booleano",
            "valor_data",
            "opcao_id",
        }

        informados = campos_valor.intersection(self.model_fields_set)

        if len(informados) != 1:
            raise ValueError(
                "Informe exatamente um tipo de valor para atualizar."
            )

        nome_campo = next(iter(informados))

        if getattr(self, nome_campo) is None:
            raise ValueError(
                "O valor informado para atualização não pode ser nulo."
            )

        return self