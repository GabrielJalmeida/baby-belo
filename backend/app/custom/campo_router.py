from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.custom.campo_service import (
    CampoCategoriaNaoEncontradaError,
    CampoEstruturalEmUsoError,
    CampoNomeDuplicadoError,
    CampoService,
)
from app.custom.schemas import (
    CampoCreate,
    CampoRead,
    CampoUpdate,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/custom/campos",
    tags=["custom-campos"],
)


def _raise_conflict(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def _is_unique_violation(error: IntegrityError) -> bool:
    original = error.orig

    sqlstate = (
        getattr(original, "sqlstate", None)
        or getattr(original, "pgcode", None)
    )

    return sqlstate == "23505"


@router.post(
    "",
    response_model=CampoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_field(
    data: CampoCreate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> CampoRead:
    try:
        campo = CampoService.create_field(
            db=db,
            empresa_id=membership.empresa_id,
            categoria_id=data.categoria_id,
            nome=data.nome,
            tipo_dado=data.tipo_dado,
            obrigatorio=data.obrigatorio,
            configuracao=data.configuracao,
            ordem_exibicao=data.ordem_exibicao,
            ativo=data.ativo,
        )

        db.commit()
        db.refresh(campo)

        return campo

    except CampoCategoriaNaoEncontradaError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada ou inativa nesta empresa.",
        )

    except CampoNomeDuplicadoError:
        db.rollback()
        _raise_conflict(
            "Já existe um campo com esse nome nesta categoria."
        )

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            _raise_conflict(
                "Já existe um campo com esse nome nesta categoria."
            )

        raise


@router.get(
    "",
    response_model=list[CampoRead],
)
def list_fields(
    categoria_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[CampoRead]:
    return CampoService.list_fields(
        db=db,
        empresa_id=membership.empresa_id,
        categoria_id=categoria_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{campo_id}",
    response_model=CampoRead,
)
def get_field(
    campo_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> CampoRead:
    campo = CampoService.get_field(
        db=db,
        empresa_id=membership.empresa_id,
        campo_id=campo_id,
    )

    if campo is None or not campo.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo não encontrado.",
        )

    return campo


@router.patch(
    "/{campo_id}",
    response_model=CampoRead,
)
def update_field(
    campo_id: int,
    data: CampoUpdate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> CampoRead:
    changes = data.model_dump(exclude_unset=True)

    try:
        campo = CampoService.update_field(
            db=db,
            empresa_id=membership.empresa_id,
            campo_id=campo_id,
            changes=changes,
        )

        if campo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campo não encontrado.",
            )

        db.commit()
        db.refresh(campo)

        return campo

    except CampoCategoriaNaoEncontradaError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada ou inativa nesta empresa.",
        )

    except CampoNomeDuplicadoError:
        db.rollback()
        _raise_conflict(
            "Já existe um campo com esse nome nesta categoria."
        )

    except CampoEstruturalEmUsoError as error:
        db.rollback()
        _raise_conflict(str(error))

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            _raise_conflict(
                "Já existe um campo com esse nome nesta categoria."
            )

        raise