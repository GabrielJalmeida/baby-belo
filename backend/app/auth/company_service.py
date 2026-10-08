from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import EmpresaUsuario
from app.core.models import Empresa


class CompanyAccessService:
    @staticmethod
    def get_active_membership(
        db: Session,
        user_id: int,
        company_id: int,
    ) -> EmpresaUsuario | None:
        statement = (
            select(EmpresaUsuario)
            .join(
                Empresa,
                Empresa.id == EmpresaUsuario.empresa_id,
            )
            .where(
                EmpresaUsuario.usuario_id == user_id,
                EmpresaUsuario.empresa_id == company_id,
                EmpresaUsuario.ativo.is_(True),
                Empresa.ativo.is_(True),
            )
        )

        return db.scalar(statement)

    @staticmethod
    def get_active_membership_for_management(
        db: Session,
        user_id: int,
        company_id: int,
    ) -> EmpresaUsuario | None:
        statement = (
            select(EmpresaUsuario)
            .where(
                EmpresaUsuario.usuario_id == user_id,
                EmpresaUsuario.empresa_id == company_id,
                EmpresaUsuario.ativo.is_(True),
            )
        )

        return db.scalar(statement)