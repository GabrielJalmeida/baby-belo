
from contextlib import contextmanager
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import EmpresaUsuario
from app.auth.service import AuthService
from app.core.item_models import Item
from app.core.models import Empresa
from app.core.unit_models import Unidade
from app.main import app
from app.shared.database import engine, get_db
from app.shared.security import create_access_token


client = TestClient(app)


@contextmanager
def api_context(role="OWNER", permite_decimal=True, item_ativo=True):
    connection = engine.connect()
    transaction = connection.begin()

    had_previous_override = get_db in app.dependency_overrides
    previous_override = app.dependency_overrides.get(get_db)

    def override_get_db():
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    db = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        user = AuthService.create_user(
            db=db,
            nome=f"Usuário {uuid4().hex}",
            email=f"movement-{uuid4().hex}@example.com",
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
        db.flush()

        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Item de teste",
            estoque_minimo=0,
            ativo=item_ativo,
        )
        db.add(item)

        other_company = Empresa(
            nome=f"Outra empresa {uuid4().hex}",
            ativo=True,
        )
        db.add(other_company)
        db.flush()

        other_unit = Unidade(
            empresa_id=other_company.id,
            nome=f"Unidade {uuid4().hex[:12]}",
            simbolo="UN",
            permite_decimal=True,
            ativo=True,
        )
        db.add(other_unit)
        db.flush()

        other_item = Item(
            empresa_id=other_company.id,
            unidade_id=other_unit.id,
            nome="Item de outra empresa",
            estoque_minimo=0,
            ativo=True,
        )
        db.add(other_item)

        db.commit()

        context = {
            "company_id": company.id,
            "unit_id": unit.id,
            "item_id": item.id,
            "other_item_id": other_item.id,
            "headers": {
                "Authorization": (
                    f"Bearer {create_access_token(subject=str(user.id))}"
                ),
                "X-Company-ID": str(company.id),
            },
        }

        db.close()
        yield context

    finally:
        db.close()

        if had_previous_override:
            app.dependency_overrides[get_db] = previous_override
        else:
            app.dependency_overrides.pop(get_db, None)

        if transaction.is_active:
            transaction.rollback()

        connection.close()


def test_create_movement_requires_authentication():
    response = client.post(
        "/api/v1/movimentacoes",
        json={
            "item_id": 1,
            "tipo": "ENTRADA",
            "quantidade": "1.0000",
        },
    )

    assert response.status_code == 401


def test_owner_can_create_movement_and_consult_balance():
    with api_context() as context:
        response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_id"],
                "tipo": "ENTRADA",
                "quantidade": "10.0000",
                "motivo": "Recebimento",
            },
            headers=context["headers"],
        )

        assert response.status_code == 201

        body = response.json()
        assert body["empresa_id"] == context["company_id"]
        assert body["item_id"] == context["item_id"]
        assert body["tipo"] == "ENTRADA"
        assert body["quantidade"] == "10.0000"

        balance_response = client.get(
            f"/api/v1/itens/{context['item_id']}/saldo",
            headers=context["headers"],
        )

        assert balance_response.status_code == 200
        assert balance_response.json()["saldo_atual"] == "10.0000"

        history_response = client.get(
            f"/api/v1/itens/{context['item_id']}/movimentacoes",
            headers=context["headers"],
        )

        assert history_response.status_code == 200
        assert len(history_response.json()) == 1
        assert history_response.json()[0]["tipo"] == "ENTRADA"


def test_viewer_cannot_create_movement():
    with api_context(role="VIEWER") as context:
        response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_id"],
                "tipo": "ENTRADA",
                "quantidade": "1.0000",
            },
            headers=context["headers"],
        )

        assert response.status_code == 403


def test_exit_without_sufficient_balance_returns_conflict():
    with api_context() as context:
        response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_id"],
                "tipo": "SAIDA",
                "quantidade": "1.0000",
            },
            headers=context["headers"],
        )

        assert response.status_code == 409

        balance_response = client.get(
            f"/api/v1/itens/{context['item_id']}/saldo",
            headers=context["headers"],
        )

        assert balance_response.status_code == 200
        assert balance_response.json()["saldo_atual"] == "0.0000"


def test_fractional_movement_for_integer_unit_returns_422():
    with api_context(permite_decimal=False) as context:
        response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_id"],
                "tipo": "ENTRADA",
                "quantidade": "1.5000",
            },
            headers=context["headers"],
        )

        assert response.status_code == 422


def test_inactive_item_cannot_be_moved():
    with api_context(item_ativo=False) as context:
        response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_id"],
                "tipo": "ENTRADA",
                "quantidade": "1.0000",
            },
            headers=context["headers"],
        )

        assert response.status_code == 409


def test_other_company_item_is_hidden_from_balance_and_history():
    with api_context() as context:
        balance_response = client.get(
            f"/api/v1/itens/{context['other_item_id']}/saldo",
            headers=context["headers"],
        )

        history_response = client.get(
            f"/api/v1/itens/{context['other_item_id']}/movimentacoes",
            headers=context["headers"],
        )

        assert balance_response.status_code == 404
        assert history_response.status_code == 404

        movement_response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["other_item_id"],
                "tipo": "ENTRADA",
                "quantidade": "1.0000",
            },
            headers=context["headers"],
        )

        assert movement_response.status_code == 404

def test_list_item_movements_supports_limit_and_offset():
    with api_context() as context:
        history_url = (
            f"/api/v1/itens/{context['item_id']}/movimentacoes"
        )

        for _ in range(5):
            response = client.post(
                "/api/v1/movimentacoes",
                json={
                    "item_id": context["item_id"],
                    "tipo": "ENTRADA",
                    "quantidade": "1.0000",
                },
                headers=context["headers"],
            )

            assert response.status_code == 201

        full_response = client.get(
            history_url,
            headers=context["headers"],
        )

        assert full_response.status_code == 200

        full_ids = [
            movement["id"]
            for movement in full_response.json()
        ]

        assert len(full_ids) == 5

        page_response = client.get(
            f"{history_url}?limit=2&offset=1",
            headers=context["headers"],
        )

        assert page_response.status_code == 200
        assert [
            movement["id"]
            for movement in page_response.json()
        ] == full_ids[1:3]


def test_list_item_movements_rejects_invalid_pagination():
    with api_context() as context:
        history_url = (
            f"/api/v1/itens/{context['item_id']}/movimentacoes"
        )

        invalid_queries = [
            "limit=0",
            "limit=101",
            "offset=-1",
        ]

        for query in invalid_queries:
            response = client.get(
                f"{history_url}?{query}",
                headers=context["headers"],
            )

            assert response.status_code == 422, query