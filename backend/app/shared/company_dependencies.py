from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.company_service import CompanyAccessService
from app.auth.models import EmpresaUsuario, Usuario
from app.shared.database import get_db
from app.shared.dependencies import get_current_user


def get_current_company_membership(
    company_id: int | None = Header(
        default=None,
        alias="X-Company-ID",
    ),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmpresaUsuario:
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID é obrigatório.",
        )

    if company_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID deve ser um número positivo.",
        )

    membership = CompanyAccessService.get_active_membership(
        db=db,
        user_id=current_user.id,
        company_id=company_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não possui acesso a esta empresa.",
        )

    return membership