from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.item_models import Item
from app.custom.models import Campo, CampoOpcao, ItemCategoria, ValorItem


class ItemValorNaoEncontradoError(ValueError):
    """O item não existe, está inativo ou pertence a outra empresa."""


class ItemSemCategoriaError(ValueError):
    """O item precisa ter uma categoria antes de receber valores customizados."""


class CampoValorNaoEncontradoError(ValueError):
    """O campo não existe, está inativo ou pertence a outra empresa."""


class CampoCategoriaIncompativelError(ValueError):
    """O campo não pertence à categoria associada ao item."""


class TipoValorIncompativelError(ValueError):
    """O tipo de valor não corresponde ao tipo configurado no campo."""


class OpcaoValorInvalidaError(ValueError):
    """A opção não existe, está inativa ou pertence a outro campo."""


class ValorItemDuplicadoError(ValueError):
    """Já existe um valor para este campo neste item."""


COLUNAS_VALOR = (
    "valor_texto",
    "valor_inteiro",
    "valor_decimal",
    "valor_monetario",
    "valor_booleano",
    "valor_data",
    "opcao_id",
)

COLUNA_POR_TIPO = {
    "TEXTO_CURTO": "valor_texto",
    "TEXTO_LONGO": "valor_texto",
    "INTEIRO": "valor_inteiro",
    "DECIMAL": "valor_decimal",
    "DINHEIRO": "valor_monetario",
    "BOOLEANO": "valor_booleano",
    "DATA": "valor_data",
    "LISTA": "opcao_id",
}


class ValorItemService:
    @staticmethod
    def _buscar_item(
        db: Session,
        empresa_id: int,
        item_id: int,
        *,
        exigir_ativo: bool,
    ) -> Item:
        statement = select(Item).where(
            Item.id == item_id,
            Item.empresa_id == empresa_id,
        )

        item = db.scalar(statement)

        if item is None or (exigir_ativo and not item.ativo):
            raise ItemValorNaoEncontradoError(
                "Item não encontrado ou inativo nesta empresa."
            )

        return item

    @staticmethod
    def _buscar_categoria_item(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> ItemCategoria:
        statement = select(ItemCategoria).where(
            ItemCategoria.item_id == item_id,
            ItemCategoria.empresa_id == empresa_id,
        )

        associacao = db.scalar(statement)

        if associacao is None:
            raise ItemSemCategoriaError(
                "O item precisa possuir uma categoria antes de "
                "receber valores personalizados."
            )

        return associacao

    @staticmethod
    def _buscar_campo(
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
            raise CampoValorNaoEncontradoError(
                "Campo não encontrado ou inativo nesta empresa."
            )

        return campo

    @staticmethod
    def _validar_categoria(
        associacao: ItemCategoria,
        campo: Campo,
    ) -> None:
        if associacao.categoria_id != campo.categoria_id:
            raise CampoCategoriaIncompativelError(
                "O campo informado não pertence à categoria deste item."
            )

    @staticmethod
    def _extrair_valor(
        value_fields: Mapping[str, object],
    ) -> tuple[str, object]:
        campos_invalidos = set(value_fields) - set(COLUNAS_VALOR)

        if campos_invalidos:
            raise ValueError(
                "A requisição contém campos de valor não permitidos."
            )

        preenchidos = [
            nome
            for nome in COLUNAS_VALOR
            if nome in value_fields and value_fields[nome] is not None
        ]

        if len(preenchidos) != 1:
            raise ValueError(
                "Informe exatamente um tipo de valor por vez."
            )

        nome = preenchidos[0]
        return nome, value_fields[nome]

    @staticmethod
    def _validar_tipo(
        campo: Campo,
        coluna: str,
    ) -> None:
        coluna_esperada = COLUNA_POR_TIPO.get(campo.tipo_dado)

        if coluna_esperada is None or coluna != coluna_esperada:
            raise TipoValorIncompativelError(
                "O valor informado não corresponde ao tipo "
                "configurado no campo."
            )

    @staticmethod
    def _validar_opcao(
        db: Session,
        campo_id: int,
        opcao_id: object,
    ) -> None:
        if not isinstance(opcao_id, int) or isinstance(opcao_id, bool):
            raise OpcaoValorInvalidaError(
                "A opção informada é inválida."
            )

        statement = select(CampoOpcao.id).where(
            CampoOpcao.id == opcao_id,
            CampoOpcao.campo_id == campo_id,
            CampoOpcao.ativo.is_(True),
        )

        if db.scalar(statement) is None:
            raise OpcaoValorInvalidaError(
                "A opção não existe, está inativa ou não pertence "
                "a este campo."
            )

    @staticmethod
    def _validar_contexto(
        db: Session,
        empresa_id: int,
        item_id: int,
        campo_id: int,
    ) -> Campo:
        ValorItemService._buscar_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
            exigir_ativo=True,
        )

        associacao = ValorItemService._buscar_categoria_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
        )

        campo = ValorItemService._buscar_campo(
            db=db,
            empresa_id=empresa_id,
            campo_id=campo_id,
        )

        ValorItemService._validar_categoria(
            associacao=associacao,
            campo=campo,
        )

        return campo

    @staticmethod
    def create_value(
        db: Session,
        empresa_id: int,
        item_id: int,
        campo_id: int,
        value_fields: Mapping[str, object],
    ) -> ValorItem:
        campo = ValorItemService._validar_contexto(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
            campo_id=campo_id,
        )

        coluna, valor = ValorItemService._extrair_valor(value_fields)

        ValorItemService._validar_tipo(
            campo=campo,
            coluna=coluna,
        )

        if coluna == "opcao_id":
            ValorItemService._validar_opcao(
                db=db,
                campo_id=campo.id,
                opcao_id=valor,
            )

        consulta_existente = select(ValorItem.id).where(
            ValorItem.item_id == item_id,
            ValorItem.campo_id == campo_id,
        )

        if db.scalar(consulta_existente) is not None:
            raise ValorItemDuplicadoError(
                "Este item já possui um valor para o campo informado."
            )

        dados = {nome: None for nome in COLUNAS_VALOR}
        dados[coluna] = valor

        registro = ValorItem(
            item_id=item_id,
            campo_id=campo_id,
            **dados,
        )

        db.add(registro)
        db.flush()

        return registro

    @staticmethod
    def list_values(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> list[ValorItem]:
        ValorItemService._buscar_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
            exigir_ativo=False,
        )

        statement = (
            select(ValorItem)
            .where(ValorItem.item_id == item_id)
            .order_by(ValorItem.id)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_value(
        db: Session,
        empresa_id: int,
        valor_id: int,
    ) -> ValorItem | None:
        statement = (
            select(ValorItem)
            .join(Item, Item.id == ValorItem.item_id)
            .where(
                ValorItem.id == valor_id,
                Item.empresa_id == empresa_id,
            )
        )

        return db.scalar(statement)

    @staticmethod
    def update_value(
        db: Session,
        empresa_id: int,
        valor_id: int,
        changes: Mapping[str, object],
    ) -> ValorItem | None:
        coluna, valor = ValorItemService._extrair_valor(changes)

        registro = ValorItemService.get_value(
            db=db,
            empresa_id=empresa_id,
            valor_id=valor_id,
        )

        if registro is None:
            return None

        campo = ValorItemService._validar_contexto(
            db=db,
            empresa_id=empresa_id,
            item_id=registro.item_id,
            campo_id=registro.campo_id,
        )

        ValorItemService._validar_tipo(
            campo=campo,
            coluna=coluna,
        )

        if coluna == "opcao_id":
            ValorItemService._validar_opcao(
                db=db,
                campo_id=campo.id,
                opcao_id=valor,
            )

        for nome in COLUNAS_VALOR:
            setattr(registro, nome, None)

        setattr(registro, coluna, valor)

        db.flush()

        return registro