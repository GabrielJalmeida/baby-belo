from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.custom.models import ValorItem
from app.custom.valor_item_service import (
    CampoCategoriaIncompativelError,
    CampoValorNaoEncontradoError,
    ItemSemCategoriaError,
    ItemValorNaoEncontradoError,
    OpcaoValorInvalidaError,
    TipoValorIncompativelError,
    ValorItemDuplicadoError,
    ValorItemService,
)


def criar_item(
    item_id=3,
    empresa_id=10,
    ativo=True,
):
    return SimpleNamespace(
        id=item_id,
        empresa_id=empresa_id,
        ativo=ativo,
    )


def criar_associacao(
    item_id=3,
    empresa_id=10,
    categoria_id=8,
):
    return SimpleNamespace(
        item_id=item_id,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
    )


def criar_campo(
    campo_id=5,
    empresa_id=10,
    categoria_id=8,
    tipo_dado="TEXTO_CURTO",
    ativo=True,
):
    return SimpleNamespace(
        id=campo_id,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
        tipo_dado=tipo_dado,
        ativo=ativo,
    )


def criar_valor(
    valor_id=12,
    item_id=3,
    campo_id=5,
    valor_texto="Antigo",
):
    return ValorItem(
        id=valor_id,
        item_id=item_id,
        campo_id=campo_id,
        valor_texto=valor_texto,
    )


def test_create_value_accepts_matching_text_type():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="TEXTO_CURTO"),
        None,
    ]

    registro = ValorItemService.create_value(
        db=db,
        empresa_id=10,
        item_id=3,
        campo_id=5,
        value_fields={"valor_texto": "Madeira"},
    )

    assert registro.item_id == 3
    assert registro.campo_id == 5
    assert registro.valor_texto == "Madeira"
    assert registro.valor_inteiro is None

    db.add.assert_called_once_with(registro)
    db.flush.assert_called_once()


def test_create_value_accepts_false_boolean():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="BOOLEANO"),
        None,
    ]

    registro = ValorItemService.create_value(
        db=db,
        empresa_id=10,
        item_id=3,
        campo_id=5,
        value_fields={"valor_booleano": False},
    )

    assert registro.valor_booleano is False


def test_create_value_accepts_decimal():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="DECIMAL"),
        None,
    ]

    registro = ValorItemService.create_value(
        db=db,
        empresa_id=10,
        item_id=3,
        campo_id=5,
        value_fields={"valor_decimal": Decimal("12.3456")},
    )

    assert registro.valor_decimal == Decimal("12.3456")


def test_create_value_accepts_date():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="DATA"),
        None,
    ]

    registro = ValorItemService.create_value(
        db=db,
        empresa_id=10,
        item_id=3,
        campo_id=5,
        value_fields={"valor_data": date(2026, 10, 8)},
    )

    assert registro.valor_data == date(2026, 10, 8)


def test_create_value_rejects_item_from_another_company():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    with pytest.raises(ItemValorNaoEncontradoError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=999,
            campo_id=5,
            value_fields={"valor_texto": "Madeira"},
        )

    db.add.assert_not_called()


def test_create_value_rejects_inactive_item():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_item(ativo=False)

    with pytest.raises(ItemValorNaoEncontradoError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={"valor_texto": "Madeira"},
        )

    db.add.assert_not_called()


def test_create_value_requires_item_category():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        None,
    ]

    with pytest.raises(ItemSemCategoriaError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={"valor_texto": "Madeira"},
        )

    db.add.assert_not_called()


def test_create_value_rejects_foreign_or_inactive_field():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        None,
    ]

    with pytest.raises(CampoValorNaoEncontradoError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=999,
            value_fields={"valor_texto": "Madeira"},
        )

    db.add.assert_not_called()


def test_create_value_rejects_field_from_another_category():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(categoria_id=8),
        criar_campo(categoria_id=9),
    ]

    with pytest.raises(CampoCategoriaIncompativelError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={"valor_texto": "Madeira"},
        )

    db.add.assert_not_called()


def test_create_value_rejects_value_with_wrong_type():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="INTEIRO"),
    ]

    with pytest.raises(TipoValorIncompativelError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={"valor_texto": "Dez"},
        )

    db.add.assert_not_called()


def test_create_value_rejects_multiple_value_columns():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(),
    ]

    with pytest.raises(ValueError, match="exatamente um"):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={
                "valor_texto": "Dez",
                "valor_inteiro": 10,
            },
        )

    db.add.assert_not_called()


def test_create_value_rejects_duplicate_item_field_pair():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(),
        900,
    ]

    with pytest.raises(ValorItemDuplicadoError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={"valor_texto": "Madeira"},
        )

    db.add.assert_not_called()


def test_create_list_value_requires_active_option_from_same_field():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="LISTA"),
        100,   # A opção existe, está ativa e pertence ao campo.
        None,  # Ainda não existe valor para este item e campo.
    ]

    registro = ValorItemService.create_value(
        db=db,
        empresa_id=10,
        item_id=3,
        campo_id=5,
        value_fields={"opcao_id": 100},
    )

    assert registro.opcao_id == 100


def test_create_list_value_rejects_invalid_option():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="LISTA"),
        None,
        None,
    ]

    with pytest.raises(OpcaoValorInvalidaError):
        ValorItemService.create_value(
            db=db,
            empresa_id=10,
            item_id=3,
            campo_id=5,
            value_fields={"opcao_id": 999},
        )

    db.add.assert_not_called()


def test_list_values_checks_item_ownership():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_item()
    esperado = [criar_valor()]

    db.scalars.return_value.all.return_value = esperado

    resultado = ValorItemService.list_values(
        db=db,
        empresa_id=10,
        item_id=3,
    )

    assert resultado == esperado

    sql = str(db.scalars.call_args.args[0])
    assert "custom.valores_item.item_id" in sql
    assert "ORDER BY custom.valores_item.id" in sql


def test_get_value_scopes_by_company():
    db = MagicMock(spec=Session)
    registro = criar_valor()
    db.scalar.return_value = registro

    resultado = ValorItemService.get_value(
        db=db,
        empresa_id=10,
        valor_id=12,
    )

    assert resultado is registro

    sql = str(db.scalar.call_args.args[0])
    assert "core.itens.empresa_id" in sql
    assert "custom.valores_item.id" in sql


def test_update_value_changes_existing_text_value():
    db = MagicMock(spec=Session)
    registro = criar_valor()

    db.scalar.side_effect = [
        registro,
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="TEXTO_CURTO"),
    ]

    resultado = ValorItemService.update_value(
        db=db,
        empresa_id=10,
        valor_id=12,
        changes={"valor_texto": "Aço"},
    )

    assert resultado is registro
    assert registro.valor_texto == "Aço"
    assert registro.valor_inteiro is None

    db.flush.assert_called_once()


def test_update_value_rejects_incompatible_type():
    db = MagicMock(spec=Session)
    registro = criar_valor()

    db.scalar.side_effect = [
        registro,
        criar_item(),
        criar_associacao(),
        criar_campo(tipo_dado="INTEIRO"),
    ]

    with pytest.raises(TipoValorIncompativelError):
        ValorItemService.update_value(
            db=db,
            empresa_id=10,
            valor_id=12,
            changes={"valor_texto": "Dez"},
        )

    assert registro.valor_texto == "Antigo"
    db.flush.assert_not_called()


def test_update_value_returns_none_for_foreign_or_missing_value():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    resultado = ValorItemService.update_value(
        db=db,
        empresa_id=10,
        valor_id=999,
        changes={"valor_texto": "Aço"},
    )

    assert resultado is None
    db.flush.assert_not_called()


def test_update_value_rejects_empty_changes():
    db = MagicMock(spec=Session)

    with pytest.raises(ValueError, match="exatamente um"):
        ValorItemService.update_value(
            db=db,
            empresa_id=10,
            valor_id=12,
            changes={},
        )

    db.scalar.assert_not_called()