from app.core.models import Empresa


def test_empresa_mapping():
    assert Empresa.__tablename__ == "empresas"
    assert Empresa.__table_args__[-1]["schema"] == "core"

    columns = Empresa.__table__.c

    assert columns["id"].primary_key is True
    assert columns["nome"].nullable is False
    assert columns["ativo"].nullable is False
    assert columns["criado_em"].nullable is False
    assert columns["atualizado_em"].nullable is False