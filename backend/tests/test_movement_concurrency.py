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
    SaldoInsuficienteError,
)
from app.core.unit_models import Unidade
from app.shared.database import SessionLocal


def test_concurrent_exits_cannot_make_stock_negative():
    company_id = None
    item_id = None

    try:
        # Preparação: empresa, unidade, item e uma unidade em estoque.
        with SessionLocal() as db:
            company = Empresa(
                nome=f"Empresa teste concorrência {uuid4().hex}",
                ativo=True,
            )
            db.add(company)
            db.flush()
            company_id = company.id

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
            db.flush()
            item_id = item.id

            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo="ENTRADA",
                quantidade=Decimal("1.0000"),
            )

            db.commit()

        # Três participantes: duas operações e o processo de teste.
        start_barrier = Barrier(3)

        def attempt_exit():
            with SessionLocal() as db:
                try:
                    # Evita que uma espera por bloqueio fique indefinida.
                    db.execute(text("SET LOCAL lock_timeout = '10s'"))
                    start_barrier.wait(timeout=10)

                    MovimentacaoService.create_movement(
                        db=db,
                        empresa_id=company_id,
                        item_id=item_id,
                        tipo="SAIDA",
                        quantidade=Decimal("1.0000"),
                    )

                    db.commit()
                    return "registrada"

                except SaldoInsuficienteError:
                    db.rollback()
                    return "saldo_insuficiente"

                except Exception as exc:
                    db.rollback()
                    return (
                        f"erro:{type(exc).__name__}: {exc}"
                    )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(attempt_exit),
                executor.submit(attempt_exit),
            ]

            start_barrier.wait(timeout=10)

            outcomes = [
                future.result(timeout=15)
                for future in futures
            ]

        assert sorted(outcomes) == [
            "registrada",
            "saldo_insuficiente",
        ], f"Resultados inesperados: {outcomes}"

        # Confere o estado persistido após as duas transações.
        with SessionLocal() as db:
            balance = MovimentacaoService.get_stock_balance(
                db=db,
                empresa_id=company_id,
                item_id=item_id,
            )

            exit_count = db.scalar(
                select(func.count())
                .select_from(Movimentacao)
                .where(
                    Movimentacao.empresa_id == company_id,
                    Movimentacao.item_id == item_id,
                    Movimentacao.tipo == "SAIDA",
                )
            )

        assert balance == Decimal("0.0000")
        assert exit_count == 1

    finally:
        # Remove somente os registros criados por este teste.
        # Primeiro o histórico, depois os itens e a unidade.
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