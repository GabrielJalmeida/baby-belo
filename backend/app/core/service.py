from sqlalchemy.orm import Session

from app.core.models import Empresa


class EmpresaService:
    @staticmethod
    def create_company(
        db: Session,
        nome: str,
    ) -> Empresa:
        company = Empresa(
            nome=nome.strip(),
            ativo=True,
        )

        db.add(company)
        db.flush()

        return company

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
        changes: dict[str, object],
    ) -> Empresa | None:
        company = db.get(Empresa, company_id)

        if company is None:
            return None

        if "nome" in changes:
            company.nome = str(changes["nome"]).strip()

        if "ativo" in changes:
            company.ativo = bool(changes["ativo"])

        db.flush()

        return company