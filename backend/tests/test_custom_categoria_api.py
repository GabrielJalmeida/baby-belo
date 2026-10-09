from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.models import Empresa
from app.custom.models import Categoria
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_user_company_membership(db, role="OWNER"):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"categoria-{uuid4().hex}@example.com",
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


def cleanup(db, records):
    for user, company, membership in records:
        db.query(Categoria).filter(
            Categoria.empresa_id == company.id
        ).delete(synchronize_session=False)

        db.delete(membership)
        db.delete(company)
        db.delete(user)

    db.commit()


def auth_headers(user, company):
    token = create_access_token(subject=str(user.id))

    return {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }


def test_create_category_requires_authentication():
    response = client.post(
        "/api/v1/custom/categorias",
        json={"nome": "Ferramentas"},
    )

    assert response.status_code == 401


def test_owner_can_create_category():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        response = client.post(
            "/api/v1/custom/categorias",
            json={
                "nome": "  Ferramentas  ",
                "descricao": "  Itens de manutenção  ",
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 201

        body = response.json()

        assert body["empresa_id"] == company.id
        assert body["nome"] == "Ferramentas"
        assert body["descricao"] == "Itens de manutenção"
        assert body["ativo"] is True
        assert body["id"] > 0

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_create_category():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="VIEWER",
        )
        records.append((user, company, membership))

        response = client.post(
            "/api/v1/custom/categorias",
            json={"nome": "Ferramentas"},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_list_categories_only_returns_active_categories_from_company():
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

        db.add_all(
            [
                Categoria(
                    empresa_id=company_a.id,
                    nome="Ferramentas",
                    ativo=True,
                ),
                Categoria(
                    empresa_id=company_a.id,
                    nome="Categoria Inativa",
                    ativo=False,
                ),
                Categoria(
                    empresa_id=company_b.id,
                    nome="Categoria de Outra Empresa",
                    ativo=True,
                ),
            ]
        )
        db.commit()

        response = client.get(
            "/api/v1/custom/categorias",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 200

        nomes = {item["nome"] for item in response.json()}

        assert "Ferramentas" in nomes
        assert "Categoria Inativa" not in nomes
        assert "Categoria de Outra Empresa" not in nomes

    finally:
        cleanup(db, records)
        db.close()


def test_get_category_does_not_expose_another_company_category():
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

        categoria = Categoria(
            empresa_id=company_b.id,
            nome="Privada",
            ativo=True,
        )

        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.get(
            f"/api/v1/custom/categorias/{categoria.id}",
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_get_category_returns_not_found_for_inactive_category():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Inativa",
            ativo=False,
        )

        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.get(
            f"/api/v1/custom/categorias/{categoria.id}",
            headers=auth_headers(user, company),
        )

        assert response.status_code == 404

    finally:
        cleanup(db, records)
        db.close()


def test_operator_can_update_category_and_clear_description():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(
            db,
            role="OPERATOR",
        )
        records.append((user, company, membership))

        categoria = Categoria(
            empresa_id=company.id,
            nome="Ferramentas",
            descricao="Descrição anterior",
            ativo=True,
        )

        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.patch(
            f"/api/v1/custom/categorias/{categoria.id}",
            json={
                "nome": "Ferramentas Gerais",
                "descricao": None,
            },
            headers=auth_headers(user, company),
        )

        assert response.status_code == 200

        body = response.json()

        assert body["nome"] == "Ferramentas Gerais"
        assert body["descricao"] is None
        assert body["ativo"] is True

    finally:
        cleanup(db, records)
        db.close()


def test_patch_empty_category_payload_is_rejected():
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

        response = client.patch(
            f"/api/v1/custom/categorias/{categoria.id}",
            json={},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 422

    finally:
        cleanup(db, records)
        db.close()


def test_duplicate_category_name_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        headers = auth_headers(user, company)

        primeira = client.post(
            "/api/v1/custom/categorias",
            json={"nome": "Ferramentas"},
            headers=headers,
        )

        assert primeira.status_code == 201

        segunda = client.post(
            "/api/v1/custom/categorias",
            json={"nome": "Ferramentas"},
            headers=headers,
        )

        assert segunda.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_updating_category_to_existing_name_returns_conflict():
    db = SessionLocal()
    records = []

    try:
        user, company, membership = create_user_company_membership(db)
        records.append((user, company, membership))
        headers = auth_headers(user, company)

        primeira = client.post(
            "/api/v1/custom/categorias",
            json={"nome": "Ferramentas"},
            headers=headers,
        )
        segunda = client.post(
            "/api/v1/custom/categorias",
            json={"nome": "Materiais"},
            headers=headers,
        )

        assert primeira.status_code == 201
        assert segunda.status_code == 201

        response = client.patch(
            f"/api/v1/custom/categorias/{primeira.json()['id']}",
            json={"nome": "Materiais"},
            headers=headers,
        )

        assert response.status_code == 409

    finally:
        cleanup(db, records)
        db.close()


def test_viewer_cannot_update_category():
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

        response = client.patch(
            f"/api/v1/custom/categorias/{categoria.id}",
            json={"ativo": False},
            headers=auth_headers(user, company),
        )

        assert response.status_code == 403

    finally:
        cleanup(db, records)
        db.close()


def test_cannot_update_category_from_another_company():
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

        categoria = Categoria(
            empresa_id=company_b.id,
            nome="Privada",
            descricao="Descrição privada",
            ativo=True,
        )

        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        response = client.patch(
            f"/api/v1/custom/categorias/{categoria.id}",
            json={"nome": "Alterada indevidamente"},
            headers=auth_headers(user_a, company_a),
        )

        assert response.status_code == 404

        db.refresh(categoria)
        assert categoria.nome == "Privada"
        assert categoria.descricao == "Descrição privada"

    finally:
        cleanup(db, records)
        db.close()
