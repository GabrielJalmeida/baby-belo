\set ON_ERROR_STOP on

-- ============================================================
-- Estoque Flex
-- Instalacao completa do banco
-- ============================================================

\echo 'Aplicando CORE...'

\ir core/001_create_schemas.sql
\ir core/002_create_empresas.sql
\ir core/003_create_unidades.sql
\ir core/004_create_itens.sql
\ir core/005_create_movimentacoes.sql
\ir core/006_create_inventarios.sql
\ir core/007_create_inventario_itens.sql
\ir core/008_create_view_saldos.sql
\ir core/009_create_view_estoque_baixo.sql

\echo 'Aplicando CUSTOM...'

\ir custom/100_create_custom_schema.sql
\ir custom/101_create_categorias.sql
\ir custom/102_create_item_categorias.sql
\ir custom/103_create_campos.sql
\ir custom/104_create_campo_opcoes.sql
\ir custom/105_create_valores_item.sql
\ir custom/106_create_validacoes_custom.sql

\echo 'Estoque Flex: schema aplicado com sucesso.'