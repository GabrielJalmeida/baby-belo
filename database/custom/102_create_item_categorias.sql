CREATE TABLE custom.item_categorias (
    item_id BIGINT PRIMARY KEY,

    categoria_id BIGINT NOT NULL,

    empresa_id BIGINT NOT NULL,

    CONSTRAINT fk_item_categorias_item
        FOREIGN KEY (item_id)
        REFERENCES core.itens(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_item_categorias_categoria
        FOREIGN KEY (categoria_id)
        REFERENCES custom.categorias(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_item_categorias_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES core.empresas(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_item_categorias_categoria
    ON custom.item_categorias (categoria_id);

CREATE INDEX idx_item_categorias_empresa
    ON custom.item_categorias (empresa_id);