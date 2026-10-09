
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select

import pytest

from app.core.inventory_service import (
    InventarioAbertoExistenteError,
    InventarioContagemIncompletaError,
    InventarioNaoAbertoError,
    InventarioService,
    ItemBloqueadoPorInventarioAbertoError,
    QuantidadeContadaFracionariaError,
)
from app.core.item_models import Item
from app.core.item_service import ItemService
from app.core.models import Empresa
from app.core.movement_models import Movimentacao
from app.core.movement_service import MovimentacaoService
from app.core.unit_models import Unidade
from app.shared.database import SessionLocal


def create_context(db, permite_decimal=True, second_item=False):
    company = Empresa(
        nome=f"Empresa {uuid4().hex}",
        ativo=True,
    )
    db.add(company)
    db.flush()

    unit = Unidade(
        empresa_id=company.id,
        nome=f"Unidade {uuid4().hex[:12]}",
        simbolo="UN",
        permite_decimal=permite_decimal,
        ativo=True,
    )
    db.add(unit)
    db.flush()

    item = Item(
        empresa_id=company.id,
        unidade_id=unit.id,
        nome="Item de teste",
        estoque_minimo=Decimal("0.0000"),
        ativo=True,
    )
    db.add(item)
    db.flush()

    second = None

    if second_item:
        second = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Segundo item",
            estoque_minimo=Decimal("0.0000"),
            ativo=True,
        )
        db.add(second)
        db.flush()

    return company, unit, item, second


def rollback_context(db):
    # Reverte também as movimentações, pois seu histórico é imutável.
    db.rollback()
    db.close()


def test_inventory_snapshots_balances_and_only_active_items():
    db = SessionLocal()

    try:
        company, unit, item, _ = create_context(db)

        inactive_item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Item inativo",
            estoque_minimo=Decimal("0.0000"),
            ativo=False,
        )
        db.add(inactive_item)
        db.flush()

        MovimentacaoService.create_movement(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
            tipo="ENTRADA",
            quantidade=Decimal("8.0000"),
        )

        inventory = InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
            observacao=" Contagem inicial ",
        )

        rows = InventarioService.list_inventory_items(
            db=db,
            empresa_id=company.id,
            inventario_id=inventory.id,
        )

        assert inventory.status == "ABERTO"
        assert inventory.observacao == "Contagem inicial"
        assert len(rows) == 1
        assert rows[0].item_id == item.id
        assert rows[0].saldo_sistema == Decimal("8.0000")
        assert rows[0].quantidade_contada is None
        assert rows[0].diferenca is None

    finally:
        rollback_context(db)


def test_company_cannot_open_two_inventories_simultaneously():
    db = SessionLocal()

    try:
        company, _, _, _ = create_context(db)

        InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        with pytest.raises(InventarioAbertoExistenteError):
            InventarioService.create_inventory(
                db=db,
                empresa_id=company.id,
            )

    finally:
        rollback_context(db)


def test_open_inventory_blocks_stock_movements():
    db = SessionLocal()

    try:
        company, _, item, _ = create_context(db)

        InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        with pytest.raises(ItemBloqueadoPorInventarioAbertoError):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo="ENTRADA",
                quantidade=Decimal("1.0000"),
            )

    finally:
        rollback_context(db)


def test_open_inventory_blocks_item_creation_and_unit_change():
    db = SessionLocal()

    try:
        company, original_unit, item, _ = create_context(db)

        other_unit = Unidade(
            empresa_id=company.id,
            nome="Outra unidade",
            simbolo="OU",
            permite_decimal=True,
            ativo=True,
        )
        db.add(other_unit)
        db.flush()

        InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        with pytest.raises(ItemBloqueadoPorInventarioAbertoError):
            ItemService.update_item(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                changes={"unidade_id": other_unit.id},
            )

        with pytest.raises(ItemBloqueadoPorInventarioAbertoError):
            ItemService.create_item(
                db=db,
                empresa_id=company.id,
                unidade_id=original_unit.id,
                nome="Novo item",
                descricao=None,
                estoque_minimo=Decimal("0.0000"),
            )

    finally:
        rollback_context(db)


def test_count_and_completion_generate_adjustment_movement():
    db = SessionLocal()

    try:
        company, _, item, _ = create_context(db)

        MovimentacaoService.create_movement(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
            tipo="ENTRADA",
            quantidade=Decimal("5.0000"),
        )

        inventory = InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        counted_item = InventarioService.record_count(
            db=db,
            empresa_id=company.id,
            inventario_id=inventory.id,
            item_id=item.id,
            quantidade_contada=Decimal("3.0000"),
        )

        assert counted_item is not None
        assert counted_item.quantidade_contada == Decimal("3.0000")
        assert counted_item.diferenca == Decimal("-2.0000")
        assert counted_item.contado_em is not None

        completed = InventarioService.complete_inventory(
            db=db,
            empresa_id=company.id,
            inventario_id=inventory.id,
        )

        assert completed is not None
        assert completed.status == "CONCLUIDO"
        assert completed.concluido_em is not None
        assert completed.cancelado_em is None

        movements = list(
            db.scalars(
                select(Movimentacao)
                .where(
                    Movimentacao.empresa_id == company.id,
                    Movimentacao.item_id == item.id,
                )
                .order_by(Movimentacao.id)
            ).all()
        )

        assert [movement.tipo for movement in movements] == [
            "ENTRADA",
            "AJUSTE_SAIDA",
        ]
        assert movements[-1].quantidade == Decimal("2.0000")

        balance = MovimentacaoService.get_stock_balance(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
        )

        assert balance == Decimal("3.0000")

        with pytest.raises(InventarioNaoAbertoError):
            InventarioService.record_count(
                db=db,
                empresa_id=company.id,
                inventario_id=inventory.id,
                item_id=item.id,
                quantidade_contada=Decimal("4.0000"),
            )

    finally:
        rollback_context(db)


def test_inventory_cannot_be_completed_with_missing_counts():
    db = SessionLocal()

    try:
        company, _, _, _ = create_context(
            db,
            second_item=True,
        )

        inventory = InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        with pytest.raises(InventarioContagemIncompletaError):
            InventarioService.complete_inventory(
                db=db,
                empresa_id=company.id,
                inventario_id=inventory.id,
            )

        assert inventory.status == "ABERTO"

    finally:
        rollback_context(db)


def test_cancelled_inventory_rejects_new_counts():
    db = SessionLocal()

    try:
        company, _, item, _ = create_context(db)

        inventory = InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        cancelled = InventarioService.cancel_inventory(
            db=db,
            empresa_id=company.id,
            inventario_id=inventory.id,
        )

        assert cancelled is not None
        assert cancelled.status == "CANCELADO"
        assert cancelled.cancelado_em is not None
        assert cancelled.concluido_em is None

        with pytest.raises(InventarioNaoAbertoError):
            InventarioService.record_count(
                db=db,
                empresa_id=company.id,
                inventario_id=inventory.id,
                item_id=item.id,
                quantidade_contada=Decimal("1.0000"),
            )

    finally:
        rollback_context(db)


def test_count_rejects_fraction_for_integer_unit():
    db = SessionLocal()

    try:
        company, _, item, _ = create_context(
            db,
            permite_decimal=False,
        )

        inventory = InventarioService.create_inventory(
            db=db,
            empresa_id=company.id,
        )

        with pytest.raises(QuantidadeContadaFracionariaError):
            InventarioService.record_count(
                db=db,
                empresa_id=company.id,
                inventario_id=inventory.id,
                item_id=item.id,
                quantidade_contada=Decimal("1.5000"),
            )

    finally:
        rollback_context(db)