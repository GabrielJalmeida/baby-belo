
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    PrimaryKeyConstraint,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    Numeric,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class Inventario(Base):
    __tablename__ = "inventarios"

    __table_args__ = (
        CheckConstraint(
            "status IN ('ABERTO', 'CONCLUIDO', 'CANCELADO')",
            name="ck_inventarios_status",
        ),
        CheckConstraint(
            """
            (
                status = 'ABERTO'
                AND concluido_em IS NULL
                AND cancelado_em IS NULL
            )
            OR
            (
                status = 'CONCLUIDO'
                AND concluido_em IS NOT NULL
                AND cancelado_em IS NULL
            )
            OR
            (
                status = 'CANCELADO'
                AND cancelado_em IS NOT NULL
                AND concluido_em IS NULL
            )
            """,
            name="ck_inventarios_status_datas",
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_inventarios_empresa_id",
        ),
        Index(
            "idx_inventarios_empresa_status",
            "empresa_id",
            "status",
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
            name="fk_inventarios_empresa",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ABERTO'"),
    )

    observacao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    iniciado_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    concluido_em: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    cancelado_em: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )


class InventarioItem(Base):
    __tablename__ = "inventario_itens"

    __table_args__ = (
        PrimaryKeyConstraint(
            "inventario_id",
            "item_id",
            name="pk_inventario_itens",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "inventario_id"],
            ["core.inventarios.empresa_id", "core.inventarios.id"],
            name="fk_inventario_itens_inventario_empresa",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "item_id"],
            ["core.itens.empresa_id", "core.itens.id"],
            name="fk_inventario_itens_item_empresa",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "quantidade_contada IS NULL OR quantidade_contada >= 0",
            name="ck_inventario_itens_quantidade_contada",
        ),
        CheckConstraint(
            """
            (
                quantidade_contada IS NULL
                AND contado_em IS NULL
            )
            OR
            (
                quantidade_contada IS NOT NULL
                AND contado_em IS NOT NULL
            )
            """,
            name="ck_inventario_itens_contagem_data",
        ),
        Index(
            "idx_inventario_itens_item",
            "item_id",
        ),
        {"schema": "core"},
    )

    inventario_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    item_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    saldo_sistema: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )

    quantidade_contada: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    diferenca: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        Computed(
            "quantidade_contada - saldo_sistema",
            persisted=True,
        ),
        nullable=True,
    )

    contado_em: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )