
from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Numeric,
    UniqueConstraint,
)

from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade


def test_item_uses_core_schema_and_expected_columns():
    table = Item.__table__

    assert table.fullname == "core.itens"
    assert set(table.columns.keys()) == {
        "id",
        "empresa_id",
        "unidade_id",
        "nome",
        "descricao",
        "estoque_minimo",
        "ativo",
        "criado_em",
        "atualizado_em",
    }


def test_item_preserves_numeric_precision_and_defaults():
    table = Item.__table__

    stock_minimum = table.c.estoque_minimo

    assert isinstance(stock_minimum.type, Numeric)
    assert stock_minimum.type.precision == 18
    assert stock_minimum.type.scale == 4
    assert stock_minimum.nullable is False
    assert str(stock_minimum.server_default.arg) == "0"

    assert table.c.ativo.nullable is False
    assert str(table.c.ativo.server_default.arg) == "TRUE"

    assert table.c.id.identity is not None
    assert table.c.id.identity.always is False


def test_item_foreign_keys_preserve_company_isolation():
    table = Item.__table__

    assert Empresa.__table__.fullname == "core.empresas"
    assert Unidade.__table__.fullname == "core.unidades"

    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    company_fk = foreign_keys["fk_itens_empresa"]

    assert [
        element.target_fullname
        for element in company_fk.elements
    ] == ["core.empresas.id"]

    assert company_fk.ondelete == "RESTRICT"

    unit_fk = foreign_keys["fk_itens_unidade_empresa"]

    assert [
        element.parent.name
        for element in unit_fk.elements
    ] == ["empresa_id", "unidade_id"]

    assert [
        element.target_fullname
        for element in unit_fk.elements
    ] == [
        "core.unidades.empresa_id",
        "core.unidades.id",
    ]

    assert unit_fk.ondelete == "RESTRICT"


def test_item_preserves_database_constraints_and_index():
    table = Item.__table__

    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert checks["ck_itens_nome_nao_vazio"] == "BTRIM(nome) <> ''"
    assert (
        checks["ck_itens_estoque_minimo_nao_negativo"]
        == "estoque_minimo >= 0"
    )

    uniques = {
        constraint.name: tuple(
            column.name for column in constraint.columns
        )
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert uniques["uq_itens_empresa_nome"] == (
        "empresa_id",
        "nome",
    )

    assert uniques["uq_itens_empresa_id"] == (
        "empresa_id",
        "id",
    )

    indexes = {
        index.name: tuple(
            column.name for column in index.columns
        )
        for index in table.indexes
    }

    assert indexes["idx_itens_empresa_ativo"] == (
        "empresa_id",
        "ativo",
    )