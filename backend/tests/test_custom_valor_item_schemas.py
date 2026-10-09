from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.custom.schemas import ValorItemUpdate


def test_valor_item_update_accepts_one_text_value():
    schema = ValorItemUpdate(valor_texto="Madeira")

    assert schema.valor_texto == "Madeira"


def test_valor_item_update_accepts_false_boolean():
    schema = ValorItemUpdate(valor_booleano=False)

    assert schema.valor_booleano is False


def test_valor_item_update_accepts_decimal():
    schema = ValorItemUpdate(valor_decimal=Decimal("12.3456"))

    assert schema.valor_decimal == Decimal("12.3456")


def test_valor_item_update_accepts_date():
    schema = ValorItemUpdate(valor_data=date(2026, 10, 8))

    assert schema.valor_data == date(2026, 10, 8)


def test_valor_item_update_accepts_option_id():
    schema = ValorItemUpdate(opcao_id=4)

    assert schema.opcao_id == 4


def test_valor_item_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        ValorItemUpdate()


def test_valor_item_update_rejects_multiple_values():
    with pytest.raises(ValidationError):
        ValorItemUpdate(
            valor_texto="Madeira",
            valor_inteiro=10,
        )


def test_valor_item_update_rejects_explicit_null():
    with pytest.raises(ValidationError):
        ValorItemUpdate(valor_texto=None)


def test_valor_item_update_rejects_decimal_with_too_many_places():
    with pytest.raises(ValidationError):
        ValorItemUpdate(valor_decimal=Decimal("12.34567"))