from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.inventory_service import (
    InventarioService,
    ItemBloqueadoPorInventarioAbertoError,
)
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade


class UnidadeComQuantidadesFracionariasError(ValueError):
    """A unidade não pode ser inteira enquanto houver valores fracionários."""

class UnidadeBloqueadaPorInventarioAbertoError(ValueError):
    """A precisão da unidade não pode mudar durante um inventário aberto."""

class UnidadeService:
    @staticmethod
    def _ensure_no_fractional_quantities(
        db: Session,
        empresa_id: int,
        unit_id: int,
    ) -> None:
        fractional_minimum_item_id = db.scalar(
            select(Item.id)
            .where(
                Item.empresa_id == empresa_id,
                Item.unidade_id == unit_id,
                Item.estoque_minimo != func.trunc(Item.estoque_minimo),
            )
            .limit(1)
        )

        fractional_balance_exists = db.scalar(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.vw_saldos_estoque
                    WHERE empresa_id = :empresa_id
                      AND unidade_id = :unit_id
                      AND saldo_atual <> TRUNC(saldo_atual)
                )
                """
            ),
            {
                "empresa_id": empresa_id,
                "unit_id": unit_id,
            },
        )

        if (
            fractional_minimum_item_id is not None
            or fractional_balance_exists
        ):
            raise UnidadeComQuantidadesFracionariasError(
                "Não é possível desativar quantidades decimais: "
                "existem itens com saldo atual ou estoque mínimo "
                "fracionário nesta unidade."
            )

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
        limit: int = 50,
        offset: int = 0,
    ) -> list[Unidade]:
        statement = (
            select(Unidade)
            .where(
                Unidade.empresa_id == empresa_id,
                Unidade.ativo.is_(True),
            )
            .order_by(Unidade.id)
            .limit(limit)
            .offset(offset)
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

        if changes.get("permite_decimal") is False:
            company = db.scalar(
                select(Empresa)
                .where(Empresa.id == empresa_id)
                .with_for_update()
            )

            if company is None:
                return None

            unit = db.scalar(
                select(Unidade)
                .where(
                    Unidade.id == unit_id,
                    Unidade.empresa_id == empresa_id,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )

            if unit is None:
                return None

            if unit.permite_decimal:
                try:
                    InventarioService.ensure_company_has_no_open_inventory(
                        db=db,
                        empresa_id=empresa_id,
                    )
                except ItemBloqueadoPorInventarioAbertoError as exc:
                    raise UnidadeBloqueadaPorInventarioAbertoError(
                        "Não é possível alterar a precisão da unidade "
                        "enquanto existe um inventário aberto."
                    ) from exc

                db.scalars(
                    select(Item)
                    .where(
                        Item.empresa_id == empresa_id,
                        Item.unidade_id == unit_id,
                    )
                    .order_by(Item.id)
                    .with_for_update()
                ).all()

                UnidadeService._ensure_no_fractional_quantities(
                    db=db,
                    empresa_id=empresa_id,
                    unit_id=unit_id,
                )
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