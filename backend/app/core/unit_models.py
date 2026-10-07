from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class Unidade(Base):
    __tablename__ = "unidades"

    __table_args__ = (
        CheckConstraint(
            "BTRIM(nome) <> ''",
            name="ck_unidades_nome_nao_vazio",
        ),
        CheckConstraint(
            "simbolo IS NULL OR BTRIM(simbolo) <> ''",
            name="ck_unidades_simbolo_nao_vazio",
        ),
        UniqueConstraint(
            "empresa_id",
            "nome",
            name="uq_unidades_empresa_nome",
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_unidades_empresa_id",
        ),
        Index(
            "idx_unidades_empresa_ativo",
            "empresa_id",
            "ativo",
        ),
        {"schema": "core"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.empresas.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    simbolo: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    permite_decimal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
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