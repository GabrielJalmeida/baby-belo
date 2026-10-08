from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import EmpresaUsuario
from app.core.models import Empresa
from app.core.service import EmpresaService


class CompanyApplicationService:
    @staticmethod
    def create_company(
        db: Session,
        user_id: int,
        nome: str,
    ) -> Empresa:
        company = EmpresaService.create_company(
            db=db,
            nome=nome,
        )

        membership = EmpresaUsuario(
            empresa_id=company.id,
            usuario_id=user_id,
            papel="OWNER",
            ativo=True,
        )

        db.add(membership)
        db.flush()

        return company

    @staticmethod
    def list_user_companies(
        db: Session,
        user_id: int,
    ) -> list[Empresa]:
        statement = (
            select(Empresa)
            .join(
                EmpresaUsuario,
                EmpresaUsuario.empresa_id == Empresa.id,
            )
            .where(
                EmpresaUsuario.usuario_id == user_id,
                EmpresaUsuario.ativo.is_(True),
                Empresa.ativo.is_(True),
            )
            .order_by(Empresa.id)
        )

        return list(db.scalars(statement).all())