from app.core.unit_models import Unidade


def test_unidade_mapping():
    assert Unidade.__tablename__ == "unidades"
    assert Unidade.__table_args__[-1]["schema"] == "core"

    columns = Unidade.__table__.c

    assert columns["id"].primary_key is True

    assert columns["empresa_id"].nullable is False
    assert columns["nome"].nullable is False
    assert columns["simbolo"].nullable is True
    assert columns["permite_decimal"].nullable is False
    assert columns["ativo"].nullable is False
    assert columns["criado_em"].nullable is False
    assert columns["atualizado_em"].nullable is False


def test_unidade_empresa_foreign_key():
    foreign_keys = list(
        Unidade.__table__.c.empresa_id.foreign_keys
    )

    assert len(foreign_keys) == 1

    foreign_key = foreign_keys[0]

    assert foreign_key.target_fullname == "core.empresas.id"


def test_unidade_has_expected_constraints_and_index():
    constraint_names = {
        constraint.name
        for constraint in Unidade.__table__.constraints
    }

    assert "ck_unidades_nome_nao_vazio" in constraint_names
    assert "ck_unidades_simbolo_nao_vazio" in constraint_names
    assert "uq_unidades_empresa_nome" in constraint_names
    assert "uq_unidades_empresa_id" in constraint_names

    index_names = {
        index.name
        for index in Unidade.__table__.indexes
    }

    assert "idx_unidades_empresa_ativo" in index_names