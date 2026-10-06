from app.auth.models import EmpresaUsuario, Usuario


def test_usuario_mapping():
    assert Usuario.__tablename__ == "usuarios"
    assert Usuario.__table__.schema == "auth"

    assert Usuario.__table__.c.id.type.python_type is int
    assert Usuario.__table__.c.nome.nullable is False
    assert Usuario.__table__.c.email.nullable is False
    assert Usuario.__table__.c.senha_hash.nullable is False


def test_empresa_usuario_mapping():
    assert EmpresaUsuario.__tablename__ == "empresa_usuarios"
    assert EmpresaUsuario.__table__.schema == "auth"

    foreign_keys = {
        (
            fk.parent.name,
            fk.target_fullname,
        )
        for fk in EmpresaUsuario.__table__.foreign_keys
    }

    assert (
        "empresa_id",
        "core.empresas.id",
    ) in foreign_keys

    assert (
        "usuario_id",
        "auth.usuarios.id",
    ) in foreign_keys