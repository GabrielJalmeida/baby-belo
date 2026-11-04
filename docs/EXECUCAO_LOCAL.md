# Executar o Baby Belo localmente

O repositório do colega contém o backend e os scripts SQL, mas não contém o banco anterior nem as credenciais. Foi preparado um ambiente **novo e local**, sem importar ou inventar dados de estoque.

## Iniciar

Abra PowerShell na raiz do projeto e execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Abra **http://127.0.0.1:5174/** e clique em **Acessar Estoque**.

Na primeira execução, crie sua própria conta em outro terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/create-owner.ps1
```

O utilitário original pedirá seu nome, e-mail, nome da empresa e senha (sem exibi-la). Informe **Baby Belo Ateliê** como empresa. Depois use o e-mail e a senha escolhidos no login. O frontend seleciona somente o vínculo Baby Belo autorizado pelo backend; nunca usa uma identificação fixa de empresa.

## O que está configurado

- Python 3.13 instalado para o usuário; dependências do backend em `.venv`.
- FastAPI, SQLAlchemy e autenticação JWT existentes, sem alterações no código do backend.
- PostgreSQL portátil 18.6, obtido pelo pacote `embedded-postgres@18.6.0-beta.19`, usado apenas neste ambiente local. Nenhum serviço do Windows foi instalado.
- Banco acessível somente em `127.0.0.1:55432`; API em `127.0.0.1:8000`; frontend em `127.0.0.1:5174`.
- `baby_belo_dev`: banco de uso, iniciado vazio.
- `baby_belo_test` e `baby_belo_auth_test`: bancos isolados de testes, com dados descartáveis.
- Senha do banco e chave JWT aleatórias, guardadas em `.local/config.json`, ignorado pelo Git. Os scripts passam a configuração por variáveis do processo; nenhum arquivo de produção foi alterado.
- Dados persistentes em `.local/postgres`. Não apague essa pasta nem publique/compartilhe `.local`, `.venv` ou arquivos de configuração com segredos.

Os scripts SQL originais são aplicados somente quando um banco novo é criado. Reiniciar o ambiente não recria tabelas nem apaga dados.

## Inicialização em terminais separados

Se preferir acompanhar os serviços e encerrá-los com Ctrl+C:

```powershell
node scripts/local-db.mjs
```

Em outro terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-api.ps1
```

Em um terceiro terminal:

```powershell
cd frontend
npm run dev
```

Não inicie uma segunda instância na mesma porta. O atalho `start-local.ps1` reaproveita serviços já iniciados; quando inicia novos processos, eles ficam em segundo plano e os logs ficam em `.local`.

## Testes

Com o PostgreSQL local iniciado, na raiz:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-backend.ps1
.\.venv\Scripts\python.exe scripts/test-live.py
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

O script de testes do backend define `DATABASE_URL` e `TEST_AUTH_DATABASE_URL` para os dois bancos isolados. **Não execute a suíte apontando para o banco de uso ou para produção**, pois os testes cadastram, alteram e removem registros.

A verificação HTTP usa os serviços reais do frontend contra uma API temporária e PostgreSQL, cobrindo autenticação, permissões, isolamento, CRUD disponível, estoque e persistência. Ela não substitui a criação da sua conta pessoal.

## Preparar novamente após baixar o projeto em outra máquina

É necessário Node.js/npm e Python 3.13. A partir da raiz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm --prefix frontend ci
npm install --prefix .local --no-audit --no-fund embedded-postgres@18.6.0-beta.19
node scripts/local-db.mjs
```

O primeiro início gera novas credenciais locais e novos bancos. Em seguida, inicie a API e crie sua conta conforme as instruções anteriores. O pacote PostgreSQL é uma dependência de conveniência local; uma instalação PostgreSQL convencional também pode usar os mesmos scripts SQL e o mecanismo de configuração existente do backend.

## Pendências de conteúdo

O banco original do colega não foi disponibilizado. Para recuperar produtos e histórico anteriores, será necessário obter um backup com ele; o ambiente atual começa vazio. Também faltam as imagens originais e a identificação das fontes do Figma para máxima fidelidade visual. Nada foi publicado na Render ou em outro serviço.
