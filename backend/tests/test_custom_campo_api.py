from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.custom.models import Campo, CampoOpcao, Categoria, ItemCategoria, ValorItem
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_user_company_membership(db, role="OWNER"):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"campo-{uuid4().hex}@example.com",
        senha="senha-segura-123",
    )

    company = Empresa(
        nome=f"Empresa {uuid4().hex}",
        ativo=True,
    )

    db.add(company)
    db.flush()

    membership = EmpresaUsuario(
        empresa_id=company.id,
        usuario_id=user.id,
        papel=role,
        ativo=True,
    )

    db.add(membership)
    db.commit()

    return user, company, membership


def auth_headers(user, company):
    token = create_access_token(subject=str(user.id))

    return {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }


def cleanup(db, records):
    for user, company, membership in records:
        empresa_id = company.id
        campo_ids = select(Campo.id).where(
            Campo.empresa_id == empresa_id,
        )

        db.query(ValorItem).filter(
            ValorItem.campo_id.in_(campo_ids),
        ).delete(synchronize_session=False)

        db.query(CampoOpcao).filter(
            CampoOpcao.campo_id.in_(campo_ids),
        ).delete(synchronize_session=False)

        db.query(Campo).filter(
            Campo.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(ItemCategoria).filter(
            ItemCategoria.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.query(Categoria).filter(
            Categoria.empresa_id == empresa_id,
        ).delete(synchronize_session=False)

        db.delete(membership)
        db.delete(company)
        db.delete(user)

    db.commit()


def test_create_field_requires_authentication():
    response = client.post(
        "/api/v1/custom/campos",
        json={
            "categoria_id": 1,
            "nome": "Cor",
            "tipo_dado": "TEXTO_CURTO",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.post(
            "/api/v1/custom/campos",
            json={
                "categoria_id": categoria.id,
                "nome": "Cor",
                "tipo_dado": "TEXTO_CURTO",
                "obrigatorio": True,
                "configuracao": {"max_length": 50},
                "ordem_exibicao": 1,
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 201

        body = response.json()
        assert body["empresa_id"] == company.id
        assert body["categoria_id"] == categoria.id
        assert body["nome"] == "Cor"
        assert body["tipo_dado"] == "TEXTO_CURTO"
        assert body["obrigatorio"] is True
        assert body["configuracao"] == {"max_length": 50}
        assert body["ativo"] is True

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_create_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.post(
            "/api/v1/custom/campos",
            json={
                "categoria_id": categoria.id,
                "nome": "Cor",
                "tipo_dado": "TEXTO_CURTO",
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_create_field_rejects_category_from_another_company():
    db = SessionLocal()
    records = []

    try:
        user_a, company_a, membership_a = (
            create_user_company_membership(db)
        )
        records.append((user_a, company_a, membership_a))

        user_b, company_b, membership_b = (
            create_user_company_membership(db)
        )
        records.append((user_b, company_b, membership_b))

        categoria_b = Categoria(
            empresa_id=company_b.id,
            nome="Materiais",
            ativo=True,
        )
        db.add(categoria_b)
        db.commit()
        db.refresh(categoria_b)

        response = client.post(
            "/api/v1/custom/campos",
            json={
                "categoria_id": categoria_b.id,
                "nome": "Cor",
                "tipo_dado": "TEXTO_CURTO",
            },
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_list_fields_only_returns_active_fields_of_company():
    db = SessionLocal()
    records = []

    try:
        user_a, company_a, membership_a = (
            create_user_company_membership(db)
        )
        records.append((user_a, company_a, membership_a))

        user_b, company_b, membership_b = (
            create_user_company_membership(db)
        )
        records.append((user_b, company_b, membership_b))

        categoria_a = Categoria(
            empresa_id=company_a.id,
            nome="Ferramentas",
            ativo=True,
        )
        categoria_b = Categoria(
            empresa_id=company_b.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add_all([categoria_a, categoria_b])
        db.flush()

        db.add_all(
            [
                Campo(
                    empresa_id=company_a.id,
                    categoria_id=categoria_a.id,
                    nome="Cor",
                    tipo_dado="TEXTO_CURTO",
                    ativo=True,
                ),
                Campo(
                    empresa_id=company_a.id,
                    categoria_id=categoria_a.id,
                    nome="Campo Inativo",
                    tipo_dado="TEXTO_CURTO",
                    ativo=False,
                ),
                Campo(
                    empresa_id=company_b.id,
                    categoria_id=categoria_b.id,
                    nome="Campo Privado",
                    tipo_dado="TEXTO_CURTO",
                    ativo=True,
                ),
            ]
        )
        db.commit()

        response = client.get(
            "/api/v1/custom/campos",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 200
        nomes = {campo["nome"] for campo in response.json()}

        assert "Cor" in nomes
        assert "Campo Inativo" not in nomes
        assert "Campo Privado" not in nomes

    finally:
        cleanup(db, records)
        db.close()


def test_list_fields_can_filter_by_category():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria_a = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        categoria_b = Categoria(
            empresa_id=company.id,
            nome="Materiais",
            ativo=True,
        )
        db.add_all([categoria_a, categoria_b])
        db.flush()

        db.add_all(
            [
                Campo(
                    empresa_id=company.id,
                    categoria_id=categoria_a.id,
                    nome="Cor",
                    tipo_dado="TEXTO_CURTO",
                    ativo=True,
                ),
                Campo(
                    empresa_id=company.id,
                    categoria_id=categoria_b.id,
                    nome="Material",
                    tipo_dado="TEXTO_CURTO",
                    ativo=True,
                ),
            ]
        )
        db.commit()

        response = client.get(
            "/api/v1/custom/campos",
            params={"categoria_id": categoria_a.id},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200
        nomes = {campo["nome"] for campo in response.json()}
        assert nomes == {"Cor"}

    finally:
        cleanup(db, records)
        db.close()


def test_get_field_does_not_expose_another_company_field():
    db = SessionLocal()
    records = []

    try:
        user_a, company_a, membership_a = (
            create_user_company_membership(db)
        )
        records.append((user_a, company_a, membership_a))

        user_b, company_b, membership_b = (
            create_user_company_membership(db)
        )
        records.append((user_b, company_b, membership_b))

        categoria_b = Categoria(
            empresa_id=company_b.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria_b)
        db.flush()

        campo_b = Campo(
            empresa_id=company_b.id,
            categoria_id=categoria_b.id,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
            ativo=True,
        )
        db.add(campo_b)
        db.commit()
        db.refresh(campo_b)

        response = client.get(
            f"/api/v1/custom/campos/{campo_b.id}",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_create_duplicate_field_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        headers = auth_headers(user, company)
        payload = {
            "categoria_id": categoria.id,
            "nome": "Cor",
            "tipo_dado": "TEXTO_CURTO",
        }

        primeira = client.post(
            "/api/v1/custom/campos",
            json=payload,
            headers=headers,
        )
        segunda = client.post(
            "/api/v1/custom/campos",
            json=payload,
            headers=headers,
        )

        assert primeira.status_code == 201
        assert segunda.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_patch_field_updates_only_supplied_attributes():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.flush()

        campo = Campo(
            empresa_id=company.id,
            categoria_id=categoria.id,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
            obrigatorio=False,
            ativo=True,
        )
        db.add(campo)
        db.commit()
        db.refresh(campo)

        response = client.patch(
            f"/api/v1/custom/campos/{campo.id}",
            json={"obrigatorio": True},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200
        body = response.json()

        assert body["obrigatorio"] is True
        assert body["nome"] == "Cor"
        assert body["ativo"] is True

    finally:
        cleanup(db, records)
        db.close()


def test_patch_empty_field_payload_is_rejected():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.flush()

        campo = Campo(
            empresa_id=company.id,
            categoria_id=categoria.id,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
        )
        db.add(campo)
        db.commit()
        db.refresh(campo)

        response = client.patch(
            f"/api/v1/custom/campos/{campo.id}",
            json={},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_patch_duplicate_field_name_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.flush()

        campo_a = Campo(
            empresa_id=company.id,
            categoria_id=categoria.id,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
        )
        campo_b = Campo(
            empresa_id=company.id,
            categoria_id=categoria.id,
            nome="Material",
            tipo_dado="TEXTO_CURTO",
        )
        db.add_all([campo_a, campo_b])
        db.commit()
        db.refresh(campo_a)

        response = client.patch(
            f"/api/v1/custom/campos/{campo_a.id}",
            json={"nome": "Material"},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 409

    finally:
        cleanup(db, records)


def test_viewer_cannot_update_field():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.flush()

        campo = Campo(
            empresa_id=company.id,
            categoria_id=categoria.id,
            nome="Cor",
            tipo_dado="TEXTO_CURTO",
            ativo=True,
        )
        db.add(campo)
        db.commit()
        db.refresh(campo)

        response = client.patch(
            f"/api/v1/custom/campos/{campo.id}",
            json={"ativo": False},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_invalid_field_type_returns_validation_error():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            ativo=True,
        )
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.post(
            "/api/v1/custom/campos",
            json={
                "categoria_id": categoria.id,
                "nome": "Cor",
                "tipo_dado": "COR",
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()