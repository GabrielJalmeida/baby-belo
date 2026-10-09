from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.custom.schemas import (
    CampoCreate,
    CampoOpcaoCreate,
    CampoOpcaoUpdate,
    CampoUpdate,
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
    ItemCategoriaCreate,
    ValorItemCreate,
)


# ============================================================
# Categorias
# ============================================================

def test_categoria_create_normalizes_text():
    schema = CategoriaCreate(
        nome="  Ferramentas  ",
        descricao="  Ferramentas de manutenção  ",
    )

    assert schema.nome == "Ferramentas"
    assert schema.descricao == "Ferramentas de manutenção"


def test_categoria_create_converts_empty_description_to_none():
    schema = CategoriaCreate(
        nome="Ferramentas",
        descricao="   ",
    )

    assert schema.descricao is None


def test_categoria_create_rejects_blank_name():
    with pytest.raises(ValidationError):
        CategoriaCreate(nome="   ")


def test_categoria_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        CategoriaUpdate()


def test_categoria_update_rejects_null_name_when_supplied():
    with pytest.raises(ValidationError):
        CategoriaUpdate(nome=None)


def test_categoria_update_accepts_deactivation():
    schema = CategoriaUpdate(ativo=False)

    assert schema.ativo is False


# ============================================================
# Campos personalizados
# ============================================================

def test_campo_create_accepts_supported_type():
    schema = CampoCreate(
        categoria_id=1,
        nome="  Cor  ",
        tipo_dado="TEXTO_CURTO",
    )

    assert schema.nome == "Cor"
    assert schema.tipo_dado == "TEXTO_CURTO"
    assert schema.obrigatorio is False
    assert schema.configuracao == {}


def test_campo_create_rejects_unsupported_type():
    with pytest.raises(ValidationError):
        CampoCreate(
            categoria_id=1,
            nome="Cor",
            tipo_dado="COR",
        )


def test_campo_create_rejects_invalid_category_id():
    with pytest.raises(ValidationError):
        CampoCreate(
            categoria_id=0,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
        )


def test_campo_create_does_not_share_configuration_between_instances():
    primeiro = CampoCreate(
        categoria_id=1,
        nome="Cor",
        tipo_dado="TEXTO_CURTO",
    )
    segundo = CampoCreate(
        categoria_id=1,
        nome="Material",
        tipo_dado="TEXTO_CURTO",
    )

    primeiro.configuracao["origem"] = "teste"

    assert segundo.configuracao == {}


def test_campo_update_accepts_partial_payload():
    schema = CampoUpdate(ativo=False)

    assert schema.ativo is False


def test_campo_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        CampoUpdate()


# ============================================================
# Opções
# ============================================================

def test_campo_opcao_create_normalizes_value():
    schema = CampoOpcaoCreate(
        campo_id=1,
        valor="  Azul  ",
    )

    assert schema.valor == "Azul"


def test_campo_opcao_create_rejects_blank_value():
    with pytest.raises(ValidationError):
        CampoOpcaoCreate(
            campo_id=1,
            valor="   ",
        )


def test_campo_opcao_update_accepts_deactivation():
    schema = CampoOpcaoUpdate(ativo=False)

    assert schema.ativo is False


def test_campo_opcao_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        CampoOpcaoUpdate()


# ============================================================
# Associação de categoria ao item
# ============================================================

def test_item_categoria_requires_positive_category_id():
    with pytest.raises(ValidationError):
        ItemCategoriaCreate(categoria_id=0)


def test_item_categoria_accepts_positive_category_id():
    schema = ItemCategoriaCreate(categoria_id=5)

    assert schema.categoria_id == 5


# ============================================================
# Valores personalizados
# ============================================================

def test_valor_item_accepts_text_value():
    schema = ValorItemCreate(
        campo_id=1,
        valor_texto="Madeira",
    )

    assert schema.campo_id == 1
    assert schema.valor_texto == "Madeira"


def test_valor_item_accepts_false_as_a_valid_boolean_value():
    schema = ValorItemCreate(
        campo_id=1,
        valor_booleano=False,
    )

    assert schema.valor_booleano is False


def test_valor_item_accepts_decimal_with_four_places():
    schema = ValorItemCreate(
        campo_id=1,
        valor_decimal=Decimal("12.3456"),
    )

    assert schema.valor_decimal == Decimal("12.3456")


def test_valor_item_rejects_decimal_with_too_many_places():
    with pytest.raises(ValidationError):
        ValorItemCreate(
            campo_id=1,
            valor_decimal=Decimal("12.34567"),
        )


def test_valor_item_accepts_monetary_value_with_two_places():
    schema = ValorItemCreate(
        campo_id=1,
        valor_monetario=Decimal("125.90"),
    )

    assert schema.valor_monetario == Decimal("125.90")


def test_valor_item_accepts_date():
    schema = ValorItemCreate(
        campo_id=1,
        valor_data=date(2026, 10, 8),
    )

    assert schema.valor_data == date(2026, 10, 8)


def test_valor_item_accepts_list_option():
    schema = ValorItemCreate(
        campo_id=1,
        opcao_id=4,
    )

    assert schema.opcao_id == 4


def test_valor_item_rejects_no_value():
    with pytest.raises(ValidationError):
        ValorItemCreate(campo_id=1)


def test_valor_item_rejects_multiple_values():
    with pytest.raises(ValidationError):
        ValorItemCreate(
            campo_id=1,
            valor_texto="Madeira",
            valor_inteiro=10,
        )


def test_valor_item_rejects_non_positive_field_id():
    with pytest.raises(ValidationError):
        ValorItemCreate(
            campo_id=0,
            valor_texto="Madeira",
        )


# ============================================================
# Schemas de leitura
# ============================================================

def test_categoria_read_accepts_orm_style_attributes():
    agora = datetime(2026, 10, 8, 12, 0, 0)

    objeto = SimpleNamespace(
        id=1,
        empresa_id=2,
        nome="Ferramentas",
        descricao=None,
        ativo=True,
        criado_em=agora,
        atualizado_em=agora,
    )

    schema = CategoriaRead.model_validate(objeto)

    assert schema.id == 1
    assert schema.empresa_id == 2
    assert schema.nome == "Ferramentas"
    assert schema.ativo is True