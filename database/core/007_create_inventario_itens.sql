-- ============================================================
-- 007_create_inventario_itens.sql
-- Itens contados em um inventário físico
-- ============================================================

CREATE TABLE core.inventario_itens (
    inventario_id BIGINT NOT NULL,

    empresa_id BIGINT NOT NULL,

    item_id BIGINT NOT NULL,

    saldo_sistema NUMERIC(18,4) NOT NULL,

    quantidade_contada NUMERIC(18,4),

    diferenca NUMERIC(18,4)
        GENERATED ALWAYS AS (
            quantidade_contada - saldo_sistema
        ) STORED,

    contado_em TIMESTAMPTZ,

    PRIMARY KEY (inventario_id, item_id),

    CONSTRAINT fk_inventario_itens_inventario_empresa
        FOREIGN KEY (empresa_id, inventario_id)
        REFERENCES core.inventarios(empresa_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_inventario_itens_item_empresa
        FOREIGN KEY (empresa_id, item_id)
        REFERENCES core.itens(empresa_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_inventario_itens_quantidade_contada
        CHECK (
            quantidade_contada IS NULL
            OR quantidade_contada >= 0
        ),

    CONSTRAINT ck_inventario_itens_contagem_data
        CHECK (
            (
                quantidade_contada IS NULL
                AND contado_em IS NULL
            )
            OR
            (
                quantidade_contada IS NOT NULL
                AND contado_em IS NOT NULL
            )
        )
);

CREATE INDEX idx_inventario_itens_item
    ON core.inventario_itens (item_id);