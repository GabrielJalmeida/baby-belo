
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.inventory_schemas import (
    InventarioContagemUpdate,
    InventarioCreate,
    InventarioDetalheResponse,
    InventarioItemResponse,
    InventarioResponse,
)
from app.core.inventory_service import (
    InventarioAbertoExistenteError,
    InventarioContagemIncompletaError,
    InventarioNaoAbertoError,
    InventarioSemItensError,
    InventarioService,
    ItemBloqueadoPorInventarioAbertoError,
    ItemForaDoInventarioError,
    QuantidadeContadaFracionariaError,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import (
    get_current_company_membership,
)
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/inventarios",
    tags=["inventários"],
)


def _handle_write_error(
    db: Session,
    exc: Exception,
) -> None:
    db.rollback()

    if isinstance(exc, InventarioAbertoExistenteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, InventarioNaoAbertoError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, InventarioContagemIncompletaError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ItemBloqueadoPorInventarioAbertoError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ItemForaDoInventarioError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, InventarioSemItensError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, QuantidadeContadaFracionariaError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, DBAPIError):
        original = exc.orig
        sqlstate = (
            getattr(original, "sqlstate", None)
            or getattr(original, "pgcode", None)
        )

        if sqlstate == "P0001":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "O inventário ou seu histórico não pode "
                    "ser alterado neste estado."
                ),
            ) from exc

        if sqlstate == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflito com um registro já existente.",
            ) from exc

        if sqlstate in {"23503", "23514"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A operação viola uma regra de integridade.",
            ) from exc

    raise exc


def _build_inventory_detail(
    db: Session,
    empresa_id: int,
    inventory,
) -> InventarioDetalheResponse:
    items = InventarioService.list_inventory_items(
        db=db,
        empresa_id=empresa_id,
        inventario_id=inventory.id,
    )

    inventory_data = InventarioResponse.model_validate(
        inventory
    ).model_dump()

    return InventarioDetalheResponse(
        **inventory_data,
        itens=items,
    )


@router.post(
    "",
    response_model=InventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    data: InventarioCreate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> InventarioResponse:
    try:
        inventory = InventarioService.create_inventory(
            db=db,
            empresa_id=membership.empresa_id,
            observacao=data.observacao,
        )

        db.commit()
        db.refresh(inventory)

        return inventory

    except (ValueError, DBAPIError) as exc:
        _handle_write_error(db, exc)


@router.get(
    "",
    response_model=list[InventarioResponse],
)
def list_inventories(
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[InventarioResponse]:
    return InventarioService.list_inventories(
        db=db,
        empresa_id=membership.empresa_id,
    )


@router.get(
    "/{inventario_id}",
    response_model=InventarioDetalheResponse,
)
def get_inventory(
    inventario_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> InventarioDetalheResponse:
    inventory = InventarioService.get_inventory(
        db=db,
        empresa_id=membership.empresa_id,
        inventario_id=inventario_id,
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventário não encontrado.",
        )

    return _build_inventory_detail(
        db=db,
        empresa_id=membership.empresa_id,
        inventory=inventory,
    )


@router.get(
    "/{inventario_id}/itens",
    response_model=list[InventarioItemResponse],
)
def list_inventory_items(
    inventario_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[InventarioItemResponse]:
    inventory = InventarioService.get_inventory(
        db=db,
        empresa_id=membership.empresa_id,
        inventario_id=inventario_id,
    )

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventário não encontrado.",
        )

    return InventarioService.list_inventory_items(
        db=db,
        empresa_id=membership.empresa_id,
        inventario_id=inventario_id,
    )


@router.put(
    "/{inventario_id}/itens/{item_id}/contagem",
    response_model=InventarioItemResponse,
)
def record_inventory_count(
    inventario_id: int,
    item_id: int,
    data: InventarioContagemUpdate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> InventarioItemResponse:
    try:
        inventory_item = InventarioService.record_count(
            db=db,
            empresa_id=membership.empresa_id,
            inventario_id=inventario_id,
            item_id=item_id,
            quantidade_contada=data.quantidade_contada,
        )

        if inventory_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventário não encontrado.",
            )

        db.commit()
        db.refresh(inventory_item)

        return inventory_item

    except HTTPException:
        raise

    except (ValueError, DBAPIError) as exc:
        _handle_write_error(db, exc)


@router.post(
    "/{inventario_id}/concluir",
    response_model=InventarioResponse,
)
def complete_inventory(
    inventario_id: int,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> InventarioResponse:
    try:
        inventory = InventarioService.complete_inventory(
            db=db,
            empresa_id=membership.empresa_id,
            inventario_id=inventario_id,
        )

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventário não encontrado.",
            )

        db.commit()
        db.refresh(inventory)

        return inventory

    except HTTPException:
        raise

    except (ValueError, DBAPIError) as exc:
        _handle_write_error(db, exc)


@router.post(
    "/{inventario_id}/cancelar",
    response_model=InventarioResponse,
)
def cancel_inventory(
    inventario_id: int,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> InventarioResponse:
    try:
        inventory = InventarioService.cancel_inventory(
            db=db,
            empresa_id=membership.empresa_id,
            inventario_id=inventario_id,
        )

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventário não encontrado.",
            )

        db.commit()
        db.refresh(inventory)

        return inventory

    except HTTPException:
        raise

    except (ValueError, DBAPIError) as exc:
        _handle_write_error(db, exc)