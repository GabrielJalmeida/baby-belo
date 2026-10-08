from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.unit_models import Unidade


class UnidadeService:
    @staticmethod
    def create_unit(
        db: Session,
        empresa_id: int,
        nome: str,
        simbolo: str | None,
        permite_decimal: bool,
    ) -> Unidade:
        unit = Unidade(
            empresa_id=empresa_id,
            nome=nome.strip(),
            simbolo=simbolo.strip() if simbolo is not None else None,
            permite_decimal=permite_decimal,
            ativo=True,
        )

        db.add(unit)
        db.flush()

        return unit

    @staticmethod
    def list_units(
        db: Session,
        empresa_id: int,
    ) -> list[Unidade]:
        statement = (
            select(Unidade)
            .where(
                Unidade.empresa_id == empresa_id,
                Unidade.ativo.is_(True),
            )
            .order_by(Unidade.id)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_unit(
        db: Session,
        empresa_id: int,
        unit_id: int,
    ) -> Unidade | None:
        statement = select(Unidade).where(
            Unidade.id == unit_id,
            Unidade.empresa_id == empresa_id,
        )

        return db.scalar(statement)

    @staticmethod
    def update_unit(
        db: Session,
        empresa_id: int,
        unit_id: int,
        nome: str | None = None,
        simbolo: str | None = None,
        permite_decimal: bool | None = None,
        ativo: bool | None = None,
    ) -> Unidade | None:
        unit = UnidadeService.get_unit(
            db=db,
            empresa_id=empresa_id,
            unit_id=unit_id,
        )

        if unit is None:
            return None

        if nome is not None:
            unit.nome = nome.strip()

        if simbolo is not None:
            unit.simbolo = simbolo.strip()

        if permite_decimal is not None:
            unit.permite_decimal = permite_decimal

        if ativo is not None:
            unit.ativo = ativo

        db.flush()

        return unit