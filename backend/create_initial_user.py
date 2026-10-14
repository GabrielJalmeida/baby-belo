from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from app.application.company_service import CompanyApplicationService
from app.auth.models import Usuario
from app.auth.service import AuthService
from app.shared.config import settings
from app.shared.database import SessionLocal


def required_input(prompt: str) -> str:
    value = input(prompt).strip()
    if not value:
        raise ValueError("Este campo é obrigatório.")
    return value


def main() -> int:
    url = make_url(settings.database_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        print("Por segurança, esta ferramenta só funciona com PostgreSQL local (localhost).")
        print("Confira DATABASE_URL em backend/.env. Nenhum dado foi alterado.")
        return 1

    print("Inicialização local do Estoque Flex — primeira conta OWNER")
    print(f"Banco alvo: {url.database} em {url.host}:{url.port or 5432}")
    print("Use apenas no banco local de desenvolvimento, nunca em produção.")

    try:
        nome = required_input("Nome do usuário: ")
        email_raw = required_input("E-mail: ")
        empresa_nome = required_input("Nome da primeira empresa: ")
        email = str(TypeAdapter(EmailStr).validate_python(email_raw)).strip().lower()
    except ValidationError:
        print("O e-mail informado não parece válido. Nenhum dado foi alterado.")
        return 1
    except (ValueError, KeyboardInterrupt) as exc:
        print("Operação cancelada ou campo obrigatório vazio. Nenhum dado foi alterado.")
        return 1

    if len(nome) > 120:
        print("O nome do usuário deve ter no máximo 120 caracteres.")
        return 1
    if len(empresa_nome) > 160:
        print("O nome da empresa deve ter no máximo 160 caracteres.")
        return 1

    password = getpass("Senha (8 a 128 caracteres; não será exibida): ")
    confirm = getpass("Repita a senha: ")
    if password != confirm:
        print("As senhas não coincidem. Nenhum dado foi alterado.")
        return 1
    if not 8 <= len(password) <= 128:
        print("A senha precisa ter entre 8 e 128 caracteres. Nenhum dado foi alterado.")
        return 1

    db = SessionLocal()
    try:
        user_count = db.scalar(select(func.count()).select_from(Usuario)) or 0
        if user_count:
            print(f"Este banco já contém {user_count} usuário(s).")
            confirm = input(
                "Criar uma nova conta OWNER neste banco local? "
                "Digite CRIAR para confirmar: "
            ).strip()

            if confirm != "CRIAR":
                print("Operação cancelada. Nenhum dado foi alterado.")
                return 1

        user = AuthService.create_user(
            db=db,
            nome=nome,
            email=email,
            senha=password,
        )
        company = CompanyApplicationService.create_company(
            db=db,
            user_id=user.id,
            nome=empresa_nome,
        )
        db.commit()

        print("Conta inicial criada com sucesso.")
        print(f"E-mail: {user.email}")
        print(f"Empresa: {company.nome}")
        print("Papel da conta: OWNER")
        print("Agora inicie a API e o frontend e entre com o e-mail e a senha informados.")
        return 0
    except Exception as exc:
        db.rollback()
        print("Não foi possível criar a conta inicial. A transação foi revertida.")
        print(f"Detalhe técnico: {type(exc).__name__}: {exc}")
        print("Confira DATABASE_URL, a instalação do schema e as dependências Python.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
