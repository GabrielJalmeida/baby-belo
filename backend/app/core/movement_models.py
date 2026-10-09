
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "item_id"],
            ["core.itens.empresa_id", "core.itens.id"],
            name="fk_movimentacoes_item_empresa",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "tipo IN ('ENTRADA', 'SAIDA', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA')",
            name="ck_movimentacoes_tipo",
        ),
        CheckConstraint(
            "quantidade > 0",
            name="ck_movimentacoes_quantidade_positiva",
        ),
        CheckConstraint(
            "motivo IS NULL OR BTRIM(motivo) <> ''",
            name="ck_movimentacoes_motivo_nao_vazio",
        ),
        Index(
            "idx_movimentacoes_item_ocorrida_em",
            "item_id",
            "ocorrida_em",
        ),
        Index(
            "idx_movimentacoes_empresa_ocorrida_em",
            "empresa_id",
            "ocorrida_em",
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
            name="fk_movimentacoes_empresa",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    item_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    quantidade: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )

    motivo: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    observacao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ocorrida_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )