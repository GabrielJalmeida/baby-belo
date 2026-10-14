import pytest

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade
from app.main import app
from app.shared.database import SessionLocal
from app.shared.security import create_access_token


client = TestClient(app)


def create_context(db, role="OWNER", permite_decimal=True):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"item-{uuid4().hex}@example.com",
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

    unit = Unidade(
        empresa_id=company.id,
        nome=f"Unidade {uuid4().hex[:12]}",
        simbolo="UN",
        permite_decimal=permite_decimal,
        ativo=True,
    )

    db.add_all([membership, unit])
    db.commit()

    token = create_access_token(subject=str(user.id))

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company.id),
    }

    return user, company, membership, unit, headers


def cleanup_context(db, user, company, membership):
    db.query(Item).filter(
        Item.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.query(Unidade).filter(
        Unidade.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.delete(membership)
    db.delete(company)
    db.delete(user)
    db.commit()


def test_create_item_requires_authentication():
    response = client.post(
        "/api/v1/itens",
        json={
            "unidade_id": 1,
            "nome": "Papel A4",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_item():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(db)

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": "Papel A4",
                "descricao": "Resma de papel",
                "estoque_minimo": "2.5000",
            },
            headers=headers,
        )

        assert response.status_code == 201

        body = response.json()

        assert body["empresa_id"] == company.id
        assert body["unidade_id"] == unit.id
        assert body["nome"] == "Papel A4"
        assert body["descricao"] == "Resma de papel"
        assert Decimal(str(body["estoque_minimo"])) == Decimal("2.5000")
        assert body["ativo"] is True

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_create_item():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            role="VIEWER",
        )

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": "Papel A4",
            },
            headers=headers,
        )

        assert response.status_code == 403

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_list_items_returns_only_active_items_from_current_company():
    db = SessionLocal()
    first_context = None
    second_context = None

    try:
        first_context = create_context(db)
        second_context = create_context(db)

        user_a, company_a, membership_a, unit_a, headers_a = first_context
        _, company_b, _, unit_b, _ = second_context

        active_item = Item(
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item ativo",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        inactive_item = Item(
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item inativo",
            estoque_minimo=Decimal("0"),
            ativo=False,
        )

        other_item = Item(
            empresa_id=company_b.id,
            unidade_id=unit_b.id,
            nome="Item de outra empresa",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add_all([active_item, inactive_item, other_item])
        db.commit()

        response = client.get(
            "/api/v1/itens",
            headers=headers_a,
        )

        assert response.status_code == 200

        names = {item["nome"] for item in response.json()}

        assert "Item ativo" in names
        assert "Item inativo" not in names
        assert "Item de outra empresa" not in names

        all_response = client.get(
            "/api/v1/itens?include_inactive=true",
            headers=headers_a,
        )
        assert all_response.status_code == 200
        all_names = {item["nome"] for item in all_response.json()}
        assert "Item ativo" in all_names
        assert "Item inativo" in all_names
        assert "Item de outra empresa" not in all_names

        cleanup_context(db, *first_context[:3])
        cleanup_context(db, *second_context[:3])

    finally:
        db.close()


def test_operator_can_update_item_partially():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            role="OPERATOR",
        )

        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel A4",
            descricao="Descrição antiga",
            estoque_minimo=Decimal("2.0000"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"descricao": None},
            headers=headers,
        )

        assert response.status_code == 200

        body = response.json()

        assert body["nome"] == "Papel A4"
        assert body["descricao"] is None
        assert Decimal(str(body["estoque_minimo"])) == Decimal("2.0000")

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_viewer_cannot_update_item():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            role="VIEWER",
        )

        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel A4",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"nome": "Nome não permitido"},
            headers=headers,
        )

        assert response.status_code == 403

        cleanup_context(db, user, company, membership)

    finally:
        db.close()


def test_cannot_access_item_from_another_company():
    db = SessionLocal()
    first_context = None
    second_context = None

    try:
        first_context = create_context(db)
        second_context = create_context(db)

        _, company_a, _, _, headers_a = first_context
        _, company_b, _, unit_b, _ = second_context

        item = Item(
            empresa_id=company_b.id,
            unidade_id=unit_b.id,
            nome="Item privado",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.get(
            f"/api/v1/itens/{item.id}",
            headers=headers_a,
        )

        assert response.status_code == 404

        cleanup_context(db, *first_context[:3])
        cleanup_context(db, *second_context[:3])

    finally:
        db.close()


def test_create_item_rejects_fractional_minimum_for_integer_unit():
    db = SessionLocal()

    try:
        user, company, membership, unit, headers = create_context(
            db,
            permite_decimal=False,
        )

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": "Caixas",
                "estoque_minimo": "1.5000",
            },
            headers=headers,
        )

        assert response.status_code == 422

        cleanup_context(db, user, company, membership)

    finally:
        db.close()

def test_list_items_supports_limit_and_offset():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        _, company, _, unit, headers = context

        items = [
            Item(
                empresa_id=company.id,
                unidade_id=unit.id,
                nome=f"Item página {index}",
                estoque_minimo=Decimal("0"),
                ativo=True,
            )
            for index in range(1, 6)
        ]

        db.add_all(items)
        db.commit()

        expected_ids = [
            item.id for item in items[1:3]
        ]

        response = client.get(
            "/api/v1/itens?limit=2&offset=1",
            headers=headers,
        )

        assert response.status_code == 200
        assert [
            item["id"] for item in response.json()
        ] == expected_ids

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()


def test_list_items_rejects_invalid_pagination_parameters():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        headers = context[4]

        invalid_queries = [
            "limit=0",
            "limit=101",
            "offset=-1",
        ]

        for query in invalid_queries:
            response = client.get(
                f"/api/v1/itens?{query}",
                headers=headers,
            )

            assert response.status_code == 422, query

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()


def test_cannot_update_item_from_another_company():
    db = SessionLocal()
    first_context = None
    second_context = None

    try:
        first_context = create_context(db)
        second_context = create_context(db)

        _, company_b, _, unit_b, _ = second_context
        headers_a = first_context[4]

        item = Item(
            empresa_id=company_b.id,
            unidade_id=unit_b.id,
            nome="Item privado",
            descricao="Descrição privada",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )

        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"nome": "Alterado indevidamente"},
            headers=headers_a,
        )

        assert response.status_code == 404

        db.refresh(item)
        assert item.nome == "Item privado"
        assert item.descricao == "Descrição privada"

    finally:
        if first_context is not None:
            cleanup_context(db, *first_context[:3])

        if second_context is not None:
            cleanup_context(db, *second_context[:3])

        db.close()


def test_patch_item_with_empty_payload_keeps_values_unchanged():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        _, _, _, unit, headers = context

        item = Item(
            empresa_id=context[1].id,
            unidade_id=unit.id,
            nome="Papel A4",
            descricao="Descrição original",
            estoque_minimo=Decimal("3.0000"),
            ativo=True,
        )
        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={},
            headers=headers,
        )

        assert response.status_code == 200, response.text

        body = response.json()
        assert body["nome"] == "Papel A4"
        assert body["descricao"] == "Descrição original"
        assert Decimal(str(body["estoque_minimo"])) == Decimal("3.0000")
        assert body["unidade_id"] == unit.id
        assert body["ativo"] is True

        db.refresh(item)
        assert item.nome == "Papel A4"
        assert item.descricao == "Descrição original"

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()


def test_patch_item_rejects_null_name_without_changing_item():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        _, company, _, unit, headers = context

        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel A4",
            descricao="Descrição original",
            estoque_minimo=Decimal("3.0000"),
            ativo=True,
        )
        db.add(item)
        db.commit()

        response = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"nome": None},
            headers=headers,
        )

        assert response.status_code == 422, response.text

        db.refresh(item)
        assert item.nome == "Papel A4"
        assert item.descricao == "Descrição original"

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()


def test_item_routes_reject_non_positive_path_ids():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        headers = context[4]

        for item_id in (0, -1):
            get_response = client.get(
                f"/api/v1/itens/{item_id}",
                headers=headers,
            )

            assert get_response.status_code == 422, (
                f"GET item ID {item_id}: "
                f"recebeu {get_response.status_code}: "
                f"{get_response.text}"
            )

            patch_response = client.patch(
                f"/api/v1/itens/{item_id}",
                json={"nome": "Item atualizado"},
                headers=headers,
            )

            assert patch_response.status_code == 422, (
                f"PATCH item ID {item_id}: "
                f"recebeu {patch_response.status_code}: "
                f"{patch_response.text}"
            )

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()


@pytest.mark.parametrize(
    ("comprimento", "status_esperado"),
    [
        (2_000, 201),
        (2_001, 422),
    ],
)
def test_create_item_enforces_description_length(
    comprimento,
    status_esperado,
):
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        _, _, _, unit, headers = context

        response = client.post(
            "/api/v1/itens",
            json={
                "unidade_id": unit.id,
                "nome": f"Item {uuid4().hex}",
                "descricao": "D" * comprimento,
            },
            headers=headers,
        )

        assert response.status_code == status_esperado, response.text

        if status_esperado == 201:
            assert len(response.json()["descricao"]) == 2_000

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()


def test_patch_item_rejects_oversized_description_without_changing_value():
    db = SessionLocal()
    context = None

    try:
        context = create_context(db)
        _, _, _, unit, headers = context

        item = Item(
            empresa_id=context[1].id,
            unidade_id=unit.id,
            nome=f"Item {uuid4().hex}",
            descricao="Descrição inicial",
            estoque_minimo=Decimal("0"),
            ativo=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        accepted = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"descricao": "D" * 2_000},
            headers=headers,
        )
        assert accepted.status_code == 200, accepted.text

        rejected = client.patch(
            f"/api/v1/itens/{item.id}",
            json={"descricao": "D" * 2_001},
            headers=headers,
        )
        assert rejected.status_code == 422, rejected.text

        persisted = client.get(
            f"/api/v1/itens/{item.id}",
            headers=headers,
        )
        assert persisted.status_code == 200, persisted.text
        assert len(persisted.json()["descricao"]) == 2_000

    finally:
        if context is not None:
            cleanup_context(db, *context[:3])
        db.close()
