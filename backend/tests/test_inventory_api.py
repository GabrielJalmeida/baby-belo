from sqlalchemy import event
from app.core.movement_models import Movimentacao
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


def seed_context(db, role="OWNER", item_count=1):
    user = AuthService.create_user(
        db=db,
        nome=f"Usuário {uuid4().hex}",
        email=f"inventory-{uuid4().hex}@example.com",
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
        permite_decimal=True,
        ativo=True,
    )

    db.add_all([membership, unit])
    db.flush()

    items = []

    for index in range(item_count):
        item = Item(
            empresa_id=company.id,
            unidade_id=unit.id,
            nome=f"Item de teste {index + 1}",
            estoque_minimo=0,
            ativo=True,
        )
        db.add(item)
        items.append(item)

    db.flush()

    token = create_access_token(subject=str(user.id))

    return {
        "user_id": user.id,
        "company_id": company.id,
        "unit_id": unit.id,
        "item_ids": [item.id for item in items],
        "headers": {
            "Authorization": f"Bearer {token}",
            "X-Company-ID": str(company.id),
        },
    }


@contextmanager
def api_context(role="OWNER", item_count=1):
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

    setup_db = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        context = seed_context(
            db=setup_db,
            role=role,
            item_count=item_count,
        )

        setup_db.commit()
        setup_db.close()

        context["connection"] = connection

        yield context

    finally:
        setup_db.close()

        if had_previous_override:
            app.dependency_overrides[get_db] = previous_override
        else:
            app.dependency_overrides.pop(get_db, None)

        if transaction.is_active:
            transaction.rollback()

        connection.close()


def seed_another_context(connection, role="OWNER", item_count=1):
    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as db:
        context = seed_context(
            db=db,
            role=role,
            item_count=item_count,
        )
        db.commit()

    context["connection"] = connection
    return context


def test_create_inventory_requires_authentication():
    response = client.post(
        "/api/v1/inventarios",
        json={},
    )

    assert response.status_code == 401


def test_owner_can_open_inventory_and_read_snapshot():
    with api_context() as context:
        response = client.post(
            "/api/v1/inventarios",
            json={"observacao": "Contagem inicial"},
            headers=context["headers"],
        )

        assert response.status_code == 201

        body = response.json()
        assert body["empresa_id"] == context["company_id"]
        assert body["status"] == "ABERTO"
        assert body["observacao"] == "Contagem inicial"
        assert body["concluido_em"] is None
        assert body["cancelado_em"] is None

        inventory_id = body["id"]

        detail_response = client.get(
            f"/api/v1/inventarios/{inventory_id}",
            headers=context["headers"],
        )

        assert detail_response.status_code == 200

        detail = detail_response.json()
        assert detail["status"] == "ABERTO"
        assert len(detail["itens"]) == 1
        assert detail["itens"][0]["item_id"] == context["item_ids"][0]
        assert detail["itens"][0]["saldo_sistema"] in (
            "0.0000",
            "0",
        )
        assert detail["itens"][0]["quantidade_contada"] is None
        assert detail["itens"][0]["diferenca"] is None


def test_viewer_cannot_open_inventory():
    with api_context(role="VIEWER") as context:
        response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert response.status_code == 403


def test_company_cannot_open_second_inventory():
    with api_context() as context:
        first = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert first.status_code == 201

        second = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert second.status_code == 409


def test_count_and_completion_generate_stock_adjustment():
    with api_context() as context:
        open_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert open_response.status_code == 201
        inventory_id = open_response.json()["id"]
        item_id = context["item_ids"][0]

        count_response = client.put(
            f"/api/v1/inventarios/{inventory_id}/itens/{item_id}/contagem",
            json={"quantidade_contada": "3.0000"},
            headers=context["headers"],
        )

        assert count_response.status_code == 200
        assert count_response.json()["quantidade_contada"] == "3.0000"
        assert count_response.json()["diferenca"] == "3.0000"

        complete_response = client.post(
            f"/api/v1/inventarios/{inventory_id}/concluir",
            headers=context["headers"],
        )

        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "CONCLUIDO"
        assert complete_response.json()["concluido_em"] is not None
        assert complete_response.json()["cancelado_em"] is None

        balance_response = client.get(
            f"/api/v1/itens/{item_id}/saldo",
            headers=context["headers"],
        )

        assert balance_response.status_code == 200
        assert balance_response.json()["saldo_atual"] == "3.0000"

        movement_response = client.get(
            f"/api/v1/itens/{item_id}/movimentacoes",
            headers=context["headers"],
        )

        assert movement_response.status_code == 200

        movements = movement_response.json()
        assert len(movements) == 1
        assert movements[0]["tipo"] == "AJUSTE_ENTRADA"
        assert movements[0]["quantidade"] == "3.0000"


def test_inventory_cannot_be_completed_before_all_counts():
    with api_context(item_count=2) as context:
        open_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert open_response.status_code == 201
        inventory_id = open_response.json()["id"]

        response = client.post(
            f"/api/v1/inventarios/{inventory_id}/concluir",
            headers=context["headers"],
        )

        assert response.status_code == 409

        detail_response = client.get(
            f"/api/v1/inventarios/{inventory_id}",
            headers=context["headers"],
        )

        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "ABERTO"


def test_cancelled_inventory_rejects_count():
    with api_context() as context:
        open_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert open_response.status_code == 201
        inventory_id = open_response.json()["id"]
        item_id = context["item_ids"][0]

        cancel_response = client.post(
            f"/api/v1/inventarios/{inventory_id}/cancelar",
            headers=context["headers"],
        )

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "CANCELADO"
        assert cancel_response.json()["cancelado_em"] is not None

        count_response = client.put(
            f"/api/v1/inventarios/{inventory_id}/itens/{item_id}/contagem",
            json={"quantidade_contada": "1.0000"},
            headers=context["headers"],
        )

        assert count_response.status_code == 409


def test_inventory_is_not_visible_to_another_company():
    with api_context() as context:
        own_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert own_response.status_code == 201
        inventory_id = own_response.json()["id"]

        other_context = seed_another_context(
            context["connection"],
        )

        detail_response = client.get(
            f"/api/v1/inventarios/{inventory_id}",
            headers=other_context["headers"],
        )

        assert detail_response.status_code == 404


def test_open_inventory_blocks_normal_stock_movement():
    with api_context() as context:
        open_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert open_response.status_code == 201

        movement_response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_ids"][0],
                "tipo": "ENTRADA",
                "quantidade": "1.0000",
            },
            headers=context["headers"],
        )

        assert movement_response.status_code == 409


def test_viewer_cannot_modify_inventory():
    with api_context(role="VIEWER") as context:
        headers = context["headers"]

        requests = [
            (
                "PUT",
                "/api/v1/inventarios/999999/itens/999999/contagem",
                {"quantidade_contada": "1.0000"},
            ),
            (
                "POST",
                "/api/v1/inventarios/999999/concluir",
                None,
            ),
            (
                "POST",
                "/api/v1/inventarios/999999/cancelar",
                None,
            ),
        ]

        for method, path, payload in requests:
            if payload is None:
                response = client.request(
                    method,
                    path,
                    headers=headers,
                )
            else:
                response = client.request(
                    method,
                    path,
                    json=payload,
                    headers=headers,
                )

            assert response.status_code == 403, (
                f"{method} {path}: "
                f"esperado 403, recebido {response.status_code}"
            )

def test_cannot_disable_decimal_unit_with_fractional_stock():
    with api_context() as context:
        movement_response = client.post(
            "/api/v1/movimentacoes",
            json={
                "item_id": context["item_ids"][0],
                "tipo": "ENTRADA",
                "quantidade": "1.5000",
            },
            headers=context["headers"],
        )

        assert movement_response.status_code == 201

        update_response = client.patch(
            f"/api/v1/unidades/{context['unit_id']}",
            json={"permite_decimal": False},
            headers=context["headers"],
        )

        assert update_response.status_code == 409

        unit_response = client.get(
            f"/api/v1/unidades/{context['unit_id']}",
            headers=context["headers"],
        )

        assert unit_response.status_code == 200
        assert unit_response.json()["permite_decimal"] is True

def test_cannot_disable_decimal_unit_while_inventory_is_open():
    with api_context() as context:
        inventory_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )

        assert inventory_response.status_code == 201

        update_response = client.patch(
            f"/api/v1/unidades/{context['unit_id']}",
            json={"permite_decimal": False},
            headers=context["headers"],
        )

        assert update_response.status_code == 409

        unit_response = client.get(
            f"/api/v1/unidades/{context['unit_id']}",
            headers=context["headers"],
        )

        assert unit_response.status_code == 200
        assert unit_response.json()["permite_decimal"] is True

def test_cannot_disable_decimal_unit_with_fractional_stock_minimum():
    with api_context() as context:
        item_id = context["item_ids"][0]
        unit_id = context["unit_id"]
        headers = context["headers"]

        item_response = client.patch(
            f"/api/v1/itens/{item_id}",
            json={"estoque_minimo": "1.5000"},
            headers=headers,
        )

        assert item_response.status_code == 200
        assert item_response.json()["estoque_minimo"] == "1.5000"

        update_response = client.patch(
            f"/api/v1/unidades/{unit_id}",
            json={"permite_decimal": False},
            headers=headers,
        )

        assert update_response.status_code == 409

        unit_response = client.get(
            f"/api/v1/unidades/{unit_id}",
            headers=headers,
        )

        assert unit_response.status_code == 200
        assert unit_response.json()["permite_decimal"] is True

def test_failed_inventory_adjustments_are_rolled_back_atomically():
    with api_context(item_count=2) as context:
        headers = context["headers"]
        item_ids = context["item_ids"]

        open_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=headers,
        )

        assert open_response.status_code == 201
        inventory_id = open_response.json()["id"]

        # Registra contagens que exigem dois ajustes de entrada.
        for item_id, counted in zip(item_ids, ("3.0000", "4.0000")):
            response = client.put(
                f"/api/v1/inventarios/{inventory_id}"
                f"/itens/{item_id}/contagem",
                json={"quantidade_contada": counted},
                headers=headers,
            )

            assert response.status_code == 200

        # Simula uma falha de integridade durante o INSERT dos ajustes.
        # A restrição real do banco deve rejeitar o tipo inválido.
        def invalidate_inventory_adjustment(mapper, connection, target):
            if (
                target.motivo
                and target.motivo.startswith("Ajuste de inventário #")
            ):
                target.tipo = "TIPO_INVALIDO"

        event.listen(
            Movimentacao,
            "before_insert",
            invalidate_inventory_adjustment,
        )

        try:
            completion_response = client.post(
                f"/api/v1/inventarios/{inventory_id}/concluir",
                headers=headers,
            )
        finally:
            event.remove(
                Movimentacao,
                "before_insert",
                invalidate_inventory_adjustment,
            )

        assert completion_response.status_code == 422

        # A falha deve deixar o inventário aberto.
        detail_response = client.get(
            f"/api/v1/inventarios/{inventory_id}",
            headers=headers,
        )

        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["status"] == "ABERTO"
        assert detail["concluido_em"] is None
        assert detail["cancelado_em"] is None

        # Nenhum ajuste pode permanecer gravado parcialmente.
        for item_id in item_ids:
            history_response = client.get(
                f"/api/v1/itens/{item_id}/movimentacoes",
                headers=headers,
            )

            assert history_response.status_code == 200
            assert history_response.json() == []

            balance_response = client.get(
                f"/api/v1/itens/{item_id}/saldo",
                headers=headers,
            )

            assert balance_response.status_code == 200
            assert balance_response.json()["saldo_atual"] == "0.0000"

def test_inventory_list_supports_pagination_and_limit_maximum():
    with api_context() as context:
        # Finaliza cada inventário para permitir abrir o próximo.
        for _ in range(3):
            create_response = client.post(
                "/api/v1/inventarios",
                json={},
                headers=context["headers"],
            )
            assert create_response.status_code == 201

            inventory_id = create_response.json()["id"]

            cancel_response = client.post(
                f"/api/v1/inventarios/{inventory_id}/cancelar",
                headers=context["headers"],
            )
            assert cancel_response.status_code == 200

        all_response = client.get(
            "/api/v1/inventarios",
            headers=context["headers"],
        )
        assert all_response.status_code == 200

        all_inventories = all_response.json()
        assert len(all_inventories) == 3

        page_response = client.get(
            "/api/v1/inventarios?limit=1&offset=1",
            headers=context["headers"],
        )
        assert page_response.status_code == 200
        assert page_response.json() == all_inventories[1:2]

        invalid_limit_response = client.get(
            "/api/v1/inventarios?limit=101",
            headers=context["headers"],
        )
        assert invalid_limit_response.status_code == 422


def test_inventory_item_list_supports_pagination_without_truncating_detail():
    with api_context(item_count=101) as context:
        create_response = client.post(
            "/api/v1/inventarios",
            json={},
            headers=context["headers"],
        )
        assert create_response.status_code == 201

        inventory_id = create_response.json()["id"]

        all_items_response = client.get(
            f"/api/v1/inventarios/{inventory_id}/itens",
            headers=context["headers"],
        )
        assert all_items_response.status_code == 200

        all_items = all_items_response.json()
        assert len(all_items) == 50

        page_response = client.get(
            f"/api/v1/inventarios/{inventory_id}/itens?limit=1&offset=1",
            headers=context["headers"],
        )
        assert page_response.status_code == 200
        assert page_response.json() == all_items[1:2]

        invalid_limit_response = client.get(
            f"/api/v1/inventarios/{inventory_id}/itens?limit=101",
            headers=context["headers"],
        )
        assert invalid_limit_response.status_code == 422

        # O endpoint de detalhe deve continuar retornando o snapshot completo.
        detail_response = client.get(
            f"/api/v1/inventarios/{inventory_id}",
            headers=context["headers"],
        )
        assert detail_response.status_code == 200
        assert len(detail_response.json()["itens"]) == 101
