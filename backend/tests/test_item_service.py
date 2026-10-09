
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.item_models import Item
from app.core.item_service import (
    EstoqueMinimoFracionarioError,
    ItemService,
    NomeItemDuplicadoError,
    UnidadeItemInvalidaError,
)
from app.core.models import Empresa
from app.core.unit_models import Unidade
from app.shared.database import SessionLocal


def create_company_and_unit(db, permite_decimal=True):
    company = Empresa(
        nome=f"Empresa {uuid4().hex}",
        ativo=True,
    )

    db.add(company)
    db.flush()

    unit = Unidade(
        empresa_id=company.id,
        nome=f"Unidade {uuid4().hex[:12]}",
        simbolo="UN",
        permite_decimal=permite_decimal,
        ativo=True,
    )

    db.add(unit)
    db.commit()

    return company, unit


def cleanup_company(db, company):
    db.query(Item).filter(
        Item.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.query(Unidade).filter(
        Unidade.empresa_id == company.id
    ).delete(synchronize_session=False)

    db.delete(company)
    db.commit()


def test_create_item_normalizes_and_persists_values():
    db = SessionLocal()
    company = None

    try:
        company, unit = create_company_and_unit(db)

        item = ItemService.create_item(
            db=db,
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="  Papel A4  ",
            descricao="  Resma de papel  ",
            estoque_minimo=Decimal("2.5000"),
        )

        db.commit()
        db.refresh(item)

        assert item.empresa_id == company.id
        assert item.unidade_id == unit.id
        assert item.nome == "Papel A4"
        assert item.descricao == "Resma de papel"
        assert item.estoque_minimo == Decimal("2.5000")
        assert item.ativo is True

    finally:
        if company is not None:
            cleanup_company(db, company)
        db.close()


def test_create_item_rejects_unit_from_another_company():
    db = SessionLocal()
    company_a = None
    company_b = None

    try:
        company_a, _ = create_company_and_unit(db)
        company_b, unit_b = create_company_and_unit(db)

        with pytest.raises(UnidadeItemInvalidaError):
            ItemService.create_item(
                db=db,
                empresa_id=company_a.id,
                unidade_id=unit_b.id,
                nome="Item indevido",
                descricao=None,
                estoque_minimo=Decimal("0"),
            )

    finally:
        if company_a is not None:
            cleanup_company(db, company_a)
        if company_b is not None:
            cleanup_company(db, company_b)
        db.close()


def test_create_item_rejects_fractional_minimum_for_integer_unit():
    db = SessionLocal()
    company = None

    try:
        company, unit = create_company_and_unit(
            db,
            permite_decimal=False,
        )

        with pytest.raises(EstoqueMinimoFracionarioError):
            ItemService.create_item(
                db=db,
                empresa_id=company.id,
                unidade_id=unit.id,
                nome="Caixas",
                descricao=None,
                estoque_minimo=Decimal("1.5000"),
            )

    finally:
        if company is not None:
            cleanup_company(db, company)
        db.close()


def test_create_item_rejects_duplicate_name_in_same_company():
    db = SessionLocal()
    company = None

    try:
        company, unit = create_company_and_unit(db)

        ItemService.create_item(
            db=db,
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel",
            descricao=None,
            estoque_minimo=Decimal("0"),
        )
        db.commit()

        with pytest.raises(NomeItemDuplicadoError):
            ItemService.create_item(
                db=db,
                empresa_id=company.id,
                unidade_id=unit.id,
                nome="Papel",
                descricao=None,
                estoque_minimo=Decimal("0"),
            )

    finally:
        if company is not None:
            db.rollback()
            cleanup_company(db, company)
        db.close()


def test_list_items_only_returns_active_items_for_company():
    db = SessionLocal()
    company_a = None
    company_b = None

    try:
        company_a, unit_a = create_company_and_unit(db)
        company_b, unit_b = create_company_and_unit(db)

        item_a = ItemService.create_item(
            db=db,
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item A",
            descricao=None,
            estoque_minimo=Decimal("0"),
        )

        item_inactive = ItemService.create_item(
            db=db,
            empresa_id=company_a.id,
            unidade_id=unit_a.id,
            nome="Item inativo",
            descricao=None,
            estoque_minimo=Decimal("0"),
        )
        item_inactive.ativo = False

        ItemService.create_item(
            db=db,
            empresa_id=company_b.id,
            unidade_id=unit_b.id,
            nome="Item B",
            descricao=None,
            estoque_minimo=Decimal("0"),
        )

        db.commit()

        result = ItemService.list_items(
            db=db,
            empresa_id=company_a.id,
        )

        assert [item.id for item in result] == [item_a.id]
        assert item_inactive.id not in [item.id for item in result]

    finally:
        if company_a is not None:
            cleanup_company(db, company_a)
        if company_b is not None:
            cleanup_company(db, company_b)
        db.close()


def test_update_item_changes_only_submitted_fields():
    db = SessionLocal()
    company = None

    try:
        company, unit = create_company_and_unit(db)

        item = ItemService.create_item(
            db=db,
            empresa_id=company.id,
            unidade_id=unit.id,
            nome="Papel A4",
            descricao="Resma",
            estoque_minimo=Decimal("2.0000"),
        )
        db.commit()

        updated = ItemService.update_item(
            db=db,
            empresa_id=company.id,
            item_id=item.id,
            changes={"descricao": None},
        )

        assert updated is not None
        assert updated.nome == "Papel A4"
        assert updated.descricao is None
        assert updated.estoque_minimo == Decimal("2.0000")

        assert ItemService.get_item(
            db=db,
            empresa_id=company.id + 999999,
            item_id=item.id,
        ) is None

    finally:
        if company is not None:
            cleanup_company(db, company)
        db.close()