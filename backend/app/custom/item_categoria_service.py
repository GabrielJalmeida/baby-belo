from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.item_models import Item
from app.custom.models import Categoria, ItemCategoria, ValorItem


class ItemCategoriaItemNaoEncontradoError(ValueError):
    """O item não existe, está inativo ou pertence a outra empresa."""


class ItemCategoriaCategoriaNaoEncontradaError(ValueError):
    """A categoria não existe, está inativa ou pertence a outra empresa."""


class ItemCategoriaComValoresError(ValueError):
    """Não permite trocar a categoria de um item com valores CUSTOM."""


class ItemCategoriaService:
    @staticmethod
    def _buscar_item(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> Item:
        statement = select(Item).where(
            Item.id == item_id,
            Item.empresa_id == empresa_id,
            Item.ativo.is_(True),
        )

        item = db.scalar(statement)

        if item is None or not item.ativo:
            raise ItemCategoriaItemNaoEncontradoError(
                "Item não encontrado ou inativo nesta empresa."
            )

        return item

    @staticmethod
    def _buscar_categoria(
        db: Session,
        empresa_id: int,
        categoria_id: int,
    ) -> Categoria:
        statement = select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == empresa_id,
            Categoria.ativo.is_(True),
        )

        categoria = db.scalar(statement)

        if categoria is None:
            raise ItemCategoriaCategoriaNaoEncontradaError(
                "Categoria não encontrada ou inativa nesta empresa."
            )

        return categoria

    @staticmethod
    def _possui_valores_custom(
        db: Session,
        item_id: int,
    ) -> bool:
        statement = (
            select(ValorItem.id)
            .where(ValorItem.item_id == item_id)
            .limit(1)
        )

        return db.scalar(statement) is not None

    @staticmethod
    def get_item_category(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> ItemCategoria | None:
        ItemCategoriaService._buscar_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
        )

        statement = select(ItemCategoria).where(
            ItemCategoria.item_id == item_id,
            ItemCategoria.empresa_id == empresa_id,
        )

        return db.scalar(statement)

    @staticmethod
    def assign_category(
        db: Session,
        empresa_id: int,
        item_id: int,
        categoria_id: int,
    ) -> ItemCategoria:
        ItemCategoriaService._buscar_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
        )

        categoria = ItemCategoriaService._buscar_categoria(
            db=db,
            empresa_id=empresa_id,
            categoria_id=categoria_id,
        )

        statement = select(ItemCategoria).where(
            ItemCategoria.item_id == item_id,
            ItemCategoria.empresa_id == empresa_id,
        )

        associacao = db.scalar(statement)

        if associacao is not None:
            # Repetir a mesma atribuição não cria outra relação.
            if associacao.categoria_id == categoria.id:
                return associacao

            # Os valores dependem da categoria e de seus campos.
            # Por isso, não podemos trocar a categoria depois do uso.
            if ItemCategoriaService._possui_valores_custom(
                db=db,
                item_id=item_id,
            ):
                raise ItemCategoriaComValoresError(
                    "Não é permitido trocar a categoria de um item "
                    "que já possui valores personalizados."
                )

            associacao.categoria_id = categoria.id
            db.flush()

            return associacao

        associacao = ItemCategoria(
            item_id=item_id,
            categoria_id=categoria.id,
            empresa_id=empresa_id,
        )

        db.add(associacao)
        db.flush()

        return associacao