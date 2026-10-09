
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.core.item_models import Item
from app.core.models import Empresa
from app.custom.models import (
    Campo,
    CampoOpcao,
    Categoria,
    ItemCategoria,
    ValorItem,
)


def test_custom_models_use_expected_schemas():
    assert Categoria.__table__.fullname == "custom.categorias"
    assert ItemCategoria.__table__.fullname == "custom.item_categorias"
    assert Campo.__table__.fullname == "custom.campos"
    assert CampoOpcao.__table__.fullname == "custom.campo_opcoes"
    assert ValorItem.__table__.fullname == "custom.valores_item"

    assert Empresa.__table__.fullname == "core.empresas"
    assert Item.__table__.fullname == "core.itens"


def test_category_preserves_company_name_uniqueness():
    table = Categoria.__table__

    uniques = {
        constraint.name: tuple(
            column.name for column in constraint.columns
        )
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert uniques["uq_categorias_empresa_nome"] == (
        "empresa_id",
        "nome",
    )


def test_field_preserves_type_constraint_json_config_and_uniqueness():
    table = Campo.__table__

    checks = {
        constraint.name: " ".join(str(constraint.sqltext).split())
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "TEXTO_CURTO" in checks["ck_campos_tipo_dado"]
    assert "LISTA" in checks["ck_campos_tipo_dado"]

    uniques = {
        constraint.name: tuple(
            column.name for column in constraint.columns
        )
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert uniques["uq_campos_categoria_nome"] == (
        "categoria_id",
        "nome",
    )

    assert isinstance(table.c.configuracao.type, JSONB)
    assert table.c.configuracao.nullable is False


def test_item_category_uses_item_as_primary_key():
    table = ItemCategoria.__table__

    assert tuple(
        column.name for column in table.primary_key.columns
    ) == ("item_id",)

    assert {
        column.name for column in table.columns
    } == {"item_id", "categoria_id", "empresa_id"}


def test_custom_values_preserve_numeric_types_and_one_value_constraint():
    table = ValorItem.__table__

    assert table.c.valor_decimal.type.precision == 18
    assert table.c.valor_decimal.type.scale == 4

    assert table.c.valor_monetario.type.precision == 18
    assert table.c.valor_monetario.type.scale == 2

    checks = {
        constraint.name: " ".join(str(constraint.sqltext).split())
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "num_nonnulls(" in checks["ck_valores_item_um_valor"]
    assert ") = 1" in checks["ck_valores_item_um_valor"]


def test_custom_values_preserve_item_field_uniqueness():
    table = ValorItem.__table__

    uniques = {
        constraint.name: tuple(
            column.name for column in constraint.columns
        )
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert uniques["uq_valores_item_item_campo"] == (
        "item_id",
        "campo_id",
    )


def test_custom_tables_keep_named_company_and_item_foreign_keys():
    tables = [
        Categoria.__table__,
        ItemCategoria.__table__,
        Campo.__table__,
        CampoOpcao.__table__,
        ValorItem.__table__,
    ]

    constraints = {
        constraint.name
        for table in tables
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    assert "fk_categorias_empresa" in constraints
    assert "fk_item_categorias_item" in constraints
    assert "fk_item_categorias_categoria" in constraints
    assert "fk_item_categorias_empresa" in constraints
    assert "fk_campos_empresa" in constraints
    assert "fk_campos_categoria" in constraints
    assert "fk_campo_opcoes_campo" in constraints
    assert "fk_valores_item_item" in constraints
    assert "fk_valores_item_campo" in constraints
    assert "fk_valores_item_opcao" in constraints