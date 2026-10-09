
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.inventory_schemas import (
    InventarioContagemUpdate,
    InventarioCreate,
    InventarioDetalheResponse,
    InventarioItemResponse,
    InventarioResponse,
)


def test_inventory_create_normalizes_observation():
    data = InventarioCreate(
        observacao="  Contagem do depósito principal  ",
    )

    assert data.observacao == "Contagem do depósito principal"


def test_inventory_create_defaults_observation_to_none():
    data = InventarioCreate()

    assert data.observacao is None


def test_inventory_create_converts_blank_observation_to_none():
    data = InventarioCreate(observacao="   ")

    assert data.observacao is None


def test_inventory_count_accepts_zero():
    data = InventarioContagemUpdate(
        quantidade_contada=Decimal("0"),
    )

    assert data.quantidade_contada == Decimal("0")


def test_inventory_count_accepts_four_decimal_places():
    data = InventarioContagemUpdate(
        quantidade_contada=Decimal("12.3456"),
    )

    assert data.quantidade_contada == Decimal("12.3456")


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("-0.0001"),
        Decimal("1.23456"),
        Decimal("100000000000000.0000"),
    ],
)
def test_inventory_count_rejects_invalid_quantity(quantity):
    with pytest.raises(ValidationError):
        InventarioContagemUpdate(
            quantidade_contada=quantity,
        )


def test_inventory_count_requires_quantity():
    with pytest.raises(ValidationError):
        InventarioContagemUpdate()


def test_inventory_response_rejects_unknown_status():
    with pytest.raises(ValidationError):
        InventarioResponse(
            id=1,
            empresa_id=1,
            status="EM_ANDAMENTO",
            observacao=None,
            iniciado_em=datetime.now(timezone.utc),
            concluido_em=None,
            cancelado_em=None,
        )


def test_inventory_detail_contains_counted_items():
    now = datetime.now(timezone.utc)

    item = InventarioItemResponse(
        inventario_id=1,
        empresa_id=2,
        item_id=3,
        saldo_sistema=Decimal("10.0000"),
        quantidade_contada=Decimal("8.0000"),
        diferenca=Decimal("-2.0000"),
        contado_em=now,
    )

    detail = InventarioDetalheResponse(
        id=1,
        empresa_id=2,
        status="ABERTO",
        observacao="Contagem do depósito",
        iniciado_em=now,
        concluido_em=None,
        cancelado_em=None,
        itens=[item],
    )

    assert detail.status == "ABERTO"
    assert len(detail.itens) == 1
    assert detail.itens[0].item_id == 3
    assert detail.itens[0].diferenca == Decimal("-2.0000")