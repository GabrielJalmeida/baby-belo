
from sqlalchemy import (
    CheckConstraint,
    Computed,
    ForeignKeyConstraint,
    Numeric,
    UniqueConstraint,
)

from app.core.inventory_models import Inventario, InventarioItem
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade


def test_inventory_uses_expected_schema_and_columns():
    table = Inventario.__table__

    assert table.fullname == "core.inventarios"
    assert set(table.columns.keys()) == {
        "id",
        "empresa_id",
        "status",
        "observacao",
        "iniciado_em",
        "concluido_em",
        "cancelado_em",
    }

    assert Empresa.__table__.fullname == "core.empresas"


def test_inventory_preserves_status_constraints_and_index():
    table = Inventario.__table__

    checks = {
        constraint.name: " ".join(str(constraint.sqltext).split())
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert checks["ck_inventarios_status"] == (
        "status IN ('ABERTO', 'CONCLUIDO', 'CANCELADO')"
    )

    status_dates = checks["ck_inventarios_status_datas"]

    assert "status = 'ABERTO'" in status_dates
    assert "status = 'CONCLUIDO'" in status_dates
    assert "status = 'CANCELADO'" in status_dates

    uniques = {
        constraint.name: tuple(
            column.name for column in constraint.columns
        )
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert uniques["uq_inventarios_empresa_id"] == (
        "empresa_id",
        "id",
    )

    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert indexes["idx_inventarios_empresa_status"] == (
        "empresa_id",
        "status",
    )


def test_inventory_items_use_composite_primary_key():
    table = InventarioItem.__table__

    assert table.fullname == "core.inventario_itens"

    assert set(table.columns.keys()) == {
        "inventario_id",
        "empresa_id",
        "item_id",
        "saldo_sistema",
        "quantidade_contada",
        "diferenca",
        "contado_em",
    }

    assert tuple(
        column.name for column in table.primary_key.columns
    ) == ("inventario_id", "item_id")

    assert Item.__table__.fullname == "core.itens"
    assert Unidade.__table__.fullname == "core.unidades"


def test_inventory_item_preserves_numeric_and_generated_difference():
    table = InventarioItem.__table__

    for column_name in ("saldo_sistema", "quantidade_contada", "diferenca"):
        column = table.c[column_name]

        assert isinstance(column.type, Numeric)
        assert column.type.precision == 18
        assert column.type.scale == 4

    assert table.c.saldo_sistema.nullable is False
    assert table.c.quantidade_contada.nullable is True
    assert table.c.diferenca.nullable is True

    computed = table.c.diferenca.computed

    assert isinstance(computed, Computed)
    assert str(computed.sqltext) == (
        "quantidade_contada - saldo_sistema"
    )
    assert computed.persisted is True


def test_inventory_item_preserves_company_foreign_keys():
    table = InventarioItem.__table__

    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    inventory_fk = foreign_keys[
        "fk_inventario_itens_inventario_empresa"
    ]

    assert [
        element.parent.name for element in inventory_fk.elements
    ] == ["empresa_id", "inventario_id"]

    assert [
        element.target_fullname for element in inventory_fk.elements
    ] == [
        "core.inventarios.empresa_id",
        "core.inventarios.id",
    ]

    assert inventory_fk.ondelete == "RESTRICT"

    item_fk = foreign_keys["fk_inventario_itens_item_empresa"]

    assert [
        element.parent.name for element in item_fk.elements
    ] == ["empresa_id", "item_id"]

    assert [
        element.target_fullname for element in item_fk.elements
    ] == [
        "core.itens.empresa_id",
        "core.itens.id",
    ]

    assert item_fk.ondelete == "RESTRICT"


def test_inventory_item_preserves_count_constraints_and_index():
    table = InventarioItem.__table__

    checks = {
        constraint.name: " ".join(str(constraint.sqltext).split())
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert checks["ck_inventario_itens_quantidade_contada"] == (
        "quantidade_contada IS NULL OR quantidade_contada >= 0"
    )

    count_date_check = checks["ck_inventario_itens_contagem_data"]

    assert "quantidade_contada IS NULL" in count_date_check
    assert "contado_em IS NULL" in count_date_check
    assert "quantidade_contada IS NOT NULL" in count_date_check
    assert "contado_em IS NOT NULL" in count_date_check

    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert indexes["idx_inventario_itens_item"] == ("item_id",)