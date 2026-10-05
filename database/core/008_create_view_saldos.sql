-- ============================================================
-- 008_create_view_saldos.sql
-- Saldo atual dos itens calculado pelo histórico
-- ============================================================

CREATE OR REPLACE VIEW core.vw_saldos_estoque AS
SELECT
    i.id AS item_id,
    i.empresa_id,
    i.nome AS item_nome,
    i.unidade_id,
    u.nome AS unidade_nome,
    u.simbolo AS unidade_simbolo,
    i.estoque_minimo,
    i.ativo,

    COALESCE(
        SUM(
            CASE
                WHEN m.tipo IN ('ENTRADA', 'AJUSTE_ENTRADA')
                    THEN m.quantidade

                WHEN m.tipo IN ('SAIDA', 'AJUSTE_SAIDA')
                    THEN -m.quantidade

                ELSE 0
            END
        ),
        0
    )::NUMERIC(18,4) AS saldo_atual

FROM core.itens i

INNER JOIN core.unidades u
    ON u.id = i.unidade_id
    AND u.empresa_id = i.empresa_id

LEFT JOIN core.movimentacoes m
    ON m.item_id = i.id
    AND m.empresa_id = i.empresa_id

GROUP BY
    i.id,
    i.empresa_id,
    i.nome,
    i.unidade_id,
    u.nome,
    u.simbolo,
    i.estoque_minimo,
    i.ativo;