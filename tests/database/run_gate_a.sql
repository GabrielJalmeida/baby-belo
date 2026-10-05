\set ON_ERROR_STOP on

\echo '============================================'
\echo ' ESTOQUE FLEX - GATE A'
\echo ' Testes automatizados do banco'
\echo '============================================'

-- Banco exclusivo de testes.
-- Nunca executar no banco de desenvolvimento.

DROP SCHEMA IF EXISTS custom CASCADE;
DROP SCHEMA IF EXISTS core CASCADE;

\ir ../../database/apply_all.sql

BEGIN;

-- ============================================================
-- SEED CORE
-- ============================================================

INSERT INTO core.empresas (nome)
VALUES
    ('Empresa A'),
    ('Empresa B');

INSERT INTO core.unidades (
    empresa_id,
    nome,
    simbolo,
    permite_decimal
)
VALUES
    (1, 'Unidade', 'un', FALSE),
    (2, 'Unidade', 'un', FALSE),
    (1, 'Caixa', 'cx', FALSE);

INSERT INTO core.itens (
    empresa_id,
    unidade_id,
    nome,
    estoque_minimo
)
VALUES
    (1, 1, 'Produto A', 0.5),
    (1, 1, 'Produto Estoque Baixo', 10),
    (2, 2, 'Produto B', 0);

INSERT INTO core.movimentacoes (
    empresa_id,
    item_id,
    tipo,
    quantidade
)
VALUES
    (1, 1, 'ENTRADA', 10),
    (1, 1, 'SAIDA', 3.5),
    (1, 1, 'AJUSTE_SAIDA', 0.5);

-- ============================================================
-- TESTE 1 - SALDO
-- ============================================================

DO $$
DECLARE
    v_saldo NUMERIC(18,4);
BEGIN
    SELECT saldo_atual
    INTO v_saldo
    FROM core.vw_saldos_estoque
    WHERE item_id = 1;

    IF v_saldo <> 6.0000 THEN
        RAISE EXCEPTION
            'TESTE FALHOU: saldo esperado 6.0000, recebido %',
            v_saldo;
    END IF;
END;
$$;

-- ============================================================
-- TESTE 2 - ESTOQUE BAIXO
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM core.vw_itens_estoque_baixo
        WHERE item_id = 2
          AND saldo_atual = 0
          AND estoque_minimo = 10
    ) THEN
        RAISE EXCEPTION
            'TESTE FALHOU: item com estoque baixo nao encontrado.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 3 - MOVIMENTO ZERO DEVE FALHAR
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO core.movimentacoes (
            empresa_id,
            item_id,
            tipo,
            quantidade
        )
        VALUES (1, 1, 'ENTRADA', 0);

    EXCEPTION
        WHEN check_violation THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: movimento com quantidade zero foi aceito.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 4 - ITEM NAO PODE USAR UNIDADE DE OUTRA EMPRESA
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO core.itens (
            empresa_id,
            unidade_id,
            nome
        )
        VALUES (
            1,
            2,
            'Item Invalido'
        );

    EXCEPTION
        WHEN foreign_key_violation THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: mistura entre empresas foi aceita.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 4.1 - ITEM COM MOVIMENTOS NAO TROCA UNIDADE
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        UPDATE core.itens
        SET unidade_id = 3
        WHERE id = 1;

    EXCEPTION
        WHEN raise_exception THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: item com movimentacoes trocou de unidade.';
    END IF;
END;
$$;

-- ============================================================
-- SEED CUSTOM
-- ============================================================

INSERT INTO custom.categorias (
    empresa_id,
    nome
)
VALUES
    (1, 'Eletronicos'),
    (1, 'Alimentos'),
    (2, 'Categoria B');

INSERT INTO custom.item_categorias (
    item_id,
    categoria_id,
    empresa_id
)
VALUES (
    1,
    1,
    1
);

INSERT INTO custom.campos (
    empresa_id,
    categoria_id,
    nome,
    tipo_dado,
    ativo
)
VALUES
    (1, 1, 'Marca', 'TEXTO_CURTO', TRUE),
    (1, 1, 'Tamanho', 'LISTA', TRUE),
    (1, 1, 'Cor', 'LISTA', TRUE),
    (1, 1, 'Modelo Inativo', 'TEXTO_CURTO', FALSE),
    (1, 1, 'Quantidade por caixa', 'INTEIRO', TRUE),
    (2, 3, 'Marca B', 'TEXTO_CURTO', TRUE);

INSERT INTO custom.campo_opcoes (
    campo_id,
    valor
)
VALUES
    (2, 'Grande'),
    (3, 'Azul');

INSERT INTO custom.valores_item (
    item_id,
    campo_id,
    valor_texto
)
VALUES (
    1,
    1,
    'Marca Teste'
);

INSERT INTO custom.valores_item (
    item_id,
    campo_id,
    opcao_id
)
VALUES (
    1,
    2,
    1
);

-- ============================================================
-- TESTE 5 - RECATEGORIZACAO DEVE FALHAR
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        UPDATE custom.item_categorias
        SET categoria_id = 2
        WHERE item_id = 1;

    EXCEPTION
        WHEN raise_exception THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: item com valores CUSTOM foi recategorizado.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 6 - OPCAO DE OUTRO CAMPO DEVE FALHAR
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO custom.valores_item (
            item_id,
            campo_id,
            opcao_id
        )
        VALUES (
            1,
            3,
            1
        );

    EXCEPTION
        WHEN raise_exception THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: opcao de outro campo foi aceita.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 7 - CAMPO INATIVO DEVE FALHAR
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO custom.valores_item (
            item_id,
            campo_id,
            valor_texto
        )
        VALUES (
            1,
            4,
            'Teste'
        );

    EXCEPTION
        WHEN raise_exception THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: campo inativo recebeu valor.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 8 - ITEM SEM CATEGORIA DEVE FALHAR
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO custom.valores_item (
            item_id,
            campo_id,
            valor_texto
        )
        VALUES (
            3,
            6,
            'Teste'
        );

    EXCEPTION
        WHEN raise_exception THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: item sem categoria recebeu CUSTOM.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 9 - EXATAMENTE UM VALOR
-- ============================================================

DO $$
DECLARE
    v_bloqueado BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO custom.valores_item (
            item_id,
            campo_id,
            valor_texto,
            valor_inteiro
        )
        VALUES (
            1,
            5,
            'Invalido',
            10
        );

    EXCEPTION
        WHEN check_violation THEN
            v_bloqueado := TRUE;
    END;

    IF NOT v_bloqueado THEN
        RAISE EXCEPTION
            'TESTE FALHOU: dois valores simultaneos foram aceitos.';
    END IF;
END;
$$;

-- ============================================================
-- TESTE 10 - INVENTARIO E DIFERENCA
-- ============================================================

INSERT INTO core.inventarios (
    empresa_id,
    observacao
)
VALUES (
    1,
    'Inventario automatizado'
);

INSERT INTO core.inventario_itens (
    inventario_id,
    empresa_id,
    item_id,
    saldo_sistema
)
SELECT
    1,
    empresa_id,
    item_id,
    saldo_atual
FROM core.vw_saldos_estoque
WHERE item_id = 1;

UPDATE core.inventario_itens
SET
    quantidade_contada = 5.5,
    contado_em = CURRENT_TIMESTAMP
WHERE inventario_id = 1
  AND item_id = 1;


DO $$
DECLARE
    v_diferenca NUMERIC(18,4);
BEGIN

    SELECT diferenca
    INTO v_diferenca
    FROM core.inventario_itens
    WHERE inventario_id = 1
      AND item_id = 1;

    IF v_diferenca <> -0.5000 THEN
        RAISE EXCEPTION
            'TESTE FALHOU: diferenca esperada -0.5000, recebida %',
            v_diferenca;
    END IF;

END;
$$;


-- ============================================================
-- TESTE 11 - CONCLUSAO DO INVENTARIO GERA AJUSTE
-- ============================================================

INSERT INTO core.movimentacoes (
    empresa_id,
    item_id,
    tipo,
    quantidade,
    motivo
)
SELECT
    empresa_id,
    item_id,
    CASE
        WHEN diferenca > 0 THEN 'AJUSTE_ENTRADA'
        ELSE 'AJUSTE_SAIDA'
    END,
    ABS(diferenca),
    'Ajuste de inventario automatizado'
FROM core.inventario_itens
WHERE inventario_id = 1
  AND diferenca <> 0;

UPDATE core.inventarios
SET
    status = 'CONCLUIDO',
    concluido_em = CURRENT_TIMESTAMP
WHERE id = 1;


DO $$
DECLARE
    v_saldo NUMERIC(18,4);
    v_status VARCHAR(20);
BEGIN

    SELECT saldo_atual
    INTO v_saldo
    FROM core.vw_saldos_estoque
    WHERE item_id = 1;

    IF v_saldo <> 5.5000 THEN
        RAISE EXCEPTION
            'TESTE FALHOU: saldo apos inventario esperado 5.5000, recebido %',
            v_saldo;
    END IF;

    SELECT status
    INTO v_status
    FROM core.inventarios
    WHERE id = 1;

    IF v_status <> 'CONCLUIDO' THEN
        RAISE EXCEPTION
            'TESTE FALHOU: inventario nao foi concluido.';
    END IF;

END;
$$;

ROLLBACK;

\echo '============================================'
\echo ' GATE A: TODOS OS TESTES PASSARAM'
\echo '============================================'