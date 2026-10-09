from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.custom.item_categoria_service import (
    ItemCategoriaCategoriaNaoEncontradaError,
    ItemCategoriaComValoresError,
    ItemCategoriaItemNaoEncontradoError,
    ItemCategoriaService,
)
from app.custom.schemas import ItemCategoriaCreate, ItemCategoriaRead
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/custom",
    tags=["custom-item-categorias"],
)


@router.get(
    "/itens/{item_id}/categoria",
    response_model=ItemCategoriaRead,
)
def get_item_category(
    item_id: int = Path(gt=0),
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> ItemCategoriaRead:
    try:
        associacao = ItemCategoriaService.get_item_category(
            db=db,
            empresa_id=membership.empresa_id,
            item_id=item_id,
        )

        if associacao is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O item ainda não possui uma categoria associada.",
            )

        return associacao

    except ItemCategoriaItemNaoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.put(
    "/itens/{item_id}/categoria",
    response_model=ItemCategoriaRead,
)
def assign_category(
    item_id: int,
    data: ItemCategoriaCreate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> ItemCategoriaRead:
    try:
        associacao = ItemCategoriaService.assign_category(
            db=db,
            empresa_id=membership.empresa_id,
            item_id=item_id,
            categoria_id=data.categoria_id,
        )

        db.commit()
        db.refresh(associacao)

        return associacao

    except (
        ItemCategoriaItemNaoEncontradoError,
        ItemCategoriaCategoriaNaoEncontradaError,
    ) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ItemCategoriaComValoresError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível alterar a categoria do item.",
        ) from error