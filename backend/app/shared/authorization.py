from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.auth.models import EmpresaUsuario
from app.shared.company_dependencies import (
    get_current_company_membership,
)
from app.shared.company_dependencies import (
    get_current_company_membership_for_management,
)


VALID_ROLES = {"OWNER", "OPERATOR", "VIEWER"}


def require_role(
    *allowed_roles: str,
    membership_dependency: Callable = get_current_company_membership,
) -> Callable:
    normalized_roles = {
        role.strip().upper()
        for role in allowed_roles
    }

    if not normalized_roles:
        raise ValueError(
            "Pelo menos um papel deve ser informado."
        )

    invalid_roles = normalized_roles - VALID_ROLES

    if invalid_roles:
        raise ValueError(
            f"Papéis inválidos: {', '.join(sorted(invalid_roles))}."
        )

    def role_dependency(
        membership: EmpresaUsuario = Depends(
            membership_dependency
        ),
    ) -> EmpresaUsuario:
        if membership.papel not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não possui permissão para esta operação.",
            )

        return membership

    return role_dependency