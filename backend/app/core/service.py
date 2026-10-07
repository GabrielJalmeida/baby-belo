from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import EmpresaUsuario
from app.core.models import Empresa


class EmpresaService:
    @staticmethod
    def create_company(
        db: Session,
        user_id: int,
        nome: str,
    ) -> Empresa:
        company = Empresa(
            nome=nome.strip(),
            ativo=True,
        )

        db.add(company)
        db.flush()

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

    @staticmethod
    def get_company(
        db: Session,
        company_id: int,
    ) -> Empresa | None:
        return db.get(Empresa, company_id)

    @staticmethod
    def update_company(
        db: Session,
        company_id: int,
        nome: str | None = None,
        ativo: bool | None = None,
    ) -> Empresa | None:
        company = db.get(Empresa, company_id)

        if company is None:
            return None

        if nome is not None:
            company.nome = nome.strip()

        if ativo is not None:
            company.ativo = ativo

        db.flush()

        return company