from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.custom.schemas import (
    ValorItemCreate,
    ValorItemRead,
    ValorItemUpdate,
)
from app.custom.valor_item_service import (
    CampoCategoriaIncompativelError,
    CampoValorNaoEncontradoError,
    ItemSemCategoriaError,
    ItemValorNaoEncontradoError,
    OpcaoValorInvalidaError,
    TipoValorIncompativelError,
    ValorItemDuplicadoError,
    ValorItemService,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/custom",
    tags=["custom-valores"],
)


def _is_unique_violation(error: IntegrityError) -> bool:
    original = error.orig

    sqlstate = (
        getattr(original, "sqlstate", None)
        or getattr(original, "pgcode", None)
    )

    return sqlstate == "23505"


@router.post(
    "/itens/{item_id}/valores",
    response_model=ValorItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_value(
    item_id: int = Path(gt=0),
    data: ValorItemCreate = ...,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> ValorItemRead:
    try:
        value_fields = data.model_dump(
            exclude={"campo_id"},
            exclude_none=True,
        )

        registro = ValorItemService.create_value(
            db=db,
            empresa_id=membership.empresa_id,
            item_id=item_id,
            campo_id=data.campo_id,
            value_fields=value_fields,
        )

        db.commit()
        db.refresh(registro)

        return registro

    except ItemValorNaoEncontradoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except CampoValorNaoEncontradoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ItemSemCategoriaError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValorItemDuplicadoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except (
        CampoCategoriaIncompativelError,
        TipoValorIncompativelError,
        OpcaoValorInvalidaError,
        ValueError,
    ) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Este item já possui um valor para o campo informado."
                ),
            ) from error

        raise


@router.get(
    "/itens/{item_id}/valores",
    response_model=list[ValorItemRead],
)
def list_values(
    item_id: int = Path(gt=0),
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[ValorItemRead]:
    try:
        return ValorItemService.list_values(
            db=db,
            empresa_id=membership.empresa_id,
            item_id=item_id,
        )

    except ItemValorNaoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/valores/{valor_id}",
    response_model=ValorItemRead,
)
def get_value(
    valor_id: int = Path(gt=0),
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> ValorItemRead:
    registro = ValorItemService.get_value(
        db=db,
        empresa_id=membership.empresa_id,
        valor_id=valor_id,
    )

    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valor personalizado não encontrado.",
        )

    return registro


@router.patch(
    "/valores/{valor_id}",
    response_model=ValorItemRead,
)
def update_value(
    valor_id: int,
    data: ValorItemUpdate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> ValorItemRead:
    changes = data.model_dump(exclude_unset=True)

    try:
        registro = ValorItemService.update_value(
            db=db,
            empresa_id=membership.empresa_id,
            valor_id=valor_id,
            changes=changes,
        )

        if registro is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valor personalizado não encontrado.",
            )

        db.commit()
        db.refresh(registro)

        return registro

    except ItemValorNaoEncontradoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except CampoValorNaoEncontradoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ItemSemCategoriaError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValorItemDuplicadoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except (
        CampoCategoriaIncompativelError,
        TipoValorIncompativelError,
        OpcaoValorInvalidaError,
        ValueError,
    ) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "O item já possui um valor para o campo informado."
                ),
            ) from error

        raise