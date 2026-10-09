from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.custom.categoria_service import (
    CategoriaNomeDuplicadoError,
    CategoriaService,
)
from app.custom.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
)
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db


router = APIRouter(
    prefix="/api/v1/custom/categorias",
    tags=["custom-categorias"],
)


def _is_unique_violation(error: IntegrityError) -> bool:
    """Identifica violações UNIQUE reportadas pelo PostgreSQL."""
    original = error.orig

    sqlstate = (
        getattr(original, "sqlstate", None)
        or getattr(original, "pgcode", None)
    )

    return sqlstate == "23505"


def _raise_name_conflict() -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe uma categoria com esse nome nesta empresa.",
    )


@router.post(
    "",
    response_model=CategoriaRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoriaCreate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> CategoriaRead:
    try:
        categoria = CategoriaService.create_category(
            db=db,
            empresa_id=membership.empresa_id,
            nome=data.nome,
            descricao=data.descricao,
        )

        db.commit()
        db.refresh(categoria)

        return categoria

    except CategoriaNomeDuplicadoError:
        db.rollback()
        _raise_name_conflict()

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            _raise_name_conflict()

        raise


@router.get(
    "",
    response_model=list[CategoriaRead],
)
def list_categories(
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> list[CategoriaRead]:
    return CategoriaService.list_categories(
        db=db,
        empresa_id=membership.empresa_id,
    )


@router.get(
    "/{categoria_id}",
    response_model=CategoriaRead,
)
def get_category(
    categoria_id: int,
    membership=Depends(get_current_company_membership),
    db: Session = Depends(get_db),
) -> CategoriaRead:
    categoria = CategoriaService.get_category(
        db=db,
        empresa_id=membership.empresa_id,
        categoria_id=categoria_id,
    )

    if categoria is None or not categoria.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada.",
        )

    return categoria


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaRead,
)
def update_category(
    categoria_id: int,
    data: CategoriaUpdate,
    membership=Depends(require_role("OWNER", "OPERATOR")),
    db: Session = Depends(get_db),
) -> CategoriaRead:
    changes = data.model_dump(exclude_unset=True)

    try:
        categoria = CategoriaService.update_category(
            db=db,
            empresa_id=membership.empresa_id,
            categoria_id=categoria_id,
            changes=changes,
        )

        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada.",
            )

        db.commit()
        db.refresh(categoria)

        return categoria

    except CategoriaNomeDuplicadoError:
        db.rollback()
        _raise_name_conflict()

    except IntegrityError as error:
        db.rollback()

        if _is_unique_violation(error):
            _raise_name_conflict()

        raise