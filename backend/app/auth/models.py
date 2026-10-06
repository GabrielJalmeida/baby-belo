from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "auth"}

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )

    senha_hash: Mapped[str] = mapped_column(
        String(255),
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

class EmpresaUsuario(Base):
    __tablename__ = "empresa_usuarios"
    __table_args__ = (
        CheckConstraint(
            "papel IN ('OWNER', 'OPERATOR', 'VIEWER')",
            name="ck_empresa_usuarios_papel",
        ),
        {"schema": "auth"},
    )

    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("core.empresas.id"),
        primary_key=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth.usuarios.id"),
        primary_key=True,
    )

    papel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'OPERATOR'"),
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