
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.inventory_models import Inventario, InventarioItem
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.movement_models import Movimentacao
from app.core.unit_models import Unidade


QUATRO_CASAS_DECIMAIS = Decimal("0.0001")
LIMITE_NUMERIC_18_4 = Decimal("100000000000000")


class InventarioSemItensError(ValueError):
    """Não existem itens ativos para iniciar a contagem."""


class InventarioAbertoExistenteError(ValueError):
    """A empresa já possui um inventário aberto."""


class InventarioNaoAbertoError(ValueError):
    """A operação exige que o inventário esteja aberto."""


class InventarioContagemIncompletaError(ValueError):
    """Existem itens sem contagem registrada."""


class ItemForaDoInventarioError(ValueError):
    """O item não faz parte do inventário informado."""


class QuantidadeContadaFracionariaError(ValueError):
    """A unidade não aceita uma quantidade contada fracionária."""


class ItemBloqueadoPorInventarioAbertoError(ValueError):
    """A alteração conflita com um inventário aberto."""


class InventarioService:
    @staticmethod
    def ensure_company_has_no_open_inventory(
        db: Session,
        empresa_id: int,
    ) -> None:
        statement = (
            select(Inventario.id)
            .where(
                Inventario.empresa_id == empresa_id,
                Inventario.status == "ABERTO",
            )
            .limit(1)
        )

        if db.scalar(statement) is not None:
            raise ItemBloqueadoPorInventarioAbertoError(
                "Não é permitido alterar o cadastro de itens "
                "enquanto há um inventário aberto."
            )

    @staticmethod
    def ensure_item_not_in_open_inventory(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> None:
        statement = (
            select(Inventario.id)
            .join(
                InventarioItem,
                (InventarioItem.empresa_id == Inventario.empresa_id)
                & (InventarioItem.inventario_id == Inventario.id),
            )
            .where(
                Inventario.empresa_id == empresa_id,
                Inventario.status == "ABERTO",
                InventarioItem.empresa_id == empresa_id,
                InventarioItem.item_id == item_id,
            )
            .limit(1)
        )

        if db.scalar(statement) is not None:
            raise ItemBloqueadoPorInventarioAbertoError(
                "Não é permitido movimentar ou trocar a unidade "
                "de um item que pertence a um inventário aberto."
            )

    @staticmethod
    def _get_inventory(
        db: Session,
        empresa_id: int,
        inventario_id: int,
        lock: bool = False,
    ) -> Inventario | None:
        statement = select(Inventario).where(
            Inventario.empresa_id == empresa_id,
            Inventario.id == inventario_id,
        )

        if lock:
            statement = statement.with_for_update()

        return db.scalar(statement)

    @staticmethod
    def create_inventory(
        db: Session,
        empresa_id: int,
        observacao: str | None = None,
    ) -> Inventario:
        # Serializa a abertura de inventários e a criação de itens
        # para esta empresa.
        company = db.scalar(
            select(Empresa)
            .where(Empresa.id == empresa_id)
            .with_for_update(key_share=True)
        )

        if company is None:
            raise ValueError("Empresa não encontrada.")

        existing_inventory = db.scalar(
            select(Inventario.id)
            .where(
                Inventario.empresa_id == empresa_id,
                Inventario.status == "ABERTO",
            )
            .limit(1)
        )

        if existing_inventory is not None:
            raise InventarioAbertoExistenteError(
                "A empresa já possui um inventário aberto."
            )

        # Primeiro bloqueamos os itens; depois capturamos seus saldos.
        # Assim, uma movimentação concorrente não passa entre as etapas.
        items = list(
            db.scalars(
                select(Item)
                .where(
                    Item.empresa_id == empresa_id,
                    Item.ativo.is_(True),
                )
                .order_by(Item.id)
                .with_for_update()
            ).all()
        )

        if not items:
            raise InventarioSemItensError(
                "Não existem itens ativos para inventariar."
            )

        balance_rows = db.execute(
            text(
                """
                SELECT item_id, saldo_atual
                FROM core.vw_saldos_estoque
                WHERE empresa_id = :empresa_id
                  AND ativo IS TRUE
                ORDER BY item_id
                """
            ),
            {"empresa_id": empresa_id},
        ).mappings().all()

        balances = {
            row["item_id"]: Decimal(
                str(row["saldo_atual"])
            ).quantize(QUATRO_CASAS_DECIMAIS)
            for row in balance_rows
        }

        normalized_observation = (
            observacao.strip() or None
            if observacao is not None
            else None
        )

        inventory = Inventario(
            empresa_id=empresa_id,
            status="ABERTO",
            observacao=normalized_observation,
        )

        db.add(inventory)
        db.flush()

        inventory_items = [
            InventarioItem(
                inventario_id=inventory.id,
                empresa_id=empresa_id,
                item_id=item.id,
                saldo_sistema=balances.get(
                    item.id,
                    Decimal("0.0000"),
                ),
            )
            for item in items
        ]

        db.add_all(inventory_items)
        db.flush()

        return inventory

    @staticmethod
    def list_inventories(
        db: Session,
        empresa_id: int,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Inventario]:
        statement = (
            select(Inventario)
            .where(Inventario.empresa_id == empresa_id)
            .order_by(
                Inventario.iniciado_em.desc(),
                Inventario.id.desc(),
            )
        )

        if limit is not None:
            statement = statement.limit(limit)

        if offset:
            statement = statement.offset(offset)

        return list(db.scalars(statement).all())

    @staticmethod
    def get_inventory(
        db: Session,
        empresa_id: int,
        inventario_id: int,
    ) -> Inventario | None:
        return InventarioService._get_inventory(
            db=db,
            empresa_id=empresa_id,
            inventario_id=inventario_id,
        )

    @staticmethod
    def list_inventory_items(
        db: Session,
        empresa_id: int,
        inventario_id: int,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[InventarioItem]:
        statement = (
            select(InventarioItem)
            .where(
                InventarioItem.empresa_id == empresa_id,
                InventarioItem.inventario_id == inventario_id,
            )
            .order_by(InventarioItem.item_id)
        )

        if limit is not None:
            statement = statement.limit(limit)

        if offset:
            statement = statement.offset(offset)

        return list(db.scalars(statement).all())

    @staticmethod
    def record_count(
        db: Session,
        empresa_id: int,
        inventario_id: int,
        item_id: int,
        quantidade_contada: Decimal,
    ) -> InventarioItem | None:
        inventory = InventarioService._get_inventory(
            db=db,
            empresa_id=empresa_id,
            inventario_id=inventario_id,
            lock=True,
        )

        if inventory is None:
            return None

        if inventory.status != "ABERTO":
            raise InventarioNaoAbertoError(
                "Somente inventários abertos aceitam contagens."
            )

        quantity = Decimal(str(quantidade_contada))

        if (
            not quantity.is_finite()
            or quantity < 0
            or quantity >= LIMITE_NUMERIC_18_4
            or quantity != quantity.quantize(QUATRO_CASAS_DECIMAIS)
        ):
            raise ValueError(
                "A quantidade contada deve ser não negativa "
                "e ter no máximo quatro casas decimais."
            )

        inventory_item = db.scalar(
            select(InventarioItem)
            .where(
                InventarioItem.empresa_id == empresa_id,
                InventarioItem.inventario_id == inventario_id,
                InventarioItem.item_id == item_id,
            )
            .with_for_update()
        )

        if inventory_item is None:
            raise ItemForaDoInventarioError(
                "O item não pertence a este inventário."
            )

        item = db.scalar(
            select(Item)
            .where(
                Item.empresa_id == empresa_id,
                Item.id == item_id,
            )
            .with_for_update()
        )

        if item is None:
            raise ItemForaDoInventarioError(
                "O item não foi encontrado nesta empresa."
            )

        unit = db.scalar(
            select(Unidade).where(
                Unidade.empresa_id == empresa_id,
                Unidade.id == item.unidade_id,
            )
        )

        if unit is None:
            raise ItemForaDoInventarioError(
                "A unidade de medida do item não foi encontrada."
            )

        if (
            not unit.permite_decimal
            and quantity != quantity.to_integral_value()
        ):
            raise QuantidadeContadaFracionariaError(
                "A unidade do item não permite quantidades "
                "fracionárias."
            )

        inventory_item.quantidade_contada = quantity
        inventory_item.contado_em = datetime.now(timezone.utc)

        db.flush()
        db.refresh(inventory_item)

        return inventory_item

    @staticmethod
    def complete_inventory(
        db: Session,
        empresa_id: int,
        inventario_id: int,
    ) -> Inventario | None:
        inventory = InventarioService._get_inventory(
            db=db,
            empresa_id=empresa_id,
            inventario_id=inventario_id,
            lock=True,
        )

        if inventory is None:
            return None

        if inventory.status != "ABERTO":
            raise InventarioNaoAbertoError(
                "Somente inventários abertos podem ser concluídos."
            )

        inventory_items = list(
            db.scalars(
                select(InventarioItem)
                .where(
                    InventarioItem.empresa_id == empresa_id,
                    InventarioItem.inventario_id == inventario_id,
                )
                .order_by(InventarioItem.item_id)
                .with_for_update()
            ).all()
        )

        if not inventory_items:
            raise InventarioSemItensError(
                "O inventário não possui itens para concluir."
            )

        if any(
            row.quantidade_contada is None
            for row in inventory_items
        ):
            raise InventarioContagemIncompletaError(
                "Registre a contagem de todos os itens antes "
                "de concluir o inventário."
            )

        item_ids = [row.item_id for row in inventory_items]

        items = list(
            db.scalars(
                select(Item)
                .where(
                    Item.empresa_id == empresa_id,
                    Item.id.in_(item_ids),
                )
                .order_by(Item.id)
                .with_for_update()
            ).all()
        )

        if len(items) != len(inventory_items):
            raise ItemForaDoInventarioError(
                "Um ou mais itens do inventário não foram encontrados."
            )

        unit_ids = sorted({item.unidade_id for item in items})

        units = list(
            db.scalars(
                select(Unidade)
                .where(
                    Unidade.empresa_id == empresa_id,
                    Unidade.id.in_(unit_ids),
                )
                .order_by(Unidade.id)
                .with_for_update()
            ).all()
        )

        units_by_id = {unit.id: unit for unit in units}
        items_by_id = {item.id: item for item in items}
        now = datetime.now(timezone.utc)
        adjustments: list[Movimentacao] = []

        for inventory_item in inventory_items:
            item = items_by_id[inventory_item.item_id]
            unit = units_by_id.get(item.unidade_id)

            if unit is None:
                raise ItemForaDoInventarioError(
                    "A unidade de medida de um item não foi encontrada."
                )

            counted = Decimal(
                str(inventory_item.quantidade_contada)
            ).quantize(QUATRO_CASAS_DECIMAIS)

            snapshot = Decimal(
                str(inventory_item.saldo_sistema)
            ).quantize(QUATRO_CASAS_DECIMAIS)

            if (
                not unit.permite_decimal
                and counted != counted.to_integral_value()
            ):
                raise QuantidadeContadaFracionariaError(
                    "A unidade do item não permite quantidades "
                    "fracionárias."
                )

            difference = (counted - snapshot).quantize(
                QUATRO_CASAS_DECIMAIS
            )

            if difference == 0:
                continue

            if difference > 0:
                movement_type = "AJUSTE_ENTRADA"
                movement_quantity = difference
            else:
                movement_type = "AJUSTE_SAIDA"
                movement_quantity = -difference

            adjustments.append(
                Movimentacao(
                    empresa_id=empresa_id,
                    item_id=item.id,
                    tipo=movement_type,
                    quantidade=movement_quantity,
                    motivo=f"Ajuste de inventário #{inventory.id}",
                    observacao=(
                        f"Saldo registrado: {snapshot}; "
                        f"contagem física: {counted}."
                    ),
                    ocorrida_em=now,
                )
            )

        # A inserção direta é intencional: o histórico do inventário
        # aberto bloqueia movimentos normais, mas sua conclusão precisa
        # gerar os ajustes correspondentes à contagem.
        db.add_all(adjustments)

        inventory.status = "CONCLUIDO"
        inventory.concluido_em = now
        inventory.cancelado_em = None

        db.flush()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def cancel_inventory(
        db: Session,
        empresa_id: int,
        inventario_id: int,
    ) -> Inventario | None:
        inventory = InventarioService._get_inventory(
            db=db,
            empresa_id=empresa_id,
            inventario_id=inventario_id,
            lock=True,
        )

        if inventory is None:
            return None

        if inventory.status != "ABERTO":
            raise InventarioNaoAbertoError(
                "Somente inventários abertos podem ser cancelados."
            )

        inventory.status = "CANCELADO"
        inventory.cancelado_em = datetime.now(timezone.utc)
        inventory.concluido_em = None

        db.flush()
        db.refresh(inventory)

        return inventory