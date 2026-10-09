from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.custom.campo_opcao_service import (
    CampoNaoListaError,
    CampoOpcaoCampoNaoEncontradoError,
    CampoOpcaoDuplicadaError,
    CampoOpcaoService,
)
from app.custom.models import Campo, CampoOpcao


def criar_campo(
    campo_id=5,
    empresa_id=10,
    tipo_dado="LISTA",
    ativo=True,
):
    return Campo(
        id=campo_id,
        empresa_id=empresa_id,
        categoria_id=1,
        nome="Material",
        tipo_dado=tipo_dado,
        obrigatorio=False,
        configuracao={},
        ordem_exibicao=0,
        ativo=ativo,
    )


def criar_opcao(
    opcao_id=20,
    campo_id=5,
    valor="Madeira",
    ordem_exibicao=0,
    ativo=True,
):
    return CampoOpcao(
        id=opcao_id,
        campo_id=campo_id,
        valor=valor,
        ordem_exibicao=ordem_exibicao,
        ativo=ativo,
    )


def test_create_option_normalizes_value():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_campo(),
        None,
    ]

    opcao = CampoOpcaoService.create_option(
        db=db,
        empresa_id=10,
        campo_id=5,
        valor="  Madeira  ",
    )

    assert opcao.campo_id == 5
    assert opcao.valor == "Madeira"
    assert opcao.ativo is True

    db.add.assert_called_once_with(opcao)
    db.flush.assert_called_once()


def test_create_option_rejects_missing_or_foreign_field():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    with pytest.raises(CampoOpcaoCampoNaoEncontradoError):
        CampoOpcaoService.create_option(
            db=db,
            empresa_id=10,
            campo_id=999,
            valor="Madeira",
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_create_option_rejects_inactive_field():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    with pytest.raises(CampoOpcaoCampoNaoEncontradoError):
        CampoOpcaoService.create_option(
            db=db,
            empresa_id=10,
            campo_id=5,
            valor="Madeira",
        )

    db.add.assert_not_called()


def test_create_option_rejects_non_list_field():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_campo(tipo_dado="TEXTO_CURTO")

    with pytest.raises(CampoNaoListaError):
        CampoOpcaoService.create_option(
            db=db,
            empresa_id=10,
            campo_id=5,
            valor="Madeira",
        )

    db.add.assert_not_called()


def test_create_option_rejects_blank_value():
    db = MagicMock(spec=Session)
    db.scalar.return_value = criar_campo()

    with pytest.raises(ValueError, match="vazio"):
        CampoOpcaoService.create_option(
            db=db,
            empresa_id=10,
            campo_id=5,
            valor="   ",
        )

    db.add.assert_not_called()


def test_create_option_rejects_duplicate_value():
    db = MagicMock(spec=Session)
    db.scalar.side_effect = [
        criar_campo(),
        100,
    ]

    with pytest.raises(CampoOpcaoDuplicadaError):
        CampoOpcaoService.create_option(
            db=db,
            empresa_id=10,
            campo_id=5,
            valor="Madeira",
        )

    db.add.assert_not_called()


def test_list_options_filters_inactive_options():
    db = MagicMock(spec=Session)
    esperadas = [criar_opcao()]

    db.scalar.return_value = criar_campo()
    db.scalars.return_value.all.return_value = esperadas

    resultado = CampoOpcaoService.list_options(
        db=db,
        empresa_id=10,
        campo_id=5,
    )

    assert resultado == esperadas

    sql = str(db.scalars.call_args.args[0])

    assert "custom.campo_opcoes.campo_id" in sql
    assert "custom.campo_opcoes.ativo" in sql
    assert "ORDER BY custom.campo_opcoes.ordem_exibicao" in sql


def test_get_option_scopes_query_to_company_and_list_field():
    db = MagicMock(spec=Session)
    opcao = criar_opcao()

    db.scalar.return_value = opcao

    resultado = CampoOpcaoService.get_option(
        db=db,
        empresa_id=10,
        opcao_id=20,
    )

    assert resultado is opcao

    sql = str(db.scalar.call_args.args[0])

    assert "custom.campos.empresa_id" in sql
    assert "custom.campos.tipo_dado" in sql
    assert "custom.campo_opcoes.id" in sql


def test_update_option_changes_value_and_order():
    db = MagicMock(spec=Session)
    opcao = criar_opcao()

    db.scalar.side_effect = [
        opcao,
        None,
    ]

    resultado = CampoOpcaoService.update_option(
        db=db,
        empresa_id=10,
        opcao_id=20,
        changes={
            "valor": "  Aço  ",
            "ordem_exibicao": 3,
        },
    )

    assert resultado is opcao
    assert opcao.valor == "Aço"
    assert opcao.ordem_exibicao == 3

    db.flush.assert_called_once()


def test_update_option_can_deactivate():
    db = MagicMock(spec=Session)
    opcao = criar_opcao()

    db.scalar.return_value = opcao

    resultado = CampoOpcaoService.update_option(
        db=db,
        empresa_id=10,
        opcao_id=20,
        changes={"ativo": False},
    )

    assert resultado is opcao
    assert opcao.ativo is False

    db.flush.assert_called_once()


def test_update_option_can_reactivate():
    db = MagicMock(spec=Session)
    opcao = criar_opcao(ativo=False)

    db.scalar.return_value = opcao

    resultado = CampoOpcaoService.update_option(
        db=db,
        empresa_id=10,
        opcao_id=20,
        changes={"ativo": True},
    )

    assert resultado is opcao
    assert opcao.ativo is True


def test_update_option_rejects_duplicate_value():
    db = MagicMock(spec=Session)
    opcao = criar_opcao(valor="Madeira")

    db.scalar.side_effect = [
        opcao,
        99,
    ]

    with pytest.raises(CampoOpcaoDuplicadaError):
        CampoOpcaoService.update_option(
            db=db,
            empresa_id=10,
            opcao_id=20,
            changes={"valor": "Metal"},
        )

    assert opcao.valor == "Madeira"
    db.flush.assert_not_called()


def test_update_option_returns_none_when_not_found():
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    resultado = CampoOpcaoService.update_option(
        db=db,
        empresa_id=10,
        opcao_id=999,
        changes={"ativo": False},
    )

    assert resultado is None
    db.flush.assert_not_called()


def test_update_option_rejects_empty_changes():
    db = MagicMock(spec=Session)

    with pytest.raises(ValueError, match="atualizar"):
        CampoOpcaoService.update_option(
            db=db,
            empresa_id=10,
            opcao_id=20,
            changes={},
        )

    db.scalar.assert_not_called()