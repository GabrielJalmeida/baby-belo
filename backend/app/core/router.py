from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import EmpresaUsuario, Usuario
from app.core.schemas import (
    EmpresaCreate,
    EmpresaResponse,
    EmpresaUpdate,
)
from app.core.service import EmpresaService
from app.shared.authorization import require_role
from app.shared.company_dependencies import get_current_company_membership
from app.shared.database import get_db
from app.shared.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/empresas",
    tags=["empresas"],
)


@router.post(
    "",
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    data: EmpresaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmpresaResponse:
    company = EmpresaService.create_company(
        db=db,
        user_id=current_user.id,
        nome=data.nome,
    )

    db.commit()
    db.refresh(company)

    return company


@router.get(
    "",
    response_model=list[EmpresaResponse],
)
def list_companies(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EmpresaResponse]:
    return EmpresaService.list_user_companies(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{company_id}",
    response_model=EmpresaResponse,
)
def get_company(
    company_id: int,
    membership: EmpresaUsuario = Depends(
        get_current_company_membership,
    ),
    db: Session = Depends(get_db),
) -> EmpresaResponse:
    if membership.empresa_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A empresa informada não corresponde ao contexto ativo.",
        )

    company = EmpresaService.get_company(
        db=db,
        company_id=company_id,
    )

    if company is None or not company.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada.",
        )

    return company


@router.patch(
    "/{company_id}",
    response_model=EmpresaResponse,
)
def update_company(
    company_id: int,
    data: EmpresaUpdate,
    membership: EmpresaUsuario = Depends(
        require_role("OWNER"),
    ),
    db: Session = Depends(get_db),
) -> EmpresaResponse:
    if membership.empresa_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A empresa informada não corresponde ao contexto ativo.",
        )

    company = EmpresaService.update_company(
        db=db,
        company_id=company_id,
        nome=data.nome,
        ativo=data.ativo,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada.",
        )

    db.commit()
    db.refresh(company)

    return company