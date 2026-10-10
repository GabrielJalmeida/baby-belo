from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

from sqlalchemy import func, select, text

from app.core.item_models import Item
from app.core.models import Empresa
from app.core.movement_models import Movimentacao
from app.core.movement_service import (
    MovimentacaoService,
    QuantidadeFracionariaError,
)
from app.core.unit_models import Unidade
from app.core.unit_service import (
    UnidadeBloqueadaPorInventarioAbertoError,
    UnidadeComQuantidadesFracionariasError,
    UnidadeService,
)
from app.shared.database import SessionLocal


def test_concurrent_unit_precision_change_and_fractional_movement():
    company_id = None

    try:
        # Prepara registros persistidos para duas sessões independentes.
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

        # Libera as duas operações para começar praticamente juntas.
        start_barrier = Barrier(3)

        def change_unit_precision():
            with SessionLocal() as db:
                try:
                    db.execute(text("SET LOCAL lock_timeout = '10s'"))
                    start_barrier.wait(timeout=10)

                    unit = UnidadeService.update_unit(
                        db=db,
                        empresa_id=company_id,
                        unit_id=unit_id,
                        changes={"permite_decimal": False},
                    )

                    if unit is None:
                        db.rollback()
                        return "unit_not_found"

                    db.commit()
                    return "unit_changed"

                except (
                    UnidadeBloqueadaPorInventarioAbertoError,
                    UnidadeComQuantidadesFracionariasError,
                ):
                    db.rollback()
                    return "unit_rejected"

                except Exception as exc:
                    db.rollback()
                    return (
                        f"unexpected_unit_error:"
                        f"{type(exc).__name__}: {exc}"
                    )

        def register_fractional_movement():
            with SessionLocal() as db:
                try:
                    db.execute(text("SET LOCAL lock_timeout = '10s'"))
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

                except QuantidadeFracionariaError:
                    db.rollback()
                    return "movement_rejected"

                except Exception as exc:
                    db.rollback()
                    return (
                        f"unexpected_movement_error:"
                        f"{type(exc).__name__}: {exc}"
                    )

        with ThreadPoolExecutor(max_workers=2) as executor:
            unit_future = executor.submit(change_unit_precision)
            movement_future = executor.submit(
                register_fractional_movement
            )

            start_barrier.wait(timeout=10)

            outcomes = [
                unit_future.result(timeout=15),
                movement_future.result(timeout=15),
            ]

        assert set(outcomes) in (
            {"unit_changed", "movement_rejected"},
            {"unit_rejected", "movement_recorded"},
        ), f"Resultados inesperados: {outcomes}"

        # Confirma o estado persistido depois das duas transações.
        with SessionLocal() as db:
            decimal_allowed = db.scalar(
                select(Unidade.permite_decimal).where(
                    Unidade.id == unit_id,
                    Unidade.empresa_id == company_id,
                )
            )

            balance = MovimentacaoService.get_stock_balance(
                db=db,
                empresa_id=company_id,
                item_id=item_id,
            )

            movement_count = db.scalar(
                select(func.count())
                .select_from(Movimentacao)
                .where(
                    Movimentacao.empresa_id == company_id,
                    Movimentacao.item_id == item_id,
                )
            )

        if "unit_changed" in outcomes:
            assert decimal_allowed is False
            assert balance == Decimal("0.0000")
            assert movement_count == 0
        else:
            assert decimal_allowed is True
            assert balance == Decimal("1.5000")
            assert movement_count == 1

    finally:
        # Limpeza restrita aos registros desta empresa de teste.
        if company_id is not None:
            with SessionLocal() as db:
                try:
                    db.query(Movimentacao).filter(
                        Movimentacao.empresa_id == company_id
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