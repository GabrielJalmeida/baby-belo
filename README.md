<p align="center">
  <img src="docs/assets/estoque-flex-hero.svg" alt="Estoque Flex — controle confiável, estrutura flexível" width="100%" />
</p>

<p align="center">
  <strong>Controle de estoque confiável, com estrutura preparada para diferentes negócios.</strong><br />
  API modular · Multiempresa · Campos personalizados · Frontend React
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-FastAPI-3776AB?style=for-the-badge&logo=fastapi&logoColor=white" alt="Python e FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Testes-468%20passed-22C55E?style=for-the-badge&logo=pytest&logoColor=white" alt="468 testes aprovados na última execução local" />
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="Frontend React e Vite" />
</p>

<p align="center">
  <a href="#visão-geral">Visão geral</a> ·
  <a href="#capacidades">Capacidades</a> ·
  <a href="#arquitetura">Arquitetura</a> ·
  <a href="#executar-localmente">Executar localmente</a> ·
  <a href="#estado-atual-e-roadmap">Estado e roadmap</a>
</p>

---

## Visão geral

O **Estoque Flex** é um sistema web de gerenciamento de estoque multiempresa, pensado para negócios que precisam de rastreabilidade sem abrir mão da flexibilidade. O núcleo mantém as regras operacionais do estoque, enquanto uma camada configurável permite que cada empresa descreva seus itens sem criar colunas específicas para cada negócio.

> **CORE controla o estoque. CUSTOM descreve o estoque. AUTH protege o acesso.**

O projeto possui uma API em FastAPI e uma interface web inicial em React/Vite. A interface já foi integrada aos principais fluxos implementados e passou por validações locais. Este README registra o estado conhecido em **13/10/2026**. A publicação na internet, a migração de uma cópia do banco para um ambiente de testes e a validação E2E completa ainda estão pendentes.

## Capacidades

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>📦 CORE</h3>
      <p>Regras operacionais e dados estruturados.</p>
      <ul>
        <li>Empresas e unidades de medida</li>
        <li>Cadastro, consulta e atualização de itens</li>
        <li>Ativação e inativação de itens e unidades</li>
        <li>Registro de entradas, saídas e ajustes</li>
        <li>Consulta de saldos e estoque baixo</li>
        <li>Inventários, contagens e conclusão/cancelamento</li>
        <li>Histórico de movimentações por item</li>
      </ul>
    </td>
    <td width="33%" valign="top">
      <h3>🧩 CUSTOM</h3>
      <p>Personalização sem acoplamento inverso ao núcleo.</p>
      <ul>
        <li>Categorias por empresa</li>
        <li>Campos personalizados por categoria</li>
        <li>Opções para campos do tipo lista</li>
        <li>Valores personalizados por item</li>
        <li>Associação de itens a categorias</li>
        <li>Validação da configuração JSON e limites de texto</li>
      </ul>
    </td>
    <td width="33%" valign="top">
      <h3>🔐 AUTH</h3>
      <p>Identidade, contexto e permissões.</p>
      <ul>
        <li>Login com JWT</li>
        <li>Consulta do usuário autenticado</li>
        <li>Contexto empresarial por <code>X-Company-ID</code></li>
        <li>Papéis OWNER, OPERATOR e VIEWER</li>
        <li>Validação de acesso no backend</li>
        <li>Separação de dados entre empresas</li>
      </ul>
    </td>
  </tr>
</table>

### Interface web

A primeira versão do frontend utiliza React, Vite e JavaScript. Ela já contempla os fluxos de interface desenvolvidos para autenticação/contexto, itens, unidades, movimentações, detalhes e configurações de campos personalizados, além de controles de interface orientados por permissões.

O frontend é uma base funcional de MVP, não uma declaração de que todos os fluxos administrativos ou requisitos de produção já estejam concluídos. A gestão global de empresas e o fluxo completo para um OWNER criar e administrar contas de funcionários ainda precisam ser planejados e implementados.

## Arquitetura

O backend segue uma arquitetura de **monólito modular**: módulos separados por domínio, uma API HTTP e uma camada de aplicação para coordenar operações que atravessam módulos.

```mermaid
flowchart TD
    CLIENT[Frontend / cliente HTTP] --> ROUTER[FastAPI · Routers]
    ROUTER --> SCHEMA[Pydantic · Schemas]
    SCHEMA --> SERVICE[Services · Regras de negócio]
    SERVICE --> ORM[SQLAlchemy 2.x]
    ORM --> DB[(PostgreSQL)]
```

### Direção das dependências

```mermaid
flowchart BT
    CUSTOM[CUSTOM] --> CORE[CORE]
    AUTH[AUTH] --> CORE
    APP[APPLICATION · orquestração] --> CORE
    APP --> AUTH
    CORE --> DB[(PostgreSQL)]
    AUTH --> DB
    CUSTOM --> DB
```

A direção é intencional: **CORE não importa AUTH nem CUSTOM**. Operações que exigem coordenação entre domínios ficam na camada `application`. CUSTOM pode depender de CORE, mas o inverso é proibido.

### Princípios de domínio

- **Saldo rastreável:** movimentações sustentam as consultas de saldo; o saldo não é um campo manualmente editável no item.
- **Precisão decimal:** quantidades operacionais usam precisão compatível com `NUMERIC(18,4)`.
- **Histórico preservado:** movimentações não devem ser apagadas para ocultar erros operacionais.
- **Multiempresa:** consultas e mutações protegidas devem respeitar a empresa do contexto e validar os registros relacionados.
- **Integridade de estoque:** saídas são validadas contra o saldo e as regras do domínio; há teste automatizado para um cenário crítico de concorrência.
- **CUSTOM sem acoplamento inverso:** campos configuráveis estendem o núcleo sem fazer CORE depender de CUSTOM.
- **PATCH previsível:** campos omitidos não devem ser alterados; a nulabilidade segue o contrato do schema.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| API | Python, FastAPI, Pydantic |
| Persistência | SQLAlchemy 2.x, PostgreSQL, scripts SQL do projeto |
| Autenticação | JWT/PyJWT, Argon2 |
| Testes de backend | pytest, FastAPI TestClient e cliente HTTP de testes |
| Frontend | React, Vite, JavaScript, CSS |
| Ferramentas de desenvolvimento | Python, Node.js/npm, VS Code |

## Qualidade e status

| Área | Estado | Observação |
|---|---|---|
| Banco local / Gate A | ✅ Concluído | Estruturas CORE, AUTH e CUSTOM aplicadas e validadas no ambiente de desenvolvimento. |
| Fundação do backend | ✅ Implementada | FastAPI, configuração, persistência, segurança e testes. |
| AUTH e multiempresa | ✅ Implementados | JWT, usuário atual, membership, papéis e contexto empresarial. |
| APIs CORE | ✅ Implementadas | Empresas, unidades, itens, movimentações, estoque e inventários. |
| API CUSTOM | ✅ Implementada | Categorias, campos, opções, valores e associação com itens. |
| Paginação | ✅ Implementada nas listas selecionadas | Limites e offsets validados; consulte a OpenAPI para o contrato de cada rota. |
| Limites de texto | ✅ Implementados | Texto curto: 255; texto longo: 10.000; descrições: 2.000; observações: 5.000 caracteres. |
| Configuração de campos | ✅ Validada | Objeto JSON serializado limitado a 16 KiB, validado no schema e no serviço. |
| Concorrência de saídas | ✅ Testada | Teste de regressão verifica que duas saídas incompatíveis não deixam o saldo negativo. |
| Frontend React/Vite | ✅ Implementado em nível de MVP | Lint, build e testes manuais registrados como aprovados. |
| Suíte de backend | ✅ 468 testes aprovados | Última execução local registrada: `468 passed in 19.56s`. |
| Lint e build do frontend | ✅ Aprovados | `npm run lint` e `npm run build` concluídos sem erros na última validação registrada. |
| Publicação na internet | ⏳ Pendente | Ambiente do backend, frontend e variáveis de implantação ainda precisam ser configurados. |
| Banco remoto para testes | ⏳ Em preparação | Projeto criado no Neon; exportação/importação dos dados locais ainda não realizada. |
| Testes E2E | ⏳ Pendente | Validar os fluxos principais de ponta a ponta. |
| Administração global e contas de funcionários | ⏳ Planejado | Não tratar como funcionalidade já concluída. |

> **Nota sobre prontidão:** o hardening preventivo desta fase foi encerrado para permitir que o MVP avance. Isso não significa que todas as condições de produção estejam resolvidas. Problemas concretos de contrato, permissão, integridade ou consistência devem ser reproduzidos e corrigidos com testes de regressão.

Os números acima registram execuções locais informadas durante o desenvolvimento; não representam, por si só, um status de CI/CD remoto.

## Organização do repositório

```text
.
├── backend/
│   ├── app/
│   │   ├── application/   # Orquestração entre domínios
│   │   ├── auth/          # Autenticação e autorização
│   │   ├── core/          # Regras fundamentais do estoque
│   │   ├── custom/        # Categorias e campos configuráveis
│   │   ├── health/        # Health check
│   │   └── shared/        # Configuração, banco e utilitários comuns
│   ├── tests/             # Testes de serviços e APIs
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/               # Interface React e cliente da API
│   └── package.json
├── database/
│   ├── core/
│   ├── auth/
│   ├── custom/
│   └── apply_all.sql      # Aplicação em banco novo
├── docs/
│   └── assets/            # Recursos visuais da documentação
├── pytest.ini
└── README.md
```

A árvore é resumida; consulte os diretórios para ver todos os arquivos existentes.

## Executar localmente

Este guia descreve uma instalação local nova no Windows usando CMD, Python, PostgreSQL e Node.js. Siga os passos na ordem. Não use os bancos de produção para testes.

### Pré-requisitos

Instale Git, Python, PostgreSQL, Node.js e npm. O comando `psql` precisa estar disponível no CMD e o serviço PostgreSQL deve estar em execução.

### 1. Clonar o repositório e abrir no VS Code

```bat
git clone https://github.com/GabrielJalmeida/baby-belo.git
cd baby-belo
code .
```

`code .` abre a pasta atual no VS Code. Se o CMD informar que `code` não é reconhecido, abra o VS Code manualmente e selecione **Arquivo → Abrir Pasta**; escolha a pasta `baby-belo` criada pelo clone.

### 2. Criar o ambiente Python

Execute na raiz do repositório:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend\requirements.txt
```

Confirme que `(.venv)` aparece no começo da linha do terminal. Se abrir outro terminal, ative novamente com `.venv\Scripts\activate` antes de executar comandos Python.

### 3. Criar e configurar o arquivo `.env`

Na raiz do projeto, execute:

```bat
copy backend\.env.example backend\.env
code backend\.env
```

O segundo comando abre o arquivo local para edição. **Não compartilhe nem publique `backend\.env`**: ele contém credenciais privadas.

Configure `DATABASE_URL` com os dados do seu PostgreSQL local. No exemplo abaixo, `postgres` é o usuário e `password` é apenas um valor fictício:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/estoque_flex_dev
TEST_AUTH_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/estoque_flex_auth_test
```

Substitua `password` pela senha real do usuário PostgreSQL. É a senha que você digita quando o comando `psql -U postgres ...` solicita `Senha para o usuário postgres`. Mantenha o mesmo usuário e senha nas duas URLs, alterando o nome do banco ao final de cada uma.

Se sua instalação usa outro usuário, porta ou host, ajuste esses campos. Se a senha tiver caracteres reservados em uma URL, como `@`, `:`, `/`, `#` ou `%`, codifique-os em formato URL.

`SECRET_KEY` também é obrigatória. Gere uma chave aleatória executando no terminal:

```bat
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o resultado e substitua o valor ilustrativo de `SECRET_KEY` no `backend\.env`. Não use o texto de exemplo como chave real. Para uso local, mantenha `CORS_ALLOWED_ORIGINS` com as origens `localhost:5173` e `127.0.0.1:5173`.

### 4. Criar os bancos locais

As URLs de exemplo usam dois bancos: um para a aplicação e outro exclusivo dos testes de autenticação. Crie-os no PostgreSQL:

```bat
psql -U postgres -d postgres -c "CREATE DATABASE estoque_flex_dev;"
psql -U postgres -d postgres -c "CREATE DATABASE estoque_flex_auth_test;"
```

Se o CMD informar que um banco já existe, **não o apague nem recrie sem verificar seus dados**. Para fazer uma instalação de validação no mesmo computador, escolha nomes novos, por exemplo `estoque_flex_validacao` e `estoque_flex_auth_validacao`; altere o nome final em cada URL no `.env` e use exatamente esses mesmos nomes nos comandos de criação e instalação a seguir.

Se seu usuário PostgreSQL não for `postgres`, adapte os comandos à sua instalação.

### 5. Aplicar o schema nos dois bancos

Na raiz do repositório, aplique os scripts no banco principal:

```bat
psql -h localhost -p 5432 -U postgres -d estoque_flex_dev -v ON_ERROR_STOP=1 -f database\apply_all.sql
```

Depois aplique a estrutura no banco auxiliar de testes:

```bat
psql -h localhost -p 5432 -U postgres -d estoque_flex_auth_test -v ON_ERROR_STOP=1 -f database\apply_all.sql
```

Se você escolheu nomes alternativos no passo anterior, substitua `estoque_flex_dev` e `estoque_flex_auth_test` pelos nomes configurados nas duas URLs.

A mensagem esperada ao final de cada comando é `Estoque Flex: schema aplicado com sucesso.` O script cria estruturas CORE, AUTH e CUSTOM, incluindo tabelas, relacionamentos, restrições, índices, funções e gatilhos.

**Não execute `database\apply_all.sql` novamente em um banco já instalado sem avaliar antes seu estado.** Esse script prepara um banco novo; não é um sistema geral de migrações.

### 6. Executar os testes do backend

Com `(.venv)` ativo, execute na raiz do repositório:

```bat
python -m pytest backend\tests -q
```

A suíte valida serviços, endpoints, autenticação, isolamento entre empresas, integridade do banco e concorrência. Execute-a somente contra bancos locais dedicados a desenvolvimento/testes, nunca contra produção. Alguns testes criam dados temporários e a limpeza de cenários de teste desativa temporariamente gatilhos de proteção dentro da transação de limpeza.

### 7. Criar a primeira conta para entrar no sistema

O frontend não oferece cadastro público de usuário. Depois de instalar o banco e executar os testes, crie a primeira conta local usando o utilitário de inicialização:

```bat
python backend\create_initial_user.py
```

Informe o nome, e-mail, nome da primeira empresa e uma senha. A senha é solicitada sem aparecer na tela. O utilitário cria o usuário com hash de senha, cria a primeira empresa e associa o usuário a ela com o papel `OWNER`.

Por segurança, o utilitário funciona apenas quando `DATABASE_URL` aponta para um PostgreSQL local. Se já houver usuários no banco, ele informa a quantidade encontrada e solicita uma confirmação. Digite `CRIAR` somente se o banco indicado em `DATABASE_URL` for o banco local correto e você desejar adicionar uma nova conta com o papel `OWNER`. Os usuários existentes não serão apagados nem modificados por essa operação.

Se a operação for cancelada, nenhum novo usuário será criado. Utilize um e-mail válido e uma senha de 8 a 128 caracteres. Guarde as credenciais para entrar no sistema. Execute o utilitário somente no banco local de desenvolvimento, nunca em produção.

### 8. Iniciar a API

Na raiz do projeto, com a `.venv` ativa, execute:

```bat
uvicorn app.main:app --reload --app-dir backend
```

Mantenha o terminal aberto. A documentação interativa estará disponível em:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 9. Iniciar o frontend

Abra um segundo terminal CMD na raiz do repositório e execute:

```bat
cd frontend
npm install
npm run dev
```

Abra a URL mostrada pelo Vite, normalmente `http://localhost:5173`. Na tela de login, use o e-mail e a senha criados no passo anterior. Após entrar, selecione a empresa criada pelo utilitário.

Se a interface não se conectar à API, confira `frontend/src/api.js` e a configuração do Vite para confirmar a URL utilizada pelo frontend.

### 10. Validar o frontend

Ainda dentro de `frontend`, execute:

```bat
npm run lint
npm run build
```

### Resumo da instalação

1. Clonar o repositório e abrir a pasta com `code .`.
2. Criar a `.venv` e instalar as dependências Python.
3. Copiar e configurar `backend\.env`, incluindo a senha PostgreSQL real e uma `SECRET_KEY` aleatória.
4. Criar os bancos definidos nas duas URLs e aplicar `database\apply_all.sql` em cada banco.
5. Rodar a suíte do backend.
6. Executar `python backend\create_initial_user.py` para criar a conta `OWNER` inicial.
7. Iniciar API e frontend e entrar com as credenciais recém-criadas.
8. Validar o frontend com lint e build.

## API

A API usa o prefixo `/api/v1`. Os grupos principais são:

| Grupo | Recursos |
|---|---|
| AUTH | Login e consulta do usuário autenticado (`/api/v1/auth/...`) |
| Empresas | Criação, listagem, consulta e atualização de empresas |
| Unidades | Cadastro, listagem, atualização e ativação/inativação conforme as regras implementadas |
| Itens | Cadastro, consulta, atualização e ativação/inativação conforme as regras implementadas |
| Movimentações | Entradas, saídas, ajustes e histórico por item |
| Estoque | Saldos e itens com estoque baixo |
| Inventários | Abertura, contagem, conclusão, cancelamento e consulta do snapshot |
| CUSTOM | Categorias, campos, opções, valores e associação de categorias aos itens |

As listas que possuem paginação usam `limit` com padrão 50 e máximo 100 e `offset` com padrão 0. O detalhe de inventário preserva o snapshot completo dos itens; não deve ser truncado pelo limite da rota de listagem. Consulte `/docs` para os caminhos, verbos HTTP, parâmetros, schemas e respostas atuais.

## Segurança e limites conhecidos

- Senhas são armazenadas com hash, não em texto puro.
- JWT tem expiração e validação de assinatura; a chave é validada conforme o algoritmo HMAC configurado.
- Papéis e membership são validados no backend; controles visuais no frontend não substituem autorização na API.
- `X-Company-ID` define o contexto da empresa para operações protegidas; o cliente não é a fonte de autorização.
- CORS deve usar origens explicitamente configuradas, especialmente no ambiente hospedado.
- Limites por campo e configuração JSON não substituem um limite global do corpo HTTP.
- Limite global do corpo HTTP e logging estruturado para produção ainda precisam ser definidos conforme a infraestrutura de implantação.
- Ainda não há idempotência geral para todas as requisições de movimentação. Reenvios de uma criação de movimento podem gerar uma segunda operação válida; considerar esse comportamento na integração.
- Nunca registrar tokens completos, senhas, `SECRET_KEY` ou URLs de banco com credenciais.
- O ambiente de testes hospedado não deve ser tratado como sistema de produção nem conter dados sensíveis reais.

## Estado atual e roadmap

```mermaid
flowchart LR
    A[Banco e backend] --> B[Frontend MVP]
    B --> C[Publicação de teste]
    C --> D[Feedback dos testadores]
    D --> E[Correções reproduzíveis e E2E]
    E --> F[Melhorias de UX e novas versões]
```

### Próximo marco: ambiente web para testadores

1. Confirmar o estado local e os commits no Git antes de alterar a implantação.
2. Fazer um backup/exportação do PostgreSQL local e importar uma cópia para o Neon, preservando intacto o banco local.
3. Hospedar a API FastAPI e configurar no serviço de backend as variáveis de ambiente necessárias, incluindo a URL do Neon.
4. Hospedar a interface React/Vite e configurar sua URL de API.
5. Validar login, contexto de empresa, permissões, itens, unidades, movimentações, inventários e CUSTOM pela internet.
6. Liberar o ambiente para testes e registrar os problemas encontrados antes de priorizar novas melhorias.

A prioridade é usar uma cópia de teste com os dados atuais relevantes, permitindo que testadores criem, alterem e removam os registros que o sistema autoriza. Alterações realizadas no banco remoto não devem modificar o PostgreSQL local.

### Evolução planejada

- Observar o uso real e corrigir bugs reproduzíveis, sem reiniciar uma auditoria preventiva geral sem motivo concreto.
- Refinar a hierarquia visual, responsividade e clareza dos estados de carregamento, vazio, sucesso e erro.
- Ampliar os testes E2E dos fluxos mais importantes.
- Planejar administração global de empresas e o fluxo de criação/gestão de contas de funcionários.
- Reavaliar logging, limite global do corpo HTTP e idempotência das movimentações antes de usos que exijam garantias adicionais.

O frontend deve consumir a API e não duplicar as regras do domínio. Traduzir erros `401`, `403`, `404`, `409` e `422` em mensagens compreensíveis; não indicar sucesso quando a API rejeitar uma operação.

## Recursos do projeto

- [Scripts e estrutura do banco](database/)
- [Dependências do backend](backend/requirements.txt)
- [Configuração de ambiente de exemplo](backend/.env.example)
- [Documentação da API após iniciar o backend](http://127.0.0.1:8000/docs)

---

<p align="center">
  <strong>Estoque Flex</strong><br />
  <sub>Estrutura estável para o que é crítico. Flexibilidade para o que muda.</sub>
</p>

---

## Informações acadêmicas

Esta seção documenta os requisitos do sistema conforme solicitado na disciplina de Engenharia de Software. **Requisitos funcionais (RF)** descrevem o que o sistema faz; **requisitos não funcionais (RNF)** descrevem as qualidades e restrições com que ele deve fazer isso.

### Requisitos funcionais

| ID | Módulo | Requisito |
|---|---|---|
| RF01 | AUTH | O sistema deve permitir que o usuário faça login com e-mail e senha, recebendo um token JWT. |
| RF02 | AUTH | O sistema deve permitir consultar os dados do usuário autenticado. |
| RF03 | AUTH | O sistema deve definir o contexto da empresa de cada operação protegida por meio do cabeçalho `X-Company-ID`. |
| RF04 | AUTH | O sistema deve controlar as permissões por papéis (OWNER, OPERATOR e VIEWER). |
| RF05 | AUTH | O sistema deve permitir criar a primeira conta de usuário, com a primeira empresa e o papel OWNER, por meio de um utilitário de inicialização. |
| RF06 | CORE | O sistema deve permitir criar, listar, consultar e atualizar empresas. |
| RF07 | CORE | O sistema deve permitir cadastrar, listar, atualizar e ativar/inativar unidades de medida. |
| RF08 | CORE | O sistema deve permitir cadastrar, consultar, atualizar e ativar/inativar itens de estoque. |
| RF09 | CORE | O sistema deve permitir registrar movimentações de entrada, saída e ajuste de estoque. |
| RF10 | CORE | O sistema deve permitir consultar o saldo de estoque dos itens e listar os itens com estoque baixo. |
| RF11 | CORE | O sistema deve permitir consultar o histórico de movimentações de cada item. |
| RF12 | CORE | O sistema deve permitir abrir inventários, registrar contagens, concluir ou cancelar o inventário e consultar o snapshot dos itens. |
| RF13 | CUSTOM | O sistema deve permitir criar categorias de itens por empresa. |
| RF14 | CUSTOM | O sistema deve permitir definir campos personalizados por categoria, incluindo campos do tipo lista com suas opções. |
| RF15 | CUSTOM | O sistema deve permitir associar itens a categorias e registrar os valores dos campos personalizados de cada item. |
| RF16 | Frontend | O sistema deve oferecer interface web para autenticação e seleção de empresa, itens, unidades, movimentações, detalhes de item e configuração de campos personalizados. |
| RF17 | Frontend | O sistema deve exibir ou ocultar os controles da interface de acordo com o papel do usuário. |

### Requisitos não funcionais

| ID | Categoria | Requisito |
|---|---|---|
| RNF01 | Segurança | As senhas devem ser armazenadas apenas como hash (Argon2), nunca em texto puro. |
| RNF02 | Segurança | A autenticação deve usar tokens JWT com assinatura validada e tempo de expiração. |
| RNF03 | Segurança | As permissões e o vínculo do usuário com a empresa devem ser validados no backend; os controles visuais do frontend não substituem a autorização na API. |
| RNF04 | Segurança | Os dados de uma empresa não devem ser acessíveis por usuários de outra empresa (isolamento multiempresa). |
| RNF05 | Segurança | O CORS deve aceitar apenas origens explicitamente configuradas. |
| RNF06 | Integridade | O saldo de estoque deve ser derivado das movimentações e não pode ser editado manualmente no item. |
| RNF07 | Integridade | As quantidades devem usar precisão decimal compatível com `NUMERIC(18,4)`. |
| RNF08 | Integridade | O histórico de movimentações deve ser preservado, sem exclusão para ocultar erros operacionais. |
| RNF09 | Confiabilidade | Saídas concorrentes não podem deixar o saldo negativo; esse comportamento é coberto por teste de regressão. |
| RNF10 | Validação | Os textos devem respeitar limites de tamanho (curto: 255; longo: 10.000; descrições: 2.000; observações: 5.000 caracteres), e a configuração JSON de campos é limitada a 16 KiB. |
| RNF11 | Desempenho | As listagens selecionadas devem ser paginadas, com `limit` padrão de 50 e máximo de 100, e `offset` padrão de 0. |
| RNF12 | Manutenibilidade | O backend deve seguir arquitetura de monólito modular, na qual CORE não depende de AUTH nem de CUSTOM, e a orquestração entre domínios fica na camada `application`. |
| RNF13 | Manutenibilidade | Atualizações parciais (PATCH) não devem alterar campos omitidos na requisição. |
| RNF14 | Testabilidade | O backend deve ter testes automatizados com pytest (468 testes aprovados na última execução local), e o frontend deve passar em lint e build. |
| RNF15 | Usabilidade | O frontend deve traduzir os erros 401, 403, 404, 409 e 422 da API em mensagens compreensíveis e não indicar sucesso quando a API rejeitar uma operação. |
| RNF16 | Interoperabilidade | A API deve seguir o padrão REST sob o prefixo `/api/v1`, com documentação interativa (Swagger UI e ReDoc) gerada pelo FastAPI. |
| RNF17 | Portabilidade | O sistema deve ser executável localmente em Windows com Python, PostgreSQL e Node.js, seguindo o guia de instalação deste README. |