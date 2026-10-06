-- ============================================================
-- 112_create_empresa_usuarios.sql
-- Relação entre usuários e empresas
-- ============================================================

CREATE TABLE auth.empresa_usuarios (
    empresa_id BIGINT NOT NULL,

    usuario_id BIGINT NOT NULL,

    papel VARCHAR(20) NOT NULL DEFAULT 'OPERATOR',

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_empresa_usuarios
    PRIMARY KEY (empresa_id, usuario_id),

    CONSTRAINT fk_empresa_usuarios_empresa
    FOREIGN KEY (empresa_id)
    REFERENCES core.empresas (id),

    CONSTRAINT fk_empresa_usuarios_usuario
    FOREIGN KEY (usuario_id)
    REFERENCES auth.usuarios (id),

    CONSTRAINT ck_empresa_usuarios_papel
    CHECK (papel IN ('OWNER', 'OPERATOR', 'VIEWER'))
);

CREATE INDEX idx_empresa_usuarios_usuario
ON auth.empresa_usuarios (usuario_id);