from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.company_service import CompanyApplicationService
from app.core.schemas import (
    EmpresaCreate,
    EmpresaResponse,
    EmpresaUpdate,
)
from app.core.service import EmpresaService
from app.shared.authorization import require_role
from app.shared.company_dependencies import (
    get_current_company_membership,
    get_current_company_membership_for_management,
)
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmpresaResponse:
    company = CompanyApplicationService.create_company(
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EmpresaResponse]:
    return CompanyApplicationService.list_user_companies(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{company_id}",
    response_model=EmpresaResponse,
)
def get_company(
    company_id: int,
    membership=Depends(
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
    membership=Depends(
        require_role(
            "OWNER",
            membership_dependency=get_current_company_membership_for_management,
        )
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
        changes=data.model_dump(exclude_unset=True),
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada.",
        )

    db.commit()
    db.refresh(company)

    return company