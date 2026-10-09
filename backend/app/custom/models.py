
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    Date,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

# Registra os modelos CORE na metadata antes de resolver as FKs.
from app.core.item_models import Item as _Item  # noqa: F401
from app.core.models import Empresa as _Empresa  # noqa: F401
from app.shared.base import Base


class Categoria(Base):
    __tablename__ = "categorias"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "nome",
            name="uq_categorias_empresa_nome",
        ),
        Index(
            "idx_categorias_empresa_ativo",
            "empresa_id",
            "ativo",
        ),
        {"schema": "custom"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.empresas.id",
            name="fk_categorias_empresa",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    criado_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class ItemCategoria(Base):
    __tablename__ = "item_categorias"

    __table_args__ = (
        ForeignKeyConstraint(
            ["item_id"],
            ["core.itens.id"],
            name="fk_item_categorias_item",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["categoria_id"],
            ["custom.categorias.id"],
            name="fk_item_categorias_categoria",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["empresa_id"],
            ["core.empresas.id"],
            name="fk_item_categorias_empresa",
            ondelete="RESTRICT",
        ),
        Index(
            "idx_item_categorias_categoria",
            "categoria_id",
        ),
        Index(
            "idx_item_categorias_empresa",
            "empresa_id",
        ),
        {"schema": "custom"},
    )

    item_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    categoria_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.empresas.id",
            name="fk_item_categorias_empresa",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )


class Campo(Base):
    __tablename__ = "campos"

    __table_args__ = (
        CheckConstraint(
            """
            tipo_dado IN (
                'TEXTO_CURTO',
                'TEXTO_LONGO',
                'INTEIRO',
                'DECIMAL',
                'DINHEIRO',
                'BOOLEANO',
                'DATA',
                'LISTA'
            )
            """,
            name="ck_campos_tipo_dado",
        ),
        UniqueConstraint(
            "categoria_id",
            "nome",
            name="uq_campos_categoria_nome",
        ),
        Index(
            "idx_campos_categoria_ativo",
            "categoria_id",
            "ativo",
        ),
        {"schema": "custom"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.empresas.id",
            name="fk_campos_empresa",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    categoria_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "custom.categorias.id",
            name="fk_campos_categoria",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    tipo_dado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    obrigatorio: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    configuracao: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    ordem_exibicao: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    criado_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class CampoOpcao(Base):
    __tablename__ = "campo_opcoes"

    __table_args__ = (
        UniqueConstraint(
            "campo_id",
            "valor",
            name="uq_campo_opcoes_campo_valor",
        ),
        {"schema": "custom"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    campo_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "custom.campos.id",
            name="fk_campo_opcoes_campo",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    valor: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    ordem_exibicao: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )


class ValorItem(Base):
    __tablename__ = "valores_item"

    __table_args__ = (
        ForeignKeyConstraint(
            ["item_id"],
            ["core.itens.id"],
            name="fk_valores_item_item",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["campo_id"],
            ["custom.campos.id"],
            name="fk_valores_item_campo",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["opcao_id"],
            ["custom.campo_opcoes.id"],
            name="fk_valores_item_opcao",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "item_id",
            "campo_id",
            name="uq_valores_item_item_campo",
        ),
        CheckConstraint(
            """
            num_nonnulls(
                valor_texto,
                valor_inteiro,
                valor_decimal,
                valor_monetario,
                valor_booleano,
                valor_data,
                opcao_id
            ) = 1
            """,
            name="ck_valores_item_um_valor",
        ),
        Index(
            "idx_valores_item_item",
            "item_id",
        ),
        Index(
            "idx_valores_item_campo",
            "campo_id",
        ),
        {"schema": "custom"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    item_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    campo_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    valor_data: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    valor_texto: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    valor_inteiro: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    valor_decimal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    valor_monetario: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    valor_booleano: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    valor_data: Mapped[datetime | None] = mapped_column(
        Date,
        nullable=True,
    )

    opcao_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )