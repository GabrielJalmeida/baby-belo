-- ============================================================
-- 009_create_view_estoque_baixo.sql
-- Itens ativos cujo saldo atingiu ou ficou abaixo do mínimo
-- ============================================================

CREATE OR REPLACE VIEW core.vw_itens_estoque_baixo AS
SELECT
    item_id,
    empresa_id,
    item_nome,
    unidade_id,
    unidade_nome,
    unidade_simbolo,
    estoque_minimo,
    saldo_atual
FROM core.vw_saldos_estoque
WHERE ativo = TRUE
  AND saldo_atual <= estoque_minimo;