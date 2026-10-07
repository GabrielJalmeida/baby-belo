from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class Empresa(Base):
    __tablename__ = "empresas"

    __table_args__ = (
        CheckConstraint(
            "BTRIM(nome) <> ''",
            name="ck_empresas_nome_nao_vazio",
        ),
        {"schema": "core"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    nome: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
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