from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.custom.item_categoria_service import (
    ItemCategoriaCategoriaNaoEncontradaError,
    ItemCategoriaComValoresError,
    ItemCategoriaItemNaoEncontradoError,
    ItemCategoriaService,
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


def criar_categoria(
    categoria_id=8,
    empresa_id=10,
    ativo=True,
):
    return SimpleNamespace(
        id=categoria_id,
        empresa_id=empresa_id,
        ativo=ativo,
    )


def criar_associacao(
    item_id=3,
    categoria_id=8,
    empresa_id=10,
):
    return SimpleNamespace(
        item_id=item_id,
        categoria_id=categoria_id,
        empresa_id=empresa_id,
    )


def test_assign_category_creates_association():
    db = MagicMock(spec=Session)

    db.scalar.side_effect = [
        criar_item(),
        criar_categoria(),
        None,
    ]

    associacao = ItemCategoriaService.assign_category(
        db=db,
        empresa_id=10,
        item_id=3,
        categoria_id=8,
    )

    assert associacao.item_id == 3
    assert associacao.categoria_id == 8
    assert associacao.empresa_id == 10

    db.add.assert_called_once_with(associacao)
    db.flush.assert_called_once()


def test_assign_category_rejects_item_outside_company():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    with pytest.raises(ItemCategoriaItemNaoEncontradoError):
        ItemCategoriaService.assign_category(
            db=db,
            empresa_id=10,
            item_id=999,
            categoria_id=8,
        )

    db.add.assert_not_called()


def test_assign_category_rejects_inactive_item():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_item(ativo=False)

    with pytest.raises(ItemCategoriaItemNaoEncontradoError):
        ItemCategoriaService.assign_category(
            db=db,
            empresa_id=10,
            item_id=3,
            categoria_id=8,
        )

    db.add.assert_not_called()


def test_assign_category_rejects_category_outside_company():
    db = MagicMock(spec=Session)

    db.scalar.side_effect = [
        criar_item(),
        None,
    ]

    with pytest.raises(ItemCategoriaCategoriaNaoEncontradaError):
        ItemCategoriaService.assign_category(
            db=db,
            empresa_id=10,
            item_id=3,
            categoria_id=99,
        )

    db.add.assert_not_called()


def test_assign_category_returns_existing_association_when_unchanged():
    db = MagicMock(spec=Session)
    associacao = criar_associacao()

    db.scalar.side_effect = [
        criar_item(),
        criar_categoria(),
        associacao,
    ]

    resultado = ItemCategoriaService.assign_category(
        db=db,
        empresa_id=10,
        item_id=3,
        categoria_id=8,
    )

    assert resultado is associacao
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_assign_category_can_change_category_without_custom_values():
    db = MagicMock(spec=Session)
    associacao = criar_associacao(categoria_id=8)

    db.scalar.side_effect = [
        criar_item(),
        criar_categoria(categoria_id=9),
        associacao,
        None,
    ]

    resultado = ItemCategoriaService.assign_category(
        db=db,
        empresa_id=10,
        item_id=3,
        categoria_id=9,
    )

    assert resultado is associacao
    assert associacao.categoria_id == 9
    db.flush.assert_called_once()


def test_assign_category_rejects_change_when_custom_values_exist():
    db = MagicMock(spec=Session)
    associacao = criar_associacao(categoria_id=8)

    db.scalar.side_effect = [
        criar_item(),
        criar_categoria(categoria_id=9),
        associacao,
        100,
    ]

    with pytest.raises(ItemCategoriaComValoresError):
        ItemCategoriaService.assign_category(
            db=db,
            empresa_id=10,
            item_id=3,
            categoria_id=9,
        )

    assert associacao.categoria_id == 8
    db.flush.assert_not_called()


def test_get_item_category_returns_existing_association():
    db = MagicMock(spec=Session)
    associacao = criar_associacao()

    db.scalar.side_effect = [
        criar_item(),
        associacao,
    ]

    resultado = ItemCategoriaService.get_item_category(
        db=db,
        empresa_id=10,
        item_id=3,
    )

    assert resultado is associacao


def test_get_item_category_returns_none_when_unassigned():
    db = MagicMock(spec=Session)

    db.scalar.side_effect = [
        criar_item(),
        None,
    ]

    resultado = ItemCategoriaService.get_item_category(
        db=db,
        empresa_id=10,
        item_id=3,
    )

    assert resultado is None