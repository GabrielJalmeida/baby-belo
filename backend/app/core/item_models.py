
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class Item(Base):
    __tablename__ = "itens"

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "unidade_id"],
            ["core.unidades.empresa_id", "core.unidades.id"],
            name="fk_itens_unidade_empresa",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "BTRIM(nome) <> ''",
            name="ck_itens_nome_nao_vazio",
        ),
        CheckConstraint(
            "estoque_minimo >= 0",
            name="ck_itens_estoque_minimo_nao_negativo",
        ),
        UniqueConstraint(
            "empresa_id",
            "nome",
            name="uq_itens_empresa_nome",
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_itens_empresa_id",
        ),
        Index(
            "idx_itens_empresa_ativo",
            "empresa_id",
            "ativo",
        ),
        {"schema": "core"},
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
            name="fk_itens_empresa",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    unidade_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    estoque_minimo: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
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