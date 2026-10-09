
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.inventory_service import (
    ItemBloqueadoPorInventarioAbertoError,
)

from app.core.item_schemas import (
    ItemCreate,
    ItemResponse,
    ItemUpdate,
)
from app.core.item_service import (
    EstoqueMinimoFracionarioError,
    ItemService,
    NomeItemDuplicadoError,
    UnidadeItemInvalidaError,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import (
    get_current_company_membership,
)
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/itens",
    tags=["itens"],
)


def _database_http_error(exc: DBAPIError) -> HTTPException | None:
    original = exc.orig
    sqlstate = (
        getattr(original, "sqlstate", None)
        or getattr(original, "pgcode", None)
    )

    if sqlstate == "23505":
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um item com esses dados únicos.",
        )

    if sqlstate == "23503":
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A empresa ou unidade informada é inválida.",
        )

    if sqlstate == "23514":
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Os dados violam uma regra de integridade.",
        )

    if sqlstate == "P0001":
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não é permitido alterar a unidade de um item "
                "que já possui movimentações."
            ),
        )

    return None


def _handle_write_error(
    db: Session,
    exc: Exception,
) -> None:
    db.rollback()

    if isinstance(exc, ItemBloqueadoPorInventarioAbertoError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, UnidadeItemInvalidaError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, EstoqueMinimoFracionarioError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, NomeItemDuplicadoError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, DBAPIError):
        http_error = _database_http_error(exc)

        if http_error is not None:
            raise http_error from exc

    raise exc


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    data: ItemCreate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> ItemResponse:
    try:
        item = ItemService.create_item(
            db=db,
            empresa_id=membership.empresa_id,
            unidade_id=data.unidade_id,
            nome=data.nome,
            descricao=data.descricao,
            estoque_minimo=data.estoque_minimo,
        )

        db.commit()
        db.refresh(item)

        return item

    except (
        UnidadeItemInvalidaError,
        EstoqueMinimoFracionarioError,
        NomeItemDuplicadoError,
        ValueError,
        DBAPIError,
    ) as exc:
        _handle_write_error(db, exc)


@router.get(
    "",
    response_model=list[ItemResponse],
)
def list_items(
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[ItemResponse]:
    return ItemService.list_items(
        db=db,
        empresa_id=membership.empresa_id,
    )


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
)
def get_item(
    item_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> ItemResponse:
    item = ItemService.get_item(
        db=db,
        empresa_id=membership.empresa_id,
        item_id=item_id,
    )

    if item is None or not item.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado.",
        )

    return item


@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
)
def update_item(
    item_id: int,
    data: ItemUpdate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> ItemResponse:
    try:
        item = ItemService.update_item(
            db=db,
            empresa_id=membership.empresa_id,
            item_id=item_id,
            changes=data.model_dump(exclude_unset=True),
        )

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )

        db.commit()
        db.refresh(item)

        return item

    except HTTPException:
        raise

    except (
        UnidadeItemInvalidaError,
        EstoqueMinimoFracionarioError,
        NomeItemDuplicadoError,
        ValueError,
        DBAPIError,
    ) as exc:
        _handle_write_error(db, exc)