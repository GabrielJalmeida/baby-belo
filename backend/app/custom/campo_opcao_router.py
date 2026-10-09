from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.custom.campo_opcao_service import (
    CampoNaoListaError,
    CampoOpcaoCampoNaoEncontradoError,
    CampoOpcaoDuplicadaError,
    CampoOpcaoService,
)
from app.custom.schemas import (
    CampoOpcaoCreate,
    CampoOpcaoRead,
    CampoOpcaoUpdate,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/custom",
    tags=["custom-opcoes"],
)


def _is_unique_violation(error: IntegrityError) -> bool:
    original = error.orig

    sqlstate = (
        getattr(original, "sqlstate", None)
        or getattr(original, "pgcode", None)
    )

    return sqlstate == "23505"


def _raise_conflict() -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe uma opção com esse valor neste campo.",
    )


@router.post(
    "/opcoes",
    response_model=CampoOpcaoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_option(
    data: CampoOpcaoCreate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> CampoOpcaoRead:
    try:
        opcao = CampoOpcaoService.create_option(
            db=db,
            empresa_id=membership.empresa_id,
            campo_id=data.campo_id,
            valor=data.valor,
            ordem_exibicao=data.ordem_exibicao,
            ativo=data.ativo,
        )

        db.commit()
        db.refresh(opcao)

        return opcao

    except CampoOpcaoCampoNaoEncontradoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except CampoNaoListaError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except CampoOpcaoDuplicadaError:
        db.rollback()
        _raise_conflict()

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            _raise_conflict()

        raise


@router.get(
    "/campos/{campo_id}/opcoes",
    response_model=list[CampoOpcaoRead],
)
def list_options(
    campo_id: int = Path(gt=0),
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[CampoOpcaoRead]:
    try:
        return CampoOpcaoService.list_options(
            db=db,
            empresa_id=membership.empresa_id,
            campo_id=campo_id,
        )

    except CampoOpcaoCampoNaoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except CampoNaoListaError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get(
    "/opcoes/{opcao_id}",
    response_model=CampoOpcaoRead,
)
def get_option(
    opcao_id: int = Path(gt=0),
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> CampoOpcaoRead:
    opcao = CampoOpcaoService.get_option(
        db=db,
        empresa_id=membership.empresa_id,
        opcao_id=opcao_id,
    )

    if opcao is None or not opcao.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opção não encontrada.",
        )

    return opcao


@router.patch(
    "/opcoes/{opcao_id}",
    response_model=CampoOpcaoRead,
)
def update_option(
    opcao_id: int,
    data: CampoOpcaoUpdate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> CampoOpcaoRead:
    changes = data.model_dump(exclude_unset=True)

    try:
        opcao = CampoOpcaoService.update_option(
            db=db,
            empresa_id=membership.empresa_id,
            opcao_id=opcao_id,
            changes=changes,
        )

        if opcao is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opção não encontrada.",
            )

        db.commit()
        db.refresh(opcao)

        return opcao

    except CampoOpcaoCampoNaoEncontradoError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except CampoNaoListaError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except CampoOpcaoDuplicadaError:
        db.rollback()
        _raise_conflict()

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            _raise_conflict()

        raise