from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

from sqlalchemy import select, text

from app.core.inventory_models import Inventario, InventarioItem
from app.core.inventory_service import (
    InventarioService,
    ItemBloqueadoPorInventarioAbertoError,
)
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.movement_models import Movimentacao
from app.core.movement_service import MovimentacaoService
from app.core.unit_models import Unidade
from app.shared.database import SessionLocal


def test_concurrent_inventory_open_and_movement_keep_snapshot_consistent():
    company_id = None

    try:
        with SessionLocal() as db:
            company = Empresa(
                nome=f"Empresa concorrência {uuid4().hex}",
                ativo=True,
            )
            db.add(company)
            db.flush()

            unit = Unidade(
                empresa_id=company.id,
                nome=f"Unidade {uuid4().hex[:12]}",
                simbolo="UN",
                permite_decimal=True,
                ativo=True,
            )
            db.add(unit)
            db.flush()

            item = Item(
                empresa_id=company.id,
                unidade_id=unit.id,
                nome=f"Item {uuid4().hex[:12]}",
                estoque_minimo=Decimal("0.0000"),
                ativo=True,
            )
            db.add(item)
            db.commit()

            company_id = company.id
            unit_id = unit.id
            item_id = item.id

        start_barrier = Barrier(3)

        def open_inventory():
            with SessionLocal() as db:
                try:
                    db.execute(
                        text("SET LOCAL lock_timeout = '10s'")
                    )
                    start_barrier.wait(timeout=10)

                    inventory = InventarioService.create_inventory(
                        db=db,
                        empresa_id=company_id,
                    )
                    inventory_id = inventory.id
                    db.commit()

                    return "inventory_opened", inventory_id

                except Exception as exc:
                    db.rollback()
                    return (
                        f"inventory_error:{type(exc).__name__}: {exc}",
                        None,
                    )

        def register_movement():
            with SessionLocal() as db:
                try:
                    db.execute(
                        text("SET LOCAL lock_timeout = '10s'")
                    )
                    start_barrier.wait(timeout=10)

                    MovimentacaoService.create_movement(
                        db=db,
                        empresa_id=company_id,
                        item_id=item_id,
                        tipo="ENTRADA",
                        quantidade=Decimal("1.5000"),
                    )
                    db.commit()

                    return "movement_recorded"

                except ItemBloqueadoPorInventarioAbertoError:
                    db.rollback()
                    return "movement_rejected"

                except Exception as exc:
                    db.rollback()
                    return (
                        f"movement_error:{type(exc).__name__}: {exc}"
                    )

        with ThreadPoolExecutor(max_workers=2) as executor:
            inventory_future = executor.submit(open_inventory)
            movement_future = executor.submit(register_movement)

            start_barrier.wait(timeout=10)

            inventory_result = inventory_future.result(timeout=15)
            movement_result = movement_future.result(timeout=15)

        assert inventory_result[0] == "inventory_opened", (
            f"Abertura inesperada: {inventory_result}"
        )
        assert movement_result in (
            "movement_recorded",
            "movement_rejected",
        ), f"Resultado inesperado: {movement_result}"

        inventory_id = inventory_result[1]

        with SessionLocal() as db:
            inventory_item = db.scalar(
                select(InventarioItem).where(
                    InventarioItem.empresa_id == company_id,
                    InventarioItem.inventario_id == inventory_id,
                    InventarioItem.item_id == item_id,
                )
            )

            balance = MovimentacaoService.get_stock_balance(
                db=db,
                empresa_id=company_id,
                item_id=item_id,
            )

        assert inventory_item is not None
        assert inventory_item.saldo_sistema == balance

        if movement_result == "movement_recorded":
            assert balance == Decimal("1.5000")
        else:
            assert balance == Decimal("0.0000")

    finally:
        if company_id is not None:
            with SessionLocal() as db:
                try:
                    db.query(Movimentacao).filter(
                        Movimentacao.empresa_id == company_id
                    ).delete(synchronize_session=False)

                    db.query(InventarioItem).filter(
                        InventarioItem.empresa_id == company_id
                    ).delete(synchronize_session=False)

                    db.query(Inventario).filter(
                        Inventario.empresa_id == company_id
                    ).delete(synchronize_session=False)

                    db.query(Item).filter(
                        Item.empresa_id == company_id
                    ).delete(synchronize_session=False)

                    db.query(Unidade).filter(
                        Unidade.empresa_id == company_id
                    ).delete(synchronize_session=False)

                    db.query(Empresa).filter(
                        Empresa.id == company_id
                    ).delete(synchronize_session=False)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise