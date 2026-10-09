<p align="center">
  <img src="docs/assets/estoque-flex-hero.svg" alt="Estoque Flex — controle confiável, estrutura flexível" width="100%" />
</p>

<p align="center">
  <strong>Controle de estoque confiável, com estrutura preparada para diferentes negócios.</strong><br />
  API modular · Multiempresa · Campos personalizados
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-FastAPI-3776AB?style=for-the-badge&logo=fastapi&logoColor=white" alt="Python e FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Testes-362%20passed-22C55E?style=for-the-badge&logo=pytest&logoColor=white" alt="362 testes aprovados na última validação" />
  <img src="https://img.shields.io/badge/Status-Backend%20em%20hardening-F59E0B?style=for-the-badge&logo=github&logoColor=white" alt="Backend em hardening" />
</p>

<p align="center">
  <a href="#-visão-geral">Visão geral</a> ·
  <a href="#-arquitetura">Arquitetura</a> ·
  <a href="#-capacidades-implementadas">Capacidades</a> ·
  <a href="#-executar-localmente">Executar localmente</a> ·
  <a href="#-roadmap">Roadmap</a>
</p>

---

## ✦ Visão geral

O **Estoque Flex** é um sistema web de gerenciamento de estoque pensado para pequenos negócios que precisam de rastreabilidade sem abrir mão da flexibilidade. O núcleo mantém as regras críticas do estoque; uma camada configurável permite que cada empresa descreva seus próprios produtos sem transformar o banco em uma coleção de colunas específicas para cada negócio.

> **CORE controla o estoque. CUSTOM descreve o estoque. AUTH protege o acesso.**

O backend já reúne as APIs de empresas, unidades, itens, movimentações, consultas de estoque, inventários e personalização de itens. O próximo marco é a revisão de hardening; o frontend e os testes E2E ainda estão pendentes.

## ✨ Capacidades implementadas

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>📦 CORE</h3>
      <p>Regras operacionais e dados estruturados.</p>
      <ul>
        <li>Empresas e unidades de medida</li>
        <li>Cadastro e consulta de itens</li>
        <li>Registro de movimentações</li>
        <li>Consulta de saldo e estoque baixo</li>
        <li>Inventários e itens de inventário</li>
      </ul>
    </td>
    <td width="33%" valign="top">
      <h3>🧩 CUSTOM</h3>
      <p>Personalização sem alterar o núcleo.</p>
      <ul>
        <li>Categorias de itens</li>
        <li>Campos personalizados por categoria</li>
        <li>Opções para campos do tipo lista</li>
        <li>Valores personalizados por item</li>
        <li>Associação de itens a categorias</li>
      </ul>
    </td>
    <td width="33%" valign="top">
      <h3>🔐 AUTH</h3>
      <p>Identidade, contexto e permissões.</p>
      <ul>
        <li>Login com JWT</li>
        <li>Endpoint de usuário atual</li>
        <li>Contexto por <code>X-Company-ID</code></li>
        <li>Papéis OWNER, OPERATOR e VIEWER</li>
        <li>Isolamento entre empresas</li>
      </ul>
    </td>
  </tr>
</table>

## 🧭 Arquitetura

O backend segue uma arquitetura de **monólito modular**: módulos separados por domínio, uma API HTTP clara e uma camada de aplicação para coordenar operações que atravessam módulos.

```mermaid
flowchart TD
    CLIENT[Cliente HTTP] --> ROUTER[FastAPI · Routers]
    ROUTER --> SCHEMA[Pydantic · Schemas]
    SCHEMA --> SERVICE[Services · Regras de negócio]
    SERVICE --> ORM[SQLAlchemy 2.x]
    ORM --> DB[(PostgreSQL)]
```

### Dependências entre módulos

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

A direção é intencional: **CORE não depende de AUTH nem de CUSTOM**. Operações que exigem coordenação entre domínios ficam na camada `application`, reduzindo o acoplamento e preservando as regras do núcleo.

### Princípios de domínio

- **Saldo rastreável:** o histórico de movimentações é a fonte de verdade; o saldo não é um campo manual editável no item.
- **Precisão:** quantidades são modeladas para suportar `NUMERIC(18,4)` no banco.
- **Histórico preservado:** correções operacionais devem ser rastreáveis; não se apagam movimentações para esconder erros.
- **Multiempresa:** consultas e operações devem respeitar o contexto da empresa e validar as relações entre registros.
- **Saldo negativo:** bloqueado por padrão, conforme as regras do domínio.
- **CUSTOM sem acoplamento inverso:** características de negócio ficam na camada configurável, não no CORE.

## 🧪 Qualidade e status atual

<p>
  <img src="https://img.shields.io/badge/Gate%20A-Banco%20validado-16A34A?style=flat-square" alt="Gate A concluído" />
  <img src="https://img.shields.io/badge/API%20CORE-Implementada-16A34A?style=flat-square" alt="API CORE implementada" />
  <img src="https://img.shields.io/badge/API%20CUSTOM-Implementada-16A34A?style=flat-square" alt="API CUSTOM implementada" />
  <img src="https://img.shields.io/badge/Frontend-Pendente-64748B?style=flat-square" alt="Frontend pendente" />
</p>

| Etapa | Estado | Observação |
|---|---|---|
| Gate A — banco de dados | ✅ Concluído | Scripts SQL CORE, AUTH e CUSTOM versionados. |
| Fundação do backend | ✅ Concluída | FastAPI, configuração, banco, segurança e testes. |
| AUTH e multiempresa | ✅ Implementados | JWT, usuário atual, membership, papéis e contexto empresarial. |
| APIs CORE | ✅ Implementadas | Empresas, unidades, itens, movimentações, estoque e inventário. |
| API CUSTOM | ✅ Implementada | Categorias, campos, opções, valores e associação com itens. |
| Suíte de testes | ✅ 362 aprovados | Última execução local registrada no checkpoint `e18bc18`. |
| Hardening consolidado | 🟡 Próxima etapa | Revisar segurança, consistência, concorrência, erros e qualidade. |
| Frontend React/Vite | ⏳ Pendente | Interface ainda não integrada ao backend. |
| Testes E2E | ⏳ Pendente | Validar os principais fluxos ponta a ponta. |
| Deploy | ⏳ Pendente | Após hardening, frontend e validação E2E. |

> **Importante:** APIs implementadas e testes aprovados não significam que a aplicação já esteja pronta para produção. Hardening, interface e validação E2E ainda fazem parte do roadmap.

## 🧱 Tecnologias

| Camada | Tecnologias |
|---|---|
| API | Python, FastAPI, Pydantic |
| Persistência | SQLAlchemy 2.x, PostgreSQL, Alembic |
| Autenticação | JWT/PyJWT, `pwdlib`, Argon2 |
| Testes | pytest, FastAPI TestClient, httpx |
| Frontend planejado | React, Vite, JavaScript |
| Ferramentas | Git, GitHub, VS Code |

## 🗂️ Organização do repositório

```text
.
├── backend/
│   ├── app/
│   │   ├── application/   # Orquestração entre domínios
│   │   ├── auth/          # Autenticação e autorização
│   │   ├── core/          # Regras fundamentais do estoque
│   │   ├── custom/        # Campos e categorias configuráveis
│   │   ├── health/        # Health check
│   │   └── shared/        # Configuração e dependências compartilhadas
│   ├── tests/             # Testes de modelos, schemas, services e APIs
│   ├── requirements.txt
│   └── .env.example
├── database/
│   ├── core/              # Estrutura e views do CORE
│   ├── auth/              # Estrutura de autenticação
│   ├── custom/            # Estrutura de personalização
│   └── apply_all.sql      # Aplicação completa em banco novo
├── docs/
│   └── assets/            # Recursos visuais da documentação
├── pytest.ini
└── README.md
```

## 🚀 Executar localmente

### 1. Preparar o ambiente Python

Execute na raiz do repositório:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend\requirements.txt
```

### 2. Configurar as variáveis de ambiente

```bat
copy backend\.env.example backend\.env
```

Edite `backend/.env`, confira a URL do PostgreSQL e defina também uma `SECRET_KEY` forte. O `.env.example` é apenas um ponto de partida; não publique credenciais reais.

Exemplo de formato:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:senha@localhost:5432/estoque_flex_dev
SECRET_KEY=substitua-por-uma-chave-segura
```

### 3. Criar e preparar um banco novo

Crie o banco `estoque_flex_dev` no PostgreSQL, caso ainda não exista. A partir da raiz do projeto, aplique os scripts versionados:

```bat
psql -U postgres -d estoque_flex_dev -v ON_ERROR_STOP=1 -f database/apply_all.sql
```

> Execute `database/apply_all.sql` em um banco novo. Não reaplique scripts sobre um banco existente sem antes conferir o estado das tabelas, constraints e triggers.

### 4. Executar os testes

Com o ambiente virtual ativo e o banco de teste configurado:

```bat
python -m pytest -q
```

### 5. Iniciar a API

Na raiz do repositório:

```bat
uvicorn app.main:app --reload --app-dir backend
```

A documentação interativa do FastAPI ficará disponível em:

- Swagger UI: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- ReDoc: [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

## 🔌 API

A API usa o prefixo `/api/v1`. Os principais grupos são:

| Grupo | Recursos |
|---|---|
| AUTH | Login e usuário autenticado (`/api/v1/auth/...`) |
| Empresas | Cadastro, listagem, consulta e atualização de empresas |
| Unidades | Cadastro e manutenção de unidades de medida |
| Itens | Cadastro e consulta de itens |
| Movimentações | Registro de entradas, saídas e ajustes |
| Estoque | Consulta de saldos e identificação de estoque baixo |
| Inventários | Contagem física e itens de inventário |
| CUSTOM | Categorias, campos, opções, valores e categoria dos itens |

Consulte `/docs` para ver os caminhos, parâmetros, schemas e respostas efetivamente registrados pela aplicação.

## 🔐 Segurança

- Senhas armazenadas com hash — nunca em texto puro.
- JWT com expiração e validação de assinatura.
- Papéis e membership validados no backend.
- Contexto de empresa fornecido por `X-Company-ID` e validado antes das operações protegidas.
- Segredos mantidos em variáveis de ambiente; `.env` não deve ser versionado.
- Tokens completos, senhas e `SECRET_KEY` não devem aparecer em logs.

O hardening final permanece como etapa explícita antes da preparação para produção. O foco inclui revisão de permissões e isolamento, concorrência e transações de estoque, mapeamento consistente de conflitos para HTTP 409, paginação com limites máximos, CORS restrito, limites de payload, logging estruturado sem dados sensíveis e quality gates de lint/testes.

## 🗺️ Roadmap

```mermaid
flowchart LR
    A[Gate A · Banco] --> B[Backend CORE + AUTH + CUSTOM]
    B --> C[Hardening consolidado]
    C --> D[Frontend React + Vite]
    D --> E[Testes E2E]
    E --> F[Deploy e demonstração]
```

**Próximo marco:** auditar as APIs já implementadas e executar o hardening consolidado antes de integrar o frontend. O objetivo é validar permissões, isolamento multiempresa, integridade referencial, semântica de PATCH, conflitos, concorrência de estoque e consistência dos inventários.

## 📚 Recursos do projeto

- [Scripts e estrutura do banco](database/)
- [Dependências do backend](backend/requirements.txt)
- [Configuração de ambiente de exemplo](backend/.env.example)

---

<p align="center">
  <strong>Estoque Flex</strong><br />
  <sub>Estrutura estável para o que é crítico. Flexibilidade para o que muda.</sub>
</p>
