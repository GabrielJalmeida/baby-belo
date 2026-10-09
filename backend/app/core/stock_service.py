
from sqlalchemy import text
from sqlalchemy.orm import Session


class StockService:
    @staticmethod
    def list_balances(
        db: Session,
        empresa_id: int,
    ) -> list[dict]:
        statement = text(
            """
            SELECT
                item_id,
                empresa_id,
                item_nome,
                unidade_id,
                unidade_nome,
                unidade_simbolo,
                estoque_minimo,
                ativo,
                saldo_atual
            FROM core.vw_saldos_estoque
            WHERE empresa_id = :empresa_id
            ORDER BY item_id
            """
        )

        result = db.execute(
            statement,
            {"empresa_id": empresa_id},
        )

        return [
            dict(row._mapping)
            for row in result
        ]

    @staticmethod
    def list_low_stock(
        db: Session,
        empresa_id: int,
    ) -> list[dict]:
        statement = text(
            """
            SELECT
                item_id,
                empresa_id,
                item_nome,
                unidade_id,
                unidade_nome,
                unidade_simbolo,
                estoque_minimo,
                saldo_atual
            FROM core.vw_itens_estoque_baixo
            WHERE empresa_id = :empresa_id
            ORDER BY item_id
            """
        )

        result = db.execute(
            statement,
            {"empresa_id": empresa_id},
        )

        return [
            dict(row._mapping)
            for row in result
        ]