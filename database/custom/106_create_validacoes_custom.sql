-- ============================================================
-- 106_create_validacoes_custom.sql
-- Validações e proteções do módulo CUSTOM
-- ============================================================


-- ============================================================
-- 1. VALIDAR ITEM <-> CATEGORIA <-> EMPRESA
-- ============================================================

CREATE OR REPLACE FUNCTION custom.fn_validar_item_categoria()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_empresa_item BIGINT;
    v_empresa_categoria BIGINT;
BEGIN

    SELECT empresa_id
    INTO v_empresa_item
    FROM core.itens
    WHERE id = NEW.item_id;

    SELECT empresa_id
    INTO v_empresa_categoria
    FROM custom.categorias
    WHERE id = NEW.categoria_id;


    IF v_empresa_item IS NULL THEN
        RAISE EXCEPTION
            'O item % não existe.',
            NEW.item_id;
    END IF;


    IF v_empresa_categoria IS NULL THEN
        RAISE EXCEPTION
            'A categoria % não existe.',
            NEW.categoria_id;
    END IF;


    IF NEW.empresa_id <> v_empresa_item THEN
        RAISE EXCEPTION
            'A empresa informada não corresponde à empresa do item.';
    END IF;


    IF NEW.empresa_id <> v_empresa_categoria THEN
        RAISE EXCEPTION
            'A empresa informada não corresponde à empresa da categoria.';
    END IF;


    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validar_item_categoria
BEFORE INSERT OR UPDATE
ON custom.item_categorias
FOR EACH ROW
EXECUTE FUNCTION custom.fn_validar_item_categoria();


-- ============================================================
-- 1.1 BLOQUEAR RECATEGORIZACAO DE ITEM COM VALORES CUSTOM
-- ============================================================

CREATE OR REPLACE FUNCTION custom.fn_bloquear_recategorizacao_item()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF OLD.categoria_id IS DISTINCT FROM NEW.categoria_id
       AND EXISTS (
            SELECT 1
            FROM custom.valores_item
            WHERE item_id = OLD.item_id
       )
    THEN
        RAISE EXCEPTION
            'Nao e permitido alterar a categoria de um item que possui valores personalizados.';
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_bloquear_recategorizacao_item
BEFORE UPDATE
ON custom.item_categorias
FOR EACH ROW
EXECUTE FUNCTION custom.fn_bloquear_recategorizacao_item();

-- ============================================================
-- 2. VALIDAR EMPRESA DO CAMPO
-- ============================================================

CREATE OR REPLACE FUNCTION custom.fn_validar_campo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_empresa_categoria BIGINT;
BEGIN

    SELECT empresa_id
    INTO v_empresa_categoria
    FROM custom.categorias
    WHERE id = NEW.categoria_id;


    IF v_empresa_categoria IS NULL THEN
        RAISE EXCEPTION
            'A categoria % não existe.',
            NEW.categoria_id;
    END IF;


    IF NEW.empresa_id <> v_empresa_categoria THEN
        RAISE EXCEPTION
            'O campo e a categoria precisam pertencer à mesma empresa.';
    END IF;


    IF jsonb_typeof(NEW.configuracao) <> 'object' THEN
        RAISE EXCEPTION
            'A configuração do campo precisa ser um objeto JSON.';
    END IF;


    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validar_campo
BEFORE INSERT OR UPDATE
ON custom.campos
FOR EACH ROW
EXECUTE FUNCTION custom.fn_validar_campo();



-- ============================================================
-- 3. BLOQUEAR ALTERAÇÕES ESTRUTURAIS EM CAMPOS QUE JÁ POSSUEM
--    VALORES CADASTRADOS
-- ============================================================

CREATE OR REPLACE FUNCTION custom.fn_bloquear_alteracao_campo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF EXISTS (
        SELECT 1
        FROM custom.valores_item
        WHERE campo_id = OLD.id
    )
    AND (
        OLD.tipo_dado IS DISTINCT FROM NEW.tipo_dado
        OR OLD.categoria_id IS DISTINCT FROM NEW.categoria_id
        OR OLD.empresa_id IS DISTINCT FROM NEW.empresa_id
    )
    THEN
        RAISE EXCEPTION
            'Não é permitido alterar tipo, categoria ou empresa de um campo que já possui valores.';
    END IF;


    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_bloquear_alteracao_campo
BEFORE UPDATE
ON custom.campos
FOR EACH ROW
EXECUTE FUNCTION custom.fn_bloquear_alteracao_campo();



-- ============================================================
-- 4. GARANTIR QUE OPÇÕES SÓ SEJAM CRIADAS PARA CAMPOS LISTA
-- ============================================================

CREATE OR REPLACE FUNCTION custom.fn_validar_opcao_campo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo_dado VARCHAR(30);
BEGIN

    SELECT tipo_dado
    INTO v_tipo_dado
    FROM custom.campos
    WHERE id = NEW.campo_id;


    IF v_tipo_dado IS NULL THEN
        RAISE EXCEPTION
            'O campo % não existe.',
            NEW.campo_id;
    END IF;


    IF v_tipo_dado <> 'LISTA' THEN
        RAISE EXCEPTION
            'Somente campos do tipo LISTA podem possuir opções.';
    END IF;


    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validar_opcao_campo
BEFORE INSERT OR UPDATE
ON custom.campo_opcoes
FOR EACH ROW
EXECUTE FUNCTION custom.fn_validar_opcao_campo();



-- ============================================================
-- 5. VALIDAR VALORES PERSONALIZADOS DOS ITENS
-- ============================================================

CREATE OR REPLACE FUNCTION custom.fn_validar_valor_item()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_empresa_item BIGINT;

    v_empresa_campo BIGINT;
    v_categoria_campo BIGINT;
    v_tipo_dado VARCHAR(30);
    v_campo_ativo BOOLEAN;

    v_categoria_item BIGINT;

    v_opcao_campo BIGINT;
    v_opcao_ativa BOOLEAN;
BEGIN

    -- Descobre a empresa do item
    SELECT empresa_id
    INTO v_empresa_item
    FROM core.itens
    WHERE id = NEW.item_id;


    IF v_empresa_item IS NULL THEN
        RAISE EXCEPTION
            'O item % não existe.',
            NEW.item_id;
    END IF;


    -- Busca informações do campo
    SELECT
        empresa_id,
        categoria_id,
        tipo_dado,
        ativo
    INTO
        v_empresa_campo,
        v_categoria_campo,
        v_tipo_dado,
        v_campo_ativo
    FROM custom.campos
    WHERE id = NEW.campo_id;


    IF v_tipo_dado IS NULL THEN
        RAISE EXCEPTION
            'O campo % não existe.',
            NEW.campo_id;
    END IF;


    IF v_campo_ativo = FALSE THEN
        RAISE EXCEPTION
            'Não é possível cadastrar valor em um campo inativo.';
    END IF;


    -- Item e campo precisam pertencer à mesma empresa
    IF v_empresa_item <> v_empresa_campo THEN
        RAISE EXCEPTION
            'O item e o campo pertencem a empresas diferentes.';
    END IF;


    -- Descobre a categoria do item
    SELECT categoria_id
    INTO v_categoria_item
    FROM custom.item_categorias
    WHERE item_id = NEW.item_id;


    IF v_categoria_item IS NULL THEN
        RAISE EXCEPTION
            'O item precisa possuir uma categoria antes de receber campos personalizados.';
    END IF;


    -- Campo precisa pertencer à categoria do item
    IF v_categoria_item <> v_categoria_campo THEN
        RAISE EXCEPTION
            'O campo informado não pertence à categoria deste item.';
    END IF;


    -- Validação do tipo de valor
    CASE v_tipo_dado

        WHEN 'TEXTO_CURTO' THEN

            IF NEW.valor_texto IS NULL THEN
                RAISE EXCEPTION
                    'Campo TEXTO_CURTO precisa utilizar valor_texto.';
            END IF;


        WHEN 'TEXTO_LONGO' THEN

            IF NEW.valor_texto IS NULL THEN
                RAISE EXCEPTION
                    'Campo TEXTO_LONGO precisa utilizar valor_texto.';
            END IF;


        WHEN 'INTEIRO' THEN

            IF NEW.valor_inteiro IS NULL THEN
                RAISE EXCEPTION
                    'Campo INTEIRO precisa utilizar valor_inteiro.';
            END IF;


        WHEN 'DECIMAL' THEN

            IF NEW.valor_decimal IS NULL THEN
                RAISE EXCEPTION
                    'Campo DECIMAL precisa utilizar valor_decimal.';
            END IF;


        WHEN 'DINHEIRO' THEN

            IF NEW.valor_monetario IS NULL THEN
                RAISE EXCEPTION
                    'Campo DINHEIRO precisa utilizar valor_monetario.';
            END IF;


        WHEN 'BOOLEANO' THEN

            IF NEW.valor_booleano IS NULL THEN
                RAISE EXCEPTION
                    'Campo BOOLEANO precisa utilizar valor_booleano.';
            END IF;


        WHEN 'DATA' THEN

            IF NEW.valor_data IS NULL THEN
                RAISE EXCEPTION
                    'Campo DATA precisa utilizar valor_data.';
            END IF;


        WHEN 'LISTA' THEN

            IF NEW.opcao_id IS NULL THEN
                RAISE EXCEPTION
                    'Campo LISTA precisa utilizar opcao_id.';
            END IF;


            SELECT
                campo_id,
                ativo
            INTO
                v_opcao_campo,
                v_opcao_ativa
            FROM custom.campo_opcoes
            WHERE id = NEW.opcao_id;


            IF v_opcao_campo IS NULL THEN
                RAISE EXCEPTION
                    'A opção % não existe.',
                    NEW.opcao_id;
            END IF;


            IF v_opcao_campo <> NEW.campo_id THEN
                RAISE EXCEPTION
                    'A opção escolhida não pertence ao campo informado.';
            END IF;


            IF v_opcao_ativa = FALSE THEN
                RAISE EXCEPTION
                    'Não é possível utilizar uma opção inativa.';
            END IF;

    END CASE;


    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validar_valor_item
BEFORE INSERT OR UPDATE
ON custom.valores_item
FOR EACH ROW
EXECUTE FUNCTION custom.fn_validar_valor_item();



-- ============================================================
-- 6. ÍNDICES DO MÓDULO CUSTOM
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_categorias_empresa_ativo
    ON custom.categorias (empresa_id, ativo);


CREATE INDEX IF NOT EXISTS idx_campos_categoria_ativo
    ON custom.campos (categoria_id, ativo);


CREATE INDEX IF NOT EXISTS idx_valores_item_item
    ON custom.valores_item (item_id);


CREATE INDEX IF NOT EXISTS idx_valores_item_campo
    ON custom.valores_item (campo_id);