
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.item_schemas import ItemCreate, ItemUpdate


def test_item_create_applies_defaults_and_normalizes_values():
    item = ItemCreate(
        unidade_id=1,
        nome="  Papel A4  ",
        descricao="  Resma de papel  ",
    )

    assert item.nome == "Papel A4"
    assert item.descricao == "Resma de papel"
    assert item.estoque_minimo == Decimal("0")


def test_item_create_accepts_four_decimal_places():
    item = ItemCreate(
        unidade_id=1,
        nome="Produto fracionado",
        estoque_minimo=Decimal("12.3456"),
    )

    assert item.estoque_minimo == Decimal("12.3456")


@pytest.mark.parametrize("nome", ["", "   "])
def test_item_create_rejects_empty_name(nome):
    with pytest.raises(ValidationError):
        ItemCreate(
            unidade_id=1,
            nome=nome,
        )


@pytest.mark.parametrize(
    "estoque_minimo",
    [
        Decimal("-0.0001"),
        Decimal("1.23456"),
        Decimal("100000000000000.0000"),
    ],
)
def test_item_create_rejects_invalid_stock_minimum(estoque_minimo):
    with pytest.raises(ValidationError):
        ItemCreate(
            unidade_id=1,
            nome="Produto",
            estoque_minimo=estoque_minimo,
        )


@pytest.mark.parametrize("unidade_id", [0, -1])
def test_item_create_rejects_invalid_unit_id(unidade_id):
    with pytest.raises(ValidationError):
        ItemCreate(
            unidade_id=unidade_id,
            nome="Produto",
        )


@pytest.mark.parametrize(
    "field",
    ["nome", "unidade_id", "estoque_minimo", "ativo"],
)
def test_item_update_rejects_null_for_required_fields(field):
    with pytest.raises(ValidationError):
        ItemUpdate(**{field: None})


def test_item_update_preserves_patch_semantics():
    empty_update = ItemUpdate()

    assert empty_update.model_dump(exclude_unset=True) == {}

    clear_description = ItemUpdate(descricao=None)

    assert clear_description.model_dump(exclude_unset=True) == {
        "descricao": None
    }

    normalize_description = ItemUpdate(descricao="   ")

    assert normalize_description.descricao is None
    assert normalize_description.model_dump(
        exclude_unset=True
    ) == {"descricao": None}