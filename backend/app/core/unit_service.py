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
        changes: dict[str, object],
    ) -> Unidade | None:
        unit = UnidadeService.get_unit(
            db=db,
            empresa_id=empresa_id,
            unit_id=unit_id,
        )

        if unit is None:
            return None

        if "nome" in changes:
            unit.nome = str(changes["nome"]).strip()

        if "simbolo" in changes:
            simbolo = changes["simbolo"]
            unit.simbolo = (
                str(simbolo).strip()
                if simbolo is not None
                else None
            )

        if "permite_decimal" in changes:
            unit.permite_decimal = bool(
                changes["permite_decimal"]
            )

        if "ativo" in changes:
            unit.ativo = bool(changes["ativo"])

        db.flush()

        return unit