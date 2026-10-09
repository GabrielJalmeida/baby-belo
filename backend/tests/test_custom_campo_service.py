from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.custom.campo_service import (
    CampoCategoriaNaoEncontradaError,
    CampoNomeDuplicadoError,
    CampoService,
    CampoEstruturalEmUsoError,
)
from app.custom.models import Campo, Categoria


def criar_categoria(
    categoria_id=1,
    empresa_id=10,
    nome="Ferramentas",
    ativo=True,
):
    return Categoria(
        id=categoria_id,
        empresa_id=empresa_id,
        nome=nome,
        ativo=ativo,
    )


def criar_campo(
    campo_id=5,
    empresa_id=10,
    categoria_id=1,
    nome="Cor",
    tipo_dado="TEXTO_CURTO",
    obrigatorio=False,
    configuracao=None,
    ordem_exibicao=0,
    ativo=True,
):
    return Campo(
        id=campo_id,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
        nome=nome,
        tipo_dado=tipo_dado,
        obrigatorio=obrigatorio,
        configuracao=configuracao or {},
        ordem_exibicao=ordem_exibicao,
        ativo=ativo,
    )


def test_create_field_derives_company_from_valid_category():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_categoria(),
        None,
    ]

    campo = CampoService.create_field(
        db=db,
        empresa_id=10,
        categoria_id=1,
        nome="  Cor  ",
        tipo_dado="TEXTO_CURTO",
        configuracao={"max_length": 50},
    )

    assert campo.empresa_id == 10
    assert campo.categoria_id == 1
    assert campo.nome == "Cor"
    assert campo.tipo_dado == "TEXTO_CURTO"
    assert campo.configuracao == {"max_length": 50}

    db.add.assert_called_once_with(campo)
    db.flush.assert_called_once()


def test_create_field_rejects_missing_or_foreign_category():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    with pytest.raises(CampoCategoriaNaoEncontradaError):
        CampoService.create_field(
            db=db,
            empresa_id=10,
            categoria_id=99,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_create_field_rejects_duplicate_name():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_categoria(),
        123,
    ]

    with pytest.raises(CampoNomeDuplicadoError):
        CampoService.create_field(
            db=db,
            empresa_id=10,
            categoria_id=1,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
        )

    db.add.assert_not_called()


def test_create_field_rejects_blank_name():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_categoria()

    with pytest.raises(ValueError, match="nome"):
        CampoService.create_field(
            db=db,
            empresa_id=10,
            categoria_id=1,
            nome="   ",
            tipo_dado="TEXTO_CURTO",
        )

    db.add.assert_not_called()


def test_create_field_rejects_non_object_configuration():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_categoria()

    with pytest.raises(ValueError, match="objeto JSON"):
        CampoService.create_field(
            db=db,
            empresa_id=10,
            categoria_id=1,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
            configuracao=["inválido"],
        )


def test_list_fields_filters_by_company_and_active_status():
    db = MagicMock(spec=Session)
    esperado = [criar_campo()]

    db.scalars.return_value.all.return_value = esperado

    resultado = CampoService.list_fields(
        db=db,
        empresa_id=10,
        categoria_id=1,
    )

    assert resultado == esperado

    sql = str(db.scalars.call_args.args[0])

    assert "custom.campos.empresa_id" in sql
    assert "custom.campos.ativo" in sql
    assert "custom.campos.categoria_id" in sql
    assert "ORDER BY custom.campos.ordem_exibicao" in sql


def test_get_field_scopes_query_to_company():
    db = MagicMock(spec=Session)
    campo = criar_campo()
    db.scalar.return_value = campo

    resultado = CampoService.get_field(
        db=db,
        empresa_id=10,
        campo_id=5,
    )

    assert resultado is campo

    sql = str(db.scalar.call_args.args[0])

    assert "custom.campos.empresa_id" in sql
    assert "custom.campos.id" in sql


def test_update_field_applies_partial_changes():
    db = MagicMock(spec=Session)
    campo = criar_campo()

    # Campo encontrado; nome ainda não utilizado na categoria.
    db.scalar.side_effect = [campo, None]

    resultado = CampoService.update_field(
        db=db,
        empresa_id=10,
        campo_id=5,
        changes={"nome": "Material", "obrigatorio": True},
    )

    assert resultado is campo
    assert campo.nome == "Material"
    assert campo.obrigatorio is True
    assert campo.tipo_dado == "TEXTO_CURTO"

    db.flush.assert_called_once()


def test_update_field_can_deactivate_field_with_existing_values():
    db = MagicMock(spec=Session)
    campo = criar_campo(ativo=True)

    db.scalar.return_value = campo

    resultado = CampoService.update_field(
        db=db,
        empresa_id=10,
        campo_id=5,
        changes={"ativo": False},
    )

    assert resultado is campo
    assert campo.ativo is False
    db.flush.assert_called_once()


def test_update_field_rejects_type_change_when_values_exist():
    db = MagicMock(spec=Session)
    campo = criar_campo(tipo_dado="TEXTO_CURTO")

    # Campo encontrado; existe pelo menos um valor cadastrado.
    db.scalar.side_effect = [campo, 100]

    with pytest.raises(CampoEstruturalEmUsoError):
        CampoService.update_field(
            db=db,
            empresa_id=10,
            campo_id=5,
            changes={"tipo_dado": "INTEIRO"},
        )

    assert campo.tipo_dado == "TEXTO_CURTO"
    db.flush.assert_not_called()


def test_update_field_rejects_category_change_when_values_exist():
    db = MagicMock(spec=Session)
    campo = criar_campo(categoria_id=1)

    categoria_destino = criar_categoria(
        categoria_id=2,
        empresa_id=10,
        nome="Materiais",
    )

    # Campo encontrado, categoria destino válida e valor existente.
    db.scalar.side_effect = [
        campo,
        categoria_destino,
        100,
    ]

    with pytest.raises(CampoEstruturalEmUsoError):
        CampoService.update_field(
            db=db,
            empresa_id=10,
            campo_id=5,
            changes={"categoria_id": 2},
        )

    assert campo.categoria_id == 1
    db.flush.assert_not_called()


def test_update_field_rejects_category_from_another_company():
    db = MagicMock(spec=Session)
    campo = criar_campo()

    # Campo encontrado; categoria não é acessível nesta empresa.
    db.scalar.side_effect = [campo, None]

    with pytest.raises(CampoCategoriaNaoEncontradaError):
        CampoService.update_field(
            db=db,
            empresa_id=10,
            campo_id=5,
            changes={"categoria_id": 99},
        )

    assert campo.categoria_id == 1
    db.flush.assert_not_called()


def test_update_field_rejects_duplicate_name():
    db = MagicMock(spec=Session)
    campo = criar_campo(nome="Cor")

    # Campo encontrado; outro campo usa o nome Material.
    db.scalar.side_effect = [campo, 99]

    with pytest.raises(CampoNomeDuplicadoError):
        CampoService.update_field(
            db=db,
            empresa_id=10,
            campo_id=5,
            changes={"nome": "Material"},
        )

    assert campo.nome == "Cor"
    db.flush.assert_not_called()


def test_update_field_returns_none_when_field_is_not_found():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    resultado = CampoService.update_field(
        db=db,
        empresa_id=10,
        campo_id=999,
        changes={"ativo": False},
    )

    assert resultado is None
    db.flush.assert_not_called()


def test_update_field_rejects_empty_changes():
    db = MagicMock(spec=Session)

    with pytest.raises(ValueError, match="atualizar"):
        CampoService.update_field(
            db=db,
            empresa_id=10,
            campo_id=5,
            changes={},
        )

    db.scalar.assert_not_called()