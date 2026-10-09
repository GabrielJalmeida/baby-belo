
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.item_models import Item
from app.core.models import Empresa
from app.core.movement_service import (
    ItemInativoError,
    ItemMovimentacaoNaoEncontradoError,
    MovimentacaoService,
    QuantidadeFracionariaError,
    SaldoInsuficienteError,
)
from app.core.movement_models import Movimentacao
from app.core.unit_models import Unidade
from app.shared.database import SessionLocal


def create_context(db, permite_decimal=True, item_ativo=True):
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
        nome=f"Item {uuid4().hex[:12]}",
        estoque_minimo=Decimal("0"),
        ativo=item_ativo,
    )
    db.add(item)
    db.commit()

    return company, unit, item


def cleanup_context(db, company):
    # Remove qualquer movimento não confirmado antes da limpeza.
    db.rollback()

    db.query(Item).filter(
        Item.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.query(Unidade).filter(
        Unidade.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.delete(company)
    db.commit()


def test_create_movement_records_entry_and_calculates_balance():
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(db)

        movement = MovimentacaoService.create_movement(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
            tipo="ENTRADA",
            quantidade=Decimal("10.2500"),
            motivo="Recebimento",
        )

        assert movement.id is not None
        assert movement.ocorrida_em is not None
        assert movement.empresa_id == company.id
        assert movement.item_id == item.id
        assert movement.quantidade == Decimal("10.2500")

        balance = MovimentacaoService.get_stock_balance(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
        )

        assert balance == Decimal("10.2500")

        movements = MovimentacaoService.list_movements(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
        )

        assert movements is not None
        assert len(movements) == 1
        assert movements[0].id == movement.id

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()


def test_balance_applies_direction_of_all_movement_types():
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(db)

        movements = [
            ("ENTRADA", Decimal("10.0000")),
            ("SAIDA", Decimal("3.0000")),
            ("AJUSTE_ENTRADA", Decimal("2.0000")),
            ("AJUSTE_SAIDA", Decimal("1.0000")),
        ]

        for tipo, quantidade in movements:
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo=tipo,
                quantidade=quantidade,
            )

        balance = MovimentacaoService.get_stock_balance(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
        )

        assert balance == Decimal("8.0000")

        history = MovimentacaoService.list_movements(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
        )

        assert history is not None
        assert len(history) == 4

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()


@pytest.mark.parametrize("tipo", ["SAIDA", "AJUSTE_SAIDA"])
def test_rejects_movement_that_would_make_balance_negative(tipo):
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(db)

        with pytest.raises(SaldoInsuficienteError):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo=tipo,
                quantidade=Decimal("1.0000"),
            )

        balance = MovimentacaoService.get_stock_balance(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
        )

        assert balance == Decimal("0.0000")

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()


@pytest.mark.parametrize(
    "quantidade",
    [Decimal("0"), Decimal("-1.0000")],
)
def test_rejects_non_positive_quantity(quantidade):
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(db)

        with pytest.raises(ValueError):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo="ENTRADA",
                quantidade=quantidade,
            )

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()


def test_rejects_fractional_quantity_for_integer_unit():
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(
            db,
            permite_decimal=False,
        )

        with pytest.raises(QuantidadeFracionariaError):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo="ENTRADA",
                quantidade=Decimal("1.5000"),
            )

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()


def test_rejects_movement_for_inactive_item():
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(
            db,
            item_ativo=False,
        )

        with pytest.raises(ItemInativoError):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo="ENTRADA",
                quantidade=Decimal("1.0000"),
            )

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()


def test_cannot_move_item_from_another_company():
    db = SessionLocal()
    company_a = None
    company_b = None

    try:
        company_a, unit_a, item_a = create_context(db)
        company_b, unit_b, item_b = create_context(db)

        with pytest.raises(ItemMovimentacaoNaoEncontradoError):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company_a.id,
                item_id=item_b.id,
                tipo="ENTRADA",
                quantidade=Decimal("1.0000"),
            )

        balance = MovimentacaoService.get_stock_balance(
            db=db,
            empresa_id=company_a.id,
            item_id=item_b.id,
        )

        assert balance is None

    finally:
        if company_a is not None:
            cleanup_context(db, company_a)
        if company_b is not None:
            cleanup_context(db, company_b)
        db.close()


def test_rejects_invalid_movement_type():
    db = SessionLocal()
    company = None

    try:
        company, unit, item = create_context(db)

        with pytest.raises(ValueError, match="Tipo de movimentação"):
            MovimentacaoService.create_movement(
                db=db,
                empresa_id=company.id,
                item_id=item.id,
                tipo="COMPRA",
                quantidade=Decimal("1.0000"),
            )

    finally:
        if company is not None:
            cleanup_context(db, company)
        db.close()