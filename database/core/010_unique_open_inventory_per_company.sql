
-- ============================================================
-- 010_unique_open_inventory_per_company.sql
-- Garante no banco no máximo um inventário aberto por empresa.
-- Seguro para reexecução quando o índice já existe.
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_inventarios_empresa_aberto
    ON core.inventarios (empresa_id)
    WHERE status = 'ABERTO';
