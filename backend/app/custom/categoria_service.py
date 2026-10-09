from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.custom.models import Categoria


class CategoriaNomeDuplicadoError(ValueError):
    """Indica que a empresa já possui uma categoria com esse nome."""


class CategoriaService:
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        nome_normalizado = nome.strip()

        if not nome_normalizado:
            raise ValueError("O nome da categoria não pode ser vazio.")

        return nome_normalizado

    @staticmethod
    def _normalizar_descricao(
        descricao: str | None,
    ) -> str | None:
        if descricao is None:
            return None

        return descricao.strip() or None

    @staticmethod
    def _nome_existe(
        db: Session,
        empresa_id: int,
        nome: str,
        excluir_categoria_id: int | None = None,
    ) -> bool:
        statement = select(Categoria.id).where(
            Categoria.empresa_id == empresa_id,
            Categoria.nome == nome,
        )

        if excluir_categoria_id is not None:
            statement = statement.where(
                Categoria.id != excluir_categoria_id,
            )

        return db.scalar(statement) is not None

    @staticmethod
    def create_category(
        db: Session,
        empresa_id: int,
        nome: str,
        descricao: str | None = None,
    ) -> Categoria:
        nome = CategoriaService._normalizar_nome(nome)
        descricao = CategoriaService._normalizar_descricao(descricao)

        if CategoriaService._nome_existe(
            db=db,
            empresa_id=empresa_id,
            nome=nome,
        ):
            raise CategoriaNomeDuplicadoError(
                "Já existe uma categoria com esse nome nesta empresa."
            )

        categoria = Categoria(
            empresa_id=empresa_id,
            nome=nome,
            descricao=descricao,
            ativo=True,
        )

        db.add(categoria)
        db.flush()

        return categoria

    @staticmethod
    def list_categories(
        db: Session,
        empresa_id: int,
    ) -> list[Categoria]:
        statement = (
            select(Categoria)
            .where(
                Categoria.empresa_id == empresa_id,
                Categoria.ativo.is_(True),
            )
            .order_by(Categoria.id)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_category(
        db: Session,
        empresa_id: int,
        categoria_id: int,
    ) -> Categoria | None:
        statement = select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == empresa_id,
        )

        return db.scalar(statement)

    @staticmethod
    def update_category(
        db: Session,
        empresa_id: int,
        categoria_id: int,
        changes: Mapping[str, object],
    ) -> Categoria | None:
        campos_permitidos = {"nome", "descricao", "ativo"}

        if not changes:
            raise ValueError(
                "Informe ao menos um campo para atualizar."
            )

        campos_invalidos = set(changes) - campos_permitidos

        if campos_invalidos:
            raise ValueError(
                "A atualização contém campos não permitidos."
            )

        categoria = CategoriaService.get_category(
            db=db,
            empresa_id=empresa_id,
            categoria_id=categoria_id,
        )

        if categoria is None:
            return None

        if "nome" in changes:
            nome_recebido = changes["nome"]

            if not isinstance(nome_recebido, str):
                raise ValueError("O nome não pode ser nulo.")

            nome = CategoriaService._normalizar_nome(nome_recebido)

            if CategoriaService._nome_existe(
                db=db,
                empresa_id=empresa_id,
                nome=nome,
                excluir_categoria_id=categoria.id,
            ):
                raise CategoriaNomeDuplicadoError(
                    "Já existe uma categoria com esse nome nesta empresa."
                )

            categoria.nome = nome

        if "descricao" in changes:
            descricao = changes["descricao"]

            if descricao is not None and not isinstance(descricao, str):
                raise ValueError(
                    "A descrição deve ser um texto ou nula."
                )

            categoria.descricao = CategoriaService._normalizar_descricao(
                descricao,
            )

        if "ativo" in changes:
            ativo = changes["ativo"]

            if not isinstance(ativo, bool):
                raise ValueError(
                    "O estado ativo deve ser verdadeiro ou falso."
                )

            categoria.ativo = ativo

        db.flush()

        return categoria