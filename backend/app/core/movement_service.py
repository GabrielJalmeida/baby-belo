
from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.item_models import Item
from app.core.movement_models import Movimentacao
from app.core.unit_models import Unidade
from app.core.inventory_service import InventarioService


TIPOS_ENTRADA = {"ENTRADA", "AJUSTE_ENTRADA"}
TIPOS_SAIDA = {"SAIDA", "AJUSTE_SAIDA"}
TIPOS_MOVIMENTACAO = TIPOS_ENTRADA | TIPOS_SAIDA
QUATRO_CASAS_DECIMAIS = Decimal("0.0001")
LIMITE_NUMERIC_18_4 = Decimal("100000000000000")


class ItemMovimentacaoNaoEncontradoError(ValueError):
    """Item inexistente no contexto da empresa informada."""


class ItemInativoError(ValueError):
    """Não é permitido movimentar um item inativo."""


class SaldoInsuficienteError(ValueError):
    """A saída deixaria o saldo do item negativo."""


class QuantidadeFracionariaError(ValueError):
    """A unidade do item não aceita quantidades fracionárias."""


class MovimentacaoService:
    @staticmethod
    def _get_item(
        db: Session,
        empresa_id: int,
        item_id: int,
        lock: bool = False,
    ) -> Item | None:
        statement = select(Item).where(
            Item.empresa_id == empresa_id,
            Item.id == item_id,
        )

        if lock:
            statement = statement.with_for_update()

        return db.scalar(statement)

    @staticmethod
    def _validate_quantity(
        quantidade: Decimal,
    ) -> Decimal:
        quantidade = Decimal(str(quantidade))

        if not quantidade.is_finite() or quantidade <= 0:
            raise ValueError(
                "A quantidade deve ser um número finito maior que zero."
            )

        if quantidade != quantidade.quantize(QUATRO_CASAS_DECIMAIS):
            raise ValueError(
                "A quantidade aceita no máximo quatro casas decimais."
            )

        if quantidade >= LIMITE_NUMERIC_18_4:
            raise ValueError(
                "A quantidade excede o limite permitido."
            )

        return quantidade

    @staticmethod
    def _get_unit(
        db: Session,
        empresa_id: int,
        unidade_id: int,
    ) -> Unidade | None:
        statement = select(Unidade).where(
            Unidade.empresa_id == empresa_id,
            Unidade.id == unidade_id,
        )

        return db.scalar(statement)

    @staticmethod
    def get_stock_balance(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> Decimal | None:
        item = MovimentacaoService._get_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
        )

        if item is None:
            return None

        signed_quantity = case(
            (
                Movimentacao.tipo.in_(TIPOS_ENTRADA),
                Movimentacao.quantidade,
            ),
            (
                Movimentacao.tipo.in_(TIPOS_SAIDA),
                -Movimentacao.quantidade,
            ),
            else_=Decimal("0.0000"),
        )

        statement = (
            select(
                func.coalesce(
                    func.sum(signed_quantity),
                    Decimal("0.0000"),
                )
            )
            .where(
                Movimentacao.empresa_id == empresa_id,
                Movimentacao.item_id == item_id,
            )
        )

        balance = db.scalar(statement)

        return Decimal(
            str(balance or "0")
        ).quantize(QUATRO_CASAS_DECIMAIS)

    @staticmethod
    def list_movements(
        db: Session,
        empresa_id: int,
        item_id: int,
    ) -> list[Movimentacao] | None:
        item = MovimentacaoService._get_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
        )

        if item is None:
            return None

        statement = (
            select(Movimentacao)
            .where(
                Movimentacao.empresa_id == empresa_id,
                Movimentacao.item_id == item_id,
            )
            .order_by(
                Movimentacao.ocorrida_em.desc(),
                Movimentacao.id.desc(),
            )
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def create_movement(
        db: Session,
        empresa_id: int,
        item_id: int,
        tipo: str,
        quantidade: Decimal,
        motivo: str | None = None,
        observacao: str | None = None,
        ocorrida_em: datetime | None = None,
    ) -> Movimentacao:
        if tipo not in TIPOS_MOVIMENTACAO:
            raise ValueError("Tipo de movimentação inválido.")

        quantidade = MovimentacaoService._validate_quantity(
            quantidade
        )

        if (
            ocorrida_em is not None
            and (
                ocorrida_em.tzinfo is None
                or ocorrida_em.utcoffset() is None
            )
        ):
            raise ValueError(
                "A data da movimentação deve incluir fuso horário."
            )

        # O bloqueio serializa as movimentações concorrentes do mesmo item.
        item = MovimentacaoService._get_item(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
            lock=True,
        )

        if item is None:
            raise ItemMovimentacaoNaoEncontradoError(
                "Item não encontrado nesta empresa."
            )

        if not item.ativo:
            raise ItemInativoError(
                "Não é permitido movimentar um item inativo."
            )

        InventarioService.ensure_item_not_in_open_inventory(
            db=db,
            empresa_id=empresa_id,
            item_id=item_id,
        )

        unit = MovimentacaoService._get_unit(
            db=db,
            empresa_id=empresa_id,
            unidade_id=item.unidade_id,
        )

        if unit is None:
            raise ItemMovimentacaoNaoEncontradoError(
                "A unidade do item não foi encontrada nesta empresa."
            )

        if (
            not unit.permite_decimal
            and quantidade != quantidade.to_integral_value()
        ):
            raise QuantidadeFracionariaError(
                "A unidade selecionada não permite quantidades "
                "fracionárias."
            )

        if tipo in TIPOS_SAIDA:
            saldo_atual = MovimentacaoService.get_stock_balance(
                db=db,
                empresa_id=empresa_id,
                item_id=item_id,
            )

            if saldo_atual is None or quantidade > saldo_atual:
                raise SaldoInsuficienteError(
                    "Saldo insuficiente para registrar esta saída."
                )

        normalized_reason = (
            motivo.strip() or None
            if motivo is not None
            else None
        )
        normalized_observation = (
            observacao.strip() or None
            if observacao is not None
            else None
        )

        values = {
            "empresa_id": empresa_id,
            "item_id": item_id,
            "tipo": tipo,
            "quantidade": quantidade,
            "motivo": normalized_reason,
            "observacao": normalized_observation,
        }

        # Se a data for omitida, o default do PostgreSQL será aplicado.
        if ocorrida_em is not None:
            values["ocorrida_em"] = ocorrida_em

        movement = Movimentacao(**values)

        db.add(movement)
        db.flush()

        return movement