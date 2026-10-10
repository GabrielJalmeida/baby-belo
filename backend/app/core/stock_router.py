from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.stock_schemas import (
    EstoqueBaixoResponse,
    SaldoEstoqueResponse,
)
from app.core.stock_service import StockService
from app.shared.company_dependencies import (
    get_current_company_membership,
)
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/estoque",
    tags=["estoque"],
)


@router.get(
    "/saldos",
    response_model=list[SaldoEstoqueResponse],
)
def list_stock_balances(
    membership=Depends(get_current_company_membership),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SaldoEstoqueResponse]:
    return StockService.list_balances(
        db=db,
        empresa_id=membership.empresa_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/baixo",
    response_model=list[EstoqueBaixoResponse],
)
def list_low_stock(
    membership=Depends(get_current_company_membership),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[EstoqueBaixoResponse]:
    return StockService.list_low_stock(
        db=db,
        empresa_id=membership.empresa_id,
        limit=limit,
        offset=offset,
    )
