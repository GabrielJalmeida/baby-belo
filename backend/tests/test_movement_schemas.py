
from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.movement_schemas import MovimentacaoCreate


def test_create_normalizes_optional_text():
    movement = MovimentacaoCreate(
        item_id=1,
        tipo="ENTRADA",
        quantidade="2.5000",
        motivo=" Compra de materiais ",
        observacao=" Recebimento inicial ",
    )

    assert movement.motivo == "Compra de materiais"
    assert movement.observacao == "Recebimento inicial"
    assert movement.quantidade == Decimal("2.5000")
    assert movement.ocorrida_em is None


def test_create_accepts_four_decimal_places():
    movement = MovimentacaoCreate(
        item_id=1,
        tipo="ENTRADA",
        quantidade="12.3456",
    )

    assert movement.quantidade == Decimal("12.3456")


@pytest.mark.parametrize(
    "quantidade",
    [
        Decimal("0"),
        Decimal("0.0000"),
        Decimal("-0.0001"),
    ],
)
def test_create_rejects_non_positive_quantity(quantidade):
    with pytest.raises(ValidationError):
        MovimentacaoCreate(
            item_id=1,
            tipo="ENTRADA",
            quantidade=quantidade,
        )


@pytest.mark.parametrize(
    "quantidade",
    [
        Decimal("1.23456"),
        Decimal("100000000000000.0000"),
    ],
)
def test_create_rejects_quantity_outside_precision(quantidade):
    with pytest.raises(ValidationError):
        MovimentacaoCreate(
            item_id=1,
            tipo="ENTRADA",
            quantidade=quantidade,
        )


@pytest.mark.parametrize(
    "tipo",
    ["REMOVIDA", "entrada", ""],
)
def test_create_rejects_invalid_movement_type(tipo):
    with pytest.raises(ValidationError):
        MovimentacaoCreate(
            item_id=1,
            tipo=tipo,
            quantidade="1.0000",
        )


@pytest.mark.parametrize("motivo", ["", "   "])
def test_create_rejects_blank_reason(motivo):
    with pytest.raises(ValidationError):
        MovimentacaoCreate(
            item_id=1,
            tipo="ENTRADA",
            quantidade="1.0000",
            motivo=motivo,
        )


@pytest.mark.parametrize(
    "field",
    ["item_id", "tipo", "quantidade"],
)
def test_create_rejects_null_required_fields(field):
    payload = {
        "item_id": 1,
        "tipo": "ENTRADA",
        "quantidade": "1.0000",
    }
    payload[field] = None

    with pytest.raises(ValidationError):
        MovimentacaoCreate(**payload)


def test_create_normalizes_blank_observation_to_none():
    movement = MovimentacaoCreate(
        item_id=1,
        tipo="AJUSTE_ENTRADA",
        quantidade="1.0000",
        observacao="   ",
    )

    assert movement.observacao is None


def test_create_rejects_datetime_without_timezone():
    with pytest.raises(ValidationError):
        MovimentacaoCreate(
            item_id=1,
            tipo="ENTRADA",
            quantidade="1.0000",
            ocorrida_em=datetime(2026, 10, 8, 12, 0, 0),
        )


def test_create_accepts_datetime_with_timezone():
    movement = MovimentacaoCreate(
        item_id=1,
        tipo="ENTRADA",
        quantidade="1.0000",
        ocorrida_em="2026-10-08T12:00:00-03:00",
    )

    assert movement.ocorrida_em is not None
    assert movement.ocorrida_em.utcoffset() is not None