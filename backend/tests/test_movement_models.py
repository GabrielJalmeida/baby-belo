
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Numeric

from app.core.item_models import Item
from app.core.models import Empresa
from app.core.movement_models import Movimentacao
from app.core.unit_models import Unidade


def test_movement_uses_core_schema_and_expected_columns():
    table = Movimentacao.__table__

    assert table.fullname == "core.movimentacoes"

    assert set(table.columns.keys()) == {
        "id",
        "empresa_id",
        "item_id",
        "tipo",
        "quantidade",
        "motivo",
        "observacao",
        "ocorrida_em",
    }

    assert Empresa.__table__.fullname == "core.empresas"
    assert Item.__table__.fullname == "core.itens"
    assert Unidade.__table__.fullname == "core.unidades"


def test_movement_preserves_quantity_precision_and_timestamp():
    table = Movimentacao.__table__

    quantity = table.c.quantidade

    assert isinstance(quantity.type, Numeric)
    assert quantity.type.precision == 18
    assert quantity.type.scale == 4
    assert quantity.nullable is False

    assert table.c.id.identity is not None
    assert table.c.id.identity.always is False

    assert table.c.ocorrida_em.nullable is False
    assert (
        str(table.c.ocorrida_em.server_default.arg)
        == "CURRENT_TIMESTAMP"
    )


def test_movement_foreign_keys_enforce_company_isolation():
    table = Movimentacao.__table__

    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    company_fk = foreign_keys["fk_movimentacoes_empresa"]

    assert [
        element.target_fullname
        for element in company_fk.elements
    ] == ["core.empresas.id"]

    assert company_fk.ondelete == "RESTRICT"

    item_fk = foreign_keys["fk_movimentacoes_item_empresa"]

    assert [
        element.parent.name
        for element in item_fk.elements
    ] == ["empresa_id", "item_id"]

    assert [
        element.target_fullname
        for element in item_fk.elements
    ] == [
        "core.itens.empresa_id",
        "core.itens.id",
    ]

    assert item_fk.ondelete == "RESTRICT"


def test_movement_preserves_database_checks_and_indexes():
    table = Movimentacao.__table__

    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert checks["ck_movimentacoes_tipo"] == (
        "tipo IN ('ENTRADA', 'SAIDA', "
        "'AJUSTE_ENTRADA', 'AJUSTE_SAIDA')"
    )

    assert (
        checks["ck_movimentacoes_quantidade_positiva"]
        == "quantidade > 0"
    )

    assert (
        checks["ck_movimentacoes_motivo_nao_vazio"]
        == "motivo IS NULL OR BTRIM(motivo) <> ''"
    )

    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert indexes["idx_movimentacoes_item_ocorrida_em"] == (
        "item_id",
        "ocorrida_em",
    )

    assert indexes["idx_movimentacoes_empresa_ocorrida_em"] == (
        "empresa_id",
        "ocorrida_em",
    )