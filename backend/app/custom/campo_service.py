from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.custom.models import Campo, Categoria, ValorItem


class CampoCategoriaNaoEncontradaError(ValueError):
    """A categoria não existe, está inativa ou pertence a outra empresa."""


class CampoNomeDuplicadoError(ValueError):
    """Já existe um campo com esse nome na categoria."""


class CampoEstruturalEmUsoError(ValueError):
    """Não permite alterar a estrutura de um campo que já possui valores."""


class CampoService:
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        nome_normalizado = nome.strip()

        if not nome_normalizado:
            raise ValueError("O nome do campo não pode ser vazio.")

        return nome_normalizado

    @staticmethod
    def _buscar_categoria_ativa(
        db: Session,
        empresa_id: int,
        categoria_id: int,
    ) -> Categoria | None:
        statement = select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == empresa_id,
            Categoria.ativo.is_(True),
        )

        return db.scalar(statement)

    @staticmethod
    def _nome_existe(
        db: Session,
        categoria_id: int,
        nome: str,
        excluir_campo_id: int | None = None,
    ) -> bool:
        statement = select(Campo.id).where(
            Campo.categoria_id == categoria_id,
            Campo.nome == nome,
        )

        if excluir_campo_id is not None:
            statement = statement.where(
                Campo.id != excluir_campo_id,
            )

        return db.scalar(statement) is not None

    @staticmethod
    def _possui_valores(
        db: Session,
        campo_id: int,
    ) -> bool:
        statement = (
            select(ValorItem.id)
            .where(ValorItem.campo_id == campo_id)
            .limit(1)
        )

        return db.scalar(statement) is not None

    @staticmethod
    def create_field(
        db: Session,
        empresa_id: int,
        categoria_id: int,
        nome: str,
        tipo_dado: str,
        obrigatorio: bool = False,
        configuracao: dict[str, Any] | None = None,
        ordem_exibicao: int = 0,
        ativo: bool = True,
    ) -> Campo:
        categoria = CampoService._buscar_categoria_ativa(
            db=db,
            empresa_id=empresa_id,
            categoria_id=categoria_id,
        )

        if categoria is None:
            raise CampoCategoriaNaoEncontradaError(
                "Categoria não encontrada ou inativa nesta empresa."
            )

        nome = CampoService._normalizar_nome(nome)
        configuracao = configuracao if configuracao is not None else {}

        if not isinstance(configuracao, dict):
            raise ValueError("A configuração precisa ser um objeto JSON.")

        if CampoService._nome_existe(
            db=db,
            categoria_id=categoria.id,
            nome=nome,
        ):
            raise CampoNomeDuplicadoError(
                "Já existe um campo com esse nome nesta categoria."
            )

        campo = Campo(
            empresa_id=empresa_id,
            categoria_id=categoria.id,
            nome=nome,
            tipo_dado=tipo_dado,
            obrigatorio=obrigatorio,
            configuracao=configuracao,
            ordem_exibicao=ordem_exibicao,
            ativo=ativo,
        )

        db.add(campo)
        db.flush()

        return campo

    @staticmethod
    def list_fields(
        db: Session,
        empresa_id: int,
        categoria_id: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Campo]:
        statement = select(Campo).where(
            Campo.empresa_id == empresa_id,
            Campo.ativo.is_(True),
        )

        if categoria_id is not None:
            statement = statement.where(
                Campo.categoria_id == categoria_id,
            )

        statement = statement.order_by(
            Campo.ordem_exibicao,
            Campo.id,
        )

        if limit is not None:
            statement = statement.limit(limit)

        if offset:
            statement = statement.offset(offset)

        return list(db.scalars(statement).all())

    @staticmethod
    def get_field(
        db: Session,
        empresa_id: int,
        campo_id: int,
    ) -> Campo | None:
        statement = select(Campo).where(
            Campo.id == campo_id,
            Campo.empresa_id == empresa_id,
        )

        return db.scalar(statement)

    @staticmethod
    def update_field(
        db: Session,
        empresa_id: int,
        campo_id: int,
        changes: Mapping[str, object],
    ) -> Campo | None:
        campos_permitidos = {
            "categoria_id",
            "nome",
            "tipo_dado",
            "obrigatorio",
            "configuracao",
            "ordem_exibicao",
            "ativo",
        }

        if not changes:
            raise ValueError(
                "Informe ao menos um campo para atualizar."
            )

        campos_invalidos = set(changes) - campos_permitidos

        if campos_invalidos:
            raise ValueError(
                "A atualização contém campos não permitidos."
            )

        statement = select(Campo).where(
            Campo.id == campo_id,
            Campo.empresa_id == empresa_id,
        )

        campo = db.scalar(statement)

        if campo is None:
            return None

        nova_categoria_id = campo.categoria_id

        if "categoria_id" in changes:
            categoria_id = changes["categoria_id"]

            if (
                not isinstance(categoria_id, int)
                or isinstance(categoria_id, bool)
                or categoria_id <= 0
            ):
                raise ValueError("O ID da categoria deve ser positivo.")

            categoria = CampoService._buscar_categoria_ativa(
                db=db,
                empresa_id=empresa_id,
                categoria_id=categoria_id,
            )

            if categoria is None:
                raise CampoCategoriaNaoEncontradaError(
                    "Categoria não encontrada ou inativa nesta empresa."
                )

            nova_categoria_id = categoria.id

        novo_nome = campo.nome

        if "nome" in changes:
            nome_recebido = changes["nome"]

            if not isinstance(nome_recebido, str):
                raise ValueError("O nome do campo não pode ser nulo.")

            novo_nome = CampoService._normalizar_nome(nome_recebido)

        novo_tipo = changes.get("tipo_dado", campo.tipo_dado)

        alteracao_estrutural = (
            nova_categoria_id != campo.categoria_id
            or novo_tipo != campo.tipo_dado
        )

        if (
            alteracao_estrutural
            and CampoService._possui_valores(db, campo.id)
        ):
            raise CampoEstruturalEmUsoError(
                "Não é permitido alterar o tipo ou a categoria "
                "de um campo que já possui valores."
            )

        nome_ou_categoria_alterados = (
            novo_nome != campo.nome
            or nova_categoria_id != campo.categoria_id
        )

        if nome_ou_categoria_alterados and CampoService._nome_existe(
            db=db,
            categoria_id=nova_categoria_id,
            nome=novo_nome,
            excluir_campo_id=campo.id,
        ):
            raise CampoNomeDuplicadoError(
                "Já existe um campo com esse nome nesta categoria."
            )

        if "configuracao" in changes:
            configuracao = changes["configuracao"]

            if not isinstance(configuracao, dict):
                raise ValueError(
                    "A configuração precisa ser um objeto JSON."
                )

        for nome, valor in changes.items():
            if nome in {"categoria_id", "nome"}:
                continue

            if nome == "tipo_dado":
                campo.tipo_dado = valor
            elif nome == "configuracao":
                campo.configuracao = valor
            else:
                setattr(campo, nome, valor)

        campo.categoria_id = nova_categoria_id
        campo.nome = novo_nome

        db.flush()

        return campo