from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.unit_schemas import (
    UnidadeCreate,
    UnidadeResponse,
    UnidadeUpdate,
)
from app.core.unit_service import UnidadeService
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/unidades",
    tags=["unidades"],
)


@router.post(
    "",
    response_model=UnidadeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_unit(
    data: UnidadeCreate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> UnidadeResponse:
    unit = UnidadeService.create_unit(
        db=db,
        empresa_id=membership.empresa_id,
        nome=data.nome,
        simbolo=data.simbolo,
        permite_decimal=data.permite_decimal,
    )

    db.commit()
    db.refresh(unit)

    return unit

@router.get(
    "",
    response_model=list[UnidadeResponse],
)
def list_units(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    membership=Depends(
        get_current_company_membership,
    ),
    db: Session = Depends(get_db),
) -> list[UnidadeResponse]:
    return UnidadeService.list_units(
        db=db,
        empresa_id=membership.empresa_id,
        limit=limit,
        offset=offset,
    )



@router.get(
    "/{unit_id}",
    response_model=UnidadeResponse,
)
def get_unit(
    unit_id: int,
    membership=Depends(
        get_current_company_membership,
    ),
    db: Session = Depends(get_db),
) -> UnidadeResponse:
    unit = UnidadeService.get_unit(
        db=db,
        empresa_id=membership.empresa_id,
        unit_id=unit_id,
    )

    if unit is None or not unit.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada.",
        )

    return unit


@router.patch(
    "/{unit_id}",
    response_model=UnidadeResponse,
)
def update_unit(
    unit_id: int,
    data: UnidadeUpdate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> UnidadeResponse:
    unit = UnidadeService.update_unit(
        db=db,
        empresa_id=membership.empresa_id,
        unit_id=unit_id,
        changes=data.model_dump(exclude_unset=True),
    )

    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade não encontrada.",
        )

    db.commit()
    db.refresh(unit)

    return unit