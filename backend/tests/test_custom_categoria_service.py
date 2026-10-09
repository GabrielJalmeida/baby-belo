from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.custom.categoria_service import (
    CategoriaNomeDuplicadoError,
    CategoriaService,
)
from app.custom.models import Categoria


def criar_categoria(
    *,
    categoria_id=10,
    empresa_id=1,
    nome="Ferramentas",
    descricao="Ferramentas gerais",
    ativo=True,
):
    return Categoria(
        id=categoria_id,
        empresa_id=empresa_id,
        nome=nome,
        descricao=descricao,
        ativo=ativo,
    )


def test_create_category_normalizes_values():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    categoria = CategoriaService.create_category(
        db=db,
        empresa_id=7,
        nome="  Ferramentas  ",
        descricao="  Ferramentas gerais  ",
    )

    assert categoria.empresa_id == 7
    assert categoria.nome == "Ferramentas"
    assert categoria.descricao == "Ferramentas gerais"
    assert categoria.ativo is True

    db.add.assert_called_once_with(categoria)
    db.flush.assert_called_once()


def test_create_category_normalizes_empty_description():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    categoria = CategoriaService.create_category(
        db=db,
        empresa_id=7,
        nome="Ferramentas",
        descricao="   ",
    )

    assert categoria.descricao is None


def test_create_category_rejects_blank_name():
    db = MagicMock(spec=Session)

    with pytest.raises(ValueError, match="nome"):
        CategoriaService.create_category(
            db=db,
            empresa_id=7,
            nome="   ",
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_create_category_rejects_duplicate_name():
    db = MagicMock(spec=Session)
    db.scalar.return_value = 42

    with pytest.raises(CategoriaNomeDuplicadoError):
        CategoriaService.create_category(
            db=db,
            empresa_id=7,
            nome="Ferramentas",
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_list_categories_returns_query_results():
    db = MagicMock(spec=Session)
    categorias = [
        criar_categoria(categoria_id=1),
        criar_categoria(categoria_id=2, nome="Materiais"),
    ]

    db.scalars.return_value.all.return_value = categorias

    resultado = CategoriaService.list_categories(
        db=db,
        empresa_id=7,
    )

    assert resultado == categorias

    statement = db.scalars.call_args.args[0]
    sql = str(statement)

    assert "custom.categorias.empresa_id" in sql
    assert "custom.categorias.ativo" in sql
    assert "ORDER BY custom.categorias.id" in sql


def test_get_category_returns_none_when_not_found():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    resultado = CategoriaService.get_category(
        db=db,
        empresa_id=7,
        categoria_id=999,
    )

    assert resultado is None

    statement = db.scalar.call_args.args[0]
    sql = str(statement)

    assert "custom.categorias.empresa_id" in sql
    assert "custom.categorias.id" in sql


def test_update_category_applies_only_supplied_changes():
    db = MagicMock(spec=Session)
    categoria = criar_categoria()

    # Primeira consulta: categoria encontrada.
    # Segunda consulta: novo nome ainda não utilizado.
    db.scalar.side_effect = [categoria, None]

    resultado = CategoriaService.update_category(
        db=db,
        empresa_id=1,
        categoria_id=10,
        changes={"nome": "  Materiais  ", "descricao": None},
    )

    assert resultado is categoria
    assert categoria.nome == "Materiais"
    assert categoria.descricao is None
    assert categoria.ativo is True

    db.flush.assert_called_once()


def test_update_category_can_deactivate():
    db = MagicMock(spec=Session)
    categoria = criar_categoria()

    db.scalar.return_value = categoria

    resultado = CategoriaService.update_category(
        db=db,
        empresa_id=1,
        categoria_id=10,
        changes={"ativo": False},
    )

    assert resultado is categoria
    assert categoria.ativo is False
    db.flush.assert_called_once()


def test_update_category_returns_none_when_not_found():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    resultado = CategoriaService.update_category(
        db=db,
        empresa_id=1,
        categoria_id=999,
        changes={"ativo": False},
    )

    assert resultado is None
    db.flush.assert_not_called()


def test_update_category_rejects_duplicate_name():
    db = MagicMock(spec=Session)
    categoria = criar_categoria()

    # Categoria encontrada; outra categoria usa o novo nome.
    db.scalar.side_effect = [categoria, 20]

    with pytest.raises(CategoriaNomeDuplicadoError):
        CategoriaService.update_category(
            db=db,
            empresa_id=1,
            categoria_id=10,
            changes={"nome": "Materiais"},
        )

    assert categoria.nome == "Ferramentas"
    db.flush.assert_not_called()


def test_update_category_rejects_empty_changes():
    db = MagicMock(spec=Session)

    with pytest.raises(ValueError, match="atualizar"):
        CategoriaService.update_category(
            db=db,
            empresa_id=1,
            categoria_id=10,
            changes={},
        )

    db.scalar.assert_not_called()