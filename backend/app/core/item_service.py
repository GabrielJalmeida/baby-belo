
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.item_models import Item
from app.core.unit_models import Unidade
from app.core.inventory_service import InventarioService
from app.core.models import Empresa


class UnidadeItemInvalidaError(ValueError):
    """A unidade não existe, está inativa ou pertence a outra empresa."""


class EstoqueMinimoFracionarioError(ValueError):
    """A unidade não permite quantidades fracionárias."""


class NomeItemDuplicadoError(ValueError):
    """Já existe um item com esse nome na empresa."""


class ItemService:
    @staticmethod
    def _get_unit(
        db: Session,
        empresa_id: int,
        unidade_id: int,
        require_active: bool = True,
    ) -> Unidade | None:
        statement = select(Unidade).where(
            Unidade.id == unidade_id,
            Unidade.empresa_id == empresa_id,
        )

        if require_active:
            statement = statement.where(
                Unidade.ativo.is_(True),
            )

        return db.scalar(statement)

    @staticmethod
    def _ensure_name_available(
        db: Session,
        empresa_id: int,
        nome: str,
        exclude_item_id: int | None = None,
    ) -> None:
        statement = select(Item.id).where(
            Item.empresa_id == empresa_id,
            Item.nome == nome,
        )

        if exclude_item_id is not None:
            statement = statement.where(
                Item.id != exclude_item_id,
            )

        if db.scalar(statement) is not None:
            raise NomeItemDuplicadoError(
                "Já existe um item com esse nome nesta empresa."
            )

    @staticmethod
    def _validate_stock_minimum(
        unit: Unidade,
        estoque_minimo: Decimal,
    ) -> None:
        if estoque_minimo < 0:
            raise ValueError(
                "O estoque mínimo não pode ser negativo."
            )

        if (
            not unit.permite_decimal
            and estoque_minimo != estoque_minimo.to_integral_value()
        ):
            raise EstoqueMinimoFracionarioError(
                "A unidade selecionada não permite quantidades "
                "fracionárias."
            )

    @staticmethod
    def create_item(
        db: Session,
        empresa_id: int,
        unidade_id: int,
        nome: str,
        descricao: str | None,
        estoque_minimo: Decimal,
    ) -> Item:
        nome = nome.strip()

        if not nome:
            raise ValueError("O nome do item não pode ficar vazio.")

        unit = ItemService._get_unit(
            db=db,
            empresa_id=empresa_id,
            unidade_id=unidade_id,
        )

        if unit is None:
            raise UnidadeItemInvalidaError(
                "A unidade não existe, está inativa ou não pertence "
                "a esta empresa."
            )

        company = db.scalar(
            select(Empresa)
            .where(Empresa.id == empresa_id)
            .with_for_update()
        )

        if company is None or not company.ativo:
            raise ValueError("Empresa não encontrada ou inativa.")

        InventarioService.ensure_company_has_no_open_inventory(
            db=db,
            empresa_id=empresa_id,
        )

        # Revalida a unidade após obter o bloqueio da empresa.
        # Isso evita usar uma configuração antiga de permite_decimal.
        unit = db.scalar(
            select(Unidade)
            .where(
                Unidade.id == unidade_id,
                Unidade.empresa_id == empresa_id,
                Unidade.ativo.is_(True),
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        if unit is None:
            raise UnidadeItemInvalidaError(
                "A unidade não existe, está inativa ou não pertence "
                "a esta empresa."
            )

        ItemService._validate_stock_minimum(
            unit=unit,
            estoque_minimo=estoque_minimo,
        )

        ItemService._ensure_name_available(
            db=db,
            empresa_id=empresa_id,
            nome=nome,
        )

        normalized_description = (
            descricao.strip() or None
            if descricao is not None
            else None
        )

        item = Item(
            empresa_id=empresa_id,
            unidade_id=unidade_id,
            nome=nome,
            descricao=normalized_description,
            estoque_minimo=estoque_minimo,
            ativo=True,
        )

        db.add(item)
        db.flush()

        return item

    @staticmethod
    def list_items(
        db: Session,
        empresa_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]:
        statement = (
            select(Item)
            .where(
                Item.empresa_id == empresa_id,
                Item.ativo.is_(True),
            )
            .order_by(Item.id)
            .limit(limit)
            .offset(offset)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_item(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> Item | None:
        statement = select(Item).where(
            Item.id == item_id,
            Item.empresa_id == empresa_id,
        )

        return db.scalar(statement)

    @staticmethod
    def update_item(
        db: Session,
        empresa_id: int,
        item_id: int,
        changes: dict[str, object],
    ) -> Item | None:
        # Mantém a ordem de bloqueio consistente com a alteração
        # de unidades e a abertura de inventários.
        company = db.scalar(
            select(Empresa)
            .where(Empresa.id == empresa_id)
            .with_for_update(key_share=True)
        )

        if company is None or not company.ativo:
            return None
        item = db.scalar(
            select(Item)
            .where(
                Item.empresa_id == empresa_id,
                Item.id == item_id,
            )
            .with_for_update()
        )

        if item is None:
            return None

        requested_unit_change = "unidade_id" in changes
        target_unit_id = changes.get("unidade_id", item.unidade_id)

        if requested_unit_change and target_unit_id != item.unidade_id:
            InventarioService.ensure_item_not_in_open_inventory(
                db=db,
                empresa_id=empresa_id,
                item_id=item_id,
            )

        requested_unit_change = "unidade_id" in changes
        target_unit_id = changes.get("unidade_id", item.unidade_id)

        unit = ItemService._get_unit(
            db=db,
            empresa_id=empresa_id,
            unidade_id=target_unit_id,
            require_active=requested_unit_change,
        )

        if unit is None:
            raise UnidadeItemInvalidaError(
                "A unidade não existe, está inativa ou não pertence "
                "a esta empresa."
            )

        target_stock_minimum = Decimal(
            str(changes.get("estoque_minimo", item.estoque_minimo))
        )

        ItemService._validate_stock_minimum(
            unit=unit,
            estoque_minimo=target_stock_minimum,
        )

        if "nome" in changes:
            nome = str(changes["nome"]).strip()

            if not nome:
                raise ValueError(
                    "O nome do item não pode ficar vazio."
                )

            ItemService._ensure_name_available(
                db=db,
                empresa_id=empresa_id,
                nome=nome,
                exclude_item_id=item.id,
            )

            item.nome = nome

        if requested_unit_change:
            item.unidade_id = target_unit_id

        if "descricao" in changes:
            descricao = changes["descricao"]
            item.descricao = (
                str(descricao).strip() or None
                if descricao is not None
                else None
            )

        if "estoque_minimo" in changes:
            item.estoque_minimo = target_stock_minimum

        if "ativo" in changes:
            item.ativo = changes["ativo"]

        db.flush()

        return item