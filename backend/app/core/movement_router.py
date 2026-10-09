
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.inventory_service import (
    ItemBloqueadoPorInventarioAbertoError,
)

from app.core.movement_schemas import (
    MovimentacaoCreate,
    MovimentacaoResponse,
    SaldoResponse,
)
from app.core.movement_service import (
    ItemInativoError,
    ItemMovimentacaoNaoEncontradoError,
    MovimentacaoService,
    QuantidadeFracionariaError,
    SaldoInsuficienteError,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import (
    get_current_company_membership,
)
from app.shared.database import get_db


router = APIRouter(tags=["movimentações"])


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

    if isinstance(exc, ItemMovimentacaoNaoEncontradoError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado nesta empresa.",
        ) from exc

    if isinstance(exc, ItemInativoError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SaldoInsuficienteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, QuantidadeFracionariaError):
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

        if sqlstate == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflito com uma restrição de unicidade.",
            ) from exc

        if sqlstate in {"23503", "23514"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A movimentação viola uma regra de integridade.",
            ) from exc

    raise exc


@router.post(
    "/api/v1/movimentacoes",
    response_model=MovimentacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_movement(
    data: MovimentacaoCreate,
    membership=Depends(
        require_role("OWNER", "OPERATOR"),
    ),
    db: Session = Depends(get_db),
) -> MovimentacaoResponse:
    try:
        movement = MovimentacaoService.create_movement(
            db=db,
            empresa_id=membership.empresa_id,
            item_id=data.item_id,
            tipo=data.tipo,
            quantidade=data.quantidade,
            motivo=data.motivo,
            observacao=data.observacao,
            ocorrida_em=data.ocorrida_em,
        )

        db.commit()
        db.refresh(movement)

        return movement

    except (ValueError, DBAPIError) as exc:
        _handle_write_error(db, exc)


@router.get(
    "/api/v1/itens/{item_id}/movimentacoes",
    response_model=list[MovimentacaoResponse],
)
def list_item_movements(
    item_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[MovimentacaoResponse]:
    movements = MovimentacaoService.list_movements(
        db=db,
        empresa_id=membership.empresa_id,
        item_id=item_id,
    )

    if movements is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado nesta empresa.",
        )

    return movements


@router.get(
    "/api/v1/itens/{item_id}/saldo",
    response_model=SaldoResponse,
)
def get_item_balance(
    item_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> SaldoResponse:
    balance = MovimentacaoService.get_stock_balance(
        db=db,
        empresa_id=membership.empresa_id,
        item_id=item_id,
    )

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado nesta empresa.",
        )

    return {
        "empresa_id": membership.empresa_id,
        "item_id": item_id,
        "saldo_atual": balance,
    }