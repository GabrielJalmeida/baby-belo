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

### 1. Preparar o ambiente Python

Execute na raiz do repositório usando o CMD do Windows:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend\requirements.txt
```

Se a `.venv` já existir, não é necessário recriá-la; basta ativá-la e instalar eventuais dependências faltantes.

### 2. Configurar as variáveis de ambiente

Se `backend/.env` ainda não existir, crie-o a partir do exemplo:

```bat
copy backend\.env.example backend\.env
```

Se o arquivo já existir, **não o sobrescreva**: mantenha suas configurações locais. Edite `backend/.env` apenas quando necessário para conferir a conexão com o PostgreSQL local, uma chave JWT forte e as origens permitidas para CORS. **Não publique nem compartilhe o conteúdo real do `.env`.** O arquivo de exemplo deve usar valores fictícios, sem credenciais válidas.

Exemplo ilustrativo de formato:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:senha@localhost:5432/estoque_flex_dev
SECRET_KEY=substitua-por-uma-chave-forte-com-pelo-menos-32-bytes
```

O nome das variáveis e as regras de validação devem acompanhar `backend/app/shared/config.py`. Não use a URL do banco no código do frontend.

### 3. Preparar um banco novo

Crie um banco de desenvolvimento vazio no PostgreSQL. A partir da raiz do projeto, aplique os scripts versionados:

```bat
psql -U postgres -d estoque_flex_dev -v ON_ERROR_STOP=1 -f database/apply_all.sql
```

Execute `database/apply_all.sql` em um banco novo. **Não reaplique os scripts em um banco existente sem verificar antes as tabelas, constraints, índices e triggers.** O banco local usado no desenvolvimento já foi preparado anteriormente.

### 4. Executar os testes de backend

Com a `.venv` ativa e o banco de testes configurado:

```bat
python -m pytest backend\tests -q
```

Última execução completa registrada: `468 passed in 19.56s`. O resultado pode mudar quando novos testes forem adicionados.

### 5. Iniciar a API

Na raiz do repositório:

```bat
uvicorn app.main:app --reload --app-dir backend
```

A documentação interativa fica disponível em:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

### 6. Iniciar o frontend

Em outro terminal CMD:

```bat
cd frontend
npm install
npm run dev
```

Para validar o frontend:

```bat
npm run lint
npm run build
```

Consulte `frontend/src/api.js` e a configuração do Vite para confirmar como a URL da API é definida no checkout atual. A URL pública da API não é segredo; credenciais de banco e a `SECRET_KEY` do backend nunca devem ser incluídas no bundle do frontend.

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
