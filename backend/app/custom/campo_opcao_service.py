from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.custom.models import Campo, CampoOpcao


class CampoOpcaoCampoNaoEncontradoError(ValueError):
    """O campo não existe ou não pertence à empresa atual."""


class CampoNaoListaError(ValueError):
    """O campo precisa ser do tipo LISTA para possuir opções."""


class CampoOpcaoDuplicadaError(ValueError):
    """O campo já possui uma opção com esse valor."""


class CampoOpcaoService:
    @staticmethod
    def _normalizar_valor(valor: str) -> str:
        valor_normalizado = valor.strip()

        if not valor_normalizado:
            raise ValueError("O valor da opção não pode ser vazio.")

        return valor_normalizado

    @staticmethod
    def _buscar_campo_lista(
        db: Session,
        empresa_id: int,
        campo_id: int,
    ) -> Campo:
        statement = select(Campo).where(
            Campo.id == campo_id,
            Campo.empresa_id == empresa_id,
            Campo.ativo.is_(True),
        )

        campo = db.scalar(statement)

        if campo is None:
            raise CampoOpcaoCampoNaoEncontradoError(
                "Campo não encontrado ou inativo nesta empresa."
            )

        if campo.tipo_dado != "LISTA":
            raise CampoNaoListaError(
                "Somente campos do tipo LISTA podem possuir opções."
            )

        return campo

    @staticmethod
    def _valor_existe(
        db: Session,
        campo_id: int,
        valor: str,
        excluir_opcao_id: int | None = None,
    ) -> bool:
        statement = select(CampoOpcao.id).where(
            CampoOpcao.campo_id == campo_id,
            CampoOpcao.valor == valor,
        )

        if excluir_opcao_id is not None:
            statement = statement.where(
                CampoOpcao.id != excluir_opcao_id,
            )

        return db.scalar(statement) is not None

    @staticmethod
    def create_option(
        db: Session,
        empresa_id: int,
        campo_id: int,
        valor: str,
        ordem_exibicao: int = 0,
        ativo: bool = True,
    ) -> CampoOpcao:
        CampoOpcaoService._buscar_campo_lista(
            db=db,
            empresa_id=empresa_id,
            campo_id=campo_id,
        )

        valor = CampoOpcaoService._normalizar_valor(valor)

        if CampoOpcaoService._valor_existe(
            db=db,
            campo_id=campo_id,
            valor=valor,
        ):
            raise CampoOpcaoDuplicadaError(
                "Já existe uma opção com esse valor neste campo."
            )

        opcao = CampoOpcao(
            campo_id=campo_id,
            valor=valor,
            ordem_exibicao=ordem_exibicao,
            ativo=ativo,
        )

        db.add(opcao)
        db.flush()

        return opcao

    @staticmethod
    def list_options(
        db: Session,
        empresa_id: int,
        campo_id: int,
    ) -> list[CampoOpcao]:
        CampoOpcaoService._buscar_campo_lista(
            db=db,
            empresa_id=empresa_id,
            campo_id=campo_id,
        )

        statement = (
            select(CampoOpcao)
            .where(
                CampoOpcao.campo_id == campo_id,
                CampoOpcao.ativo.is_(True),
            )
            .order_by(
                CampoOpcao.ordem_exibicao,
                CampoOpcao.id,
            )
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_option(
        db: Session,
        empresa_id: int,
        opcao_id: int,
    ) -> CampoOpcao | None:
        statement = (
            select(CampoOpcao)
            .join(
                Campo,
                Campo.id == CampoOpcao.campo_id,
            )
            .where(
                CampoOpcao.id == opcao_id,
                Campo.empresa_id == empresa_id,
                Campo.ativo.is_(True),
                Campo.tipo_dado == "LISTA",
            )
        )

        return db.scalar(statement)

    @staticmethod
    def update_option(
        db: Session,
        empresa_id: int,
        opcao_id: int,
        changes: Mapping[str, object],
    ) -> CampoOpcao | None:
        campos_permitidos = {
            "valor",
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

        opcao = CampoOpcaoService.get_option(
            db=db,
            empresa_id=empresa_id,
            opcao_id=opcao_id,
        )

        if opcao is None:
            return None

        if "valor" in changes:
            valor_recebido = changes["valor"]

            if not isinstance(valor_recebido, str):
                raise ValueError("O valor da opção não pode ser nulo.")

            valor = CampoOpcaoService._normalizar_valor(
                valor_recebido
            )

            if CampoOpcaoService._valor_existe(
                db=db,
                campo_id=opcao.campo_id,
                valor=valor,
                excluir_opcao_id=opcao.id,
            ):
                raise CampoOpcaoDuplicadaError(
                    "Já existe uma opção com esse valor neste campo."
                )

            opcao.valor = valor

        if "ordem_exibicao" in changes:
            ordem = changes["ordem_exibicao"]

            if (
                not isinstance(ordem, int)
                or isinstance(ordem, bool)
            ):
                raise ValueError(
                    "A ordem de exibição precisa ser um inteiro."
                )

            opcao.ordem_exibicao = ordem

        if "ativo" in changes:
            ativo = changes["ativo"]

            if not isinstance(ativo, bool):
                raise ValueError(
                    "O estado ativo precisa ser verdadeiro ou falso."
                )

            opcao.ativo = ativo

        db.flush()

        return opcao