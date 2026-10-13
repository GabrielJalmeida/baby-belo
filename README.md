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
  <img src="https://img.shields.io/badge/Testes-467%20passed-22C55E?style=for-the-badge&logo=pytest&logoColor=white" alt="467 testes aprovados na última execução local" />
  <img src="https://img.shields.io/badge/Frontend-pr%C3%B3xima%20etapa-64748B?style=for-the-badge&logo=react&logoColor=white" alt="Frontend é a próxima etapa" />
</p>

<p align="center">
  <a href="#visao-geral">Visão geral</a> ·
  <a href="#capacidades">Capacidades</a> ·
  <a href="#arquitetura">Arquitetura</a> ·
  <a href="#executar-localmente">Executar localmente</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

## Visão geral

O **Estoque Flex** é um sistema de gerenciamento de estoque pensado para pequenos negócios que precisam de rastreabilidade sem abrir mão da flexibilidade. O núcleo mantém as regras operacionais do estoque, enquanto uma camada configurável permite que cada empresa descreva seus itens sem transformar o banco em uma coleção de colunas específicas para cada negócio.

> **CORE controla o estoque. CUSTOM descreve o estoque. AUTH protege o acesso.**

O backend disponibiliza APIs para empresas, unidades, itens, movimentações, consultas de estoque, inventários e personalização de itens. O hardening planejado para esta fase foi encerrado; a próxima etapa de desenvolvimento é o frontend temporário em React/Vite. Os testes E2E e o deploy continuam pendentes.

## Capacidades

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>📦 CORE</h3>
      <p>Regras operacionais e dados estruturados.</p>
      <ul>
        <li>Empresas e unidades de medida</li>
        <li>Cadastro, consulta e atualização de itens</li>
        <li>Registro de entradas, saídas e ajustes</li>
        <li>Consulta de saldos e estoque baixo</li>
        <li>Inventários, contagens e ajustes resultantes</li>
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
        <li>Isolamento de dados entre empresas</li>
      </ul>
    </td>
  </tr>
</table>

## Arquitetura

O backend segue uma arquitetura de **monólito modular**: módulos separados por domínio, uma API HTTP clara e uma camada de aplicação para coordenar operações que atravessam módulos.

```mermaid
flowchart TD
    CLIENT[Cliente HTTP] --> ROUTER[FastAPI · Routers]
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

A direção é intencional: **CORE não importa AUTH nem CUSTOM**. Operações que exigem coordenação entre domínios ficam na camada `application`, reduzindo o acoplamento e preservando as regras do núcleo. CUSTOM pode depender de CORE, mas o inverso é proibido.

### Princípios de domínio

- **Saldo rastreável:** o histórico de movimentações sustenta as consultas de saldo; o saldo não é um campo manualmente editável no item.
- **Precisão decimal:** quantidades usam precisão compatível com `NUMERIC(18,4)`.
- **Histórico preservado:** movimentações não devem ser apagadas para ocultar erros operacionais.
- **Multiempresa:** toda consulta e mutação protegida deve respeitar a empresa autenticada e validar os registros relacionados.
- **Integridade de estoque:** saídas são validadas contra o saldo e as regras do domínio; cenários concorrentes críticos têm teste automatizado.
- **CUSTOM sem acoplamento inverso:** os campos configuráveis estendem o núcleo sem fazer o CORE depender de CUSTOM.

## Qualidade e status

<p>
  <img src="https://img.shields.io/badge/Gate%20A-Banco%20validado-16A34A?style=flat-square" alt="Gate A concluído" />
  <img src="https://img.shields.io/badge/API%20CORE-Implementada-16A34A?style=flat-square" alt="API CORE implementada" />
  <img src="https://img.shields.io/badge/API%20CUSTOM-Implementada-16A34A?style=flat-square" alt="API CUSTOM implementada" />
  <img src="https://img.shields.io/badge/Hardening-Fase%20encerrada-16A34A?style=flat-square" alt="Hardening encerrado nesta fase" />
</p>

| Etapa | Estado | Observação |
|---|---|---|
| Gate A — banco de dados | ✅ Concluído | Estrutura CORE, AUTH e CUSTOM aplicada e validada no ambiente de desenvolvimento. |
| Fundação do backend | ✅ Concluída | FastAPI, configuração, persistência, segurança e testes. |
| AUTH e multiempresa | ✅ Implementados | JWT, usuário atual, membership, papéis e contexto empresarial. |
| APIs CORE | ✅ Implementadas | Empresas, unidades, itens, movimentações, estoque e inventário. |
| API CUSTOM | ✅ Implementada | Categorias, campos, opções, valores e associação com itens. |
| Paginação | ✅ Implementada nas listas selecionadas | Listas de empresas, saldos, estoque baixo, inventários, itens de inventário, categorias, campos e opções usam limites validados. |
| Limites de texto | ✅ Implementados | Texto curto: 255; texto longo: 10.000; descrições: 2.000; observações: 5.000 caracteres. |
| Configuração de campos | ✅ Validada | Objeto JSON serializado limitado a 16 KiB, validado no schema e no serviço. |
| Concorrência de saídas | ✅ Testada | Teste concorrente confirma que duas saídas incompatíveis não causam saldo negativo. |
| Suíte de testes | ✅ 467 aprovados | Última execução local: `467 passed in 20.19s`. |
| Hardening desta fase | ✅ Encerrado | Pendências de implantação e idempotência permanecem documentadas, sem bloquear o início do frontend. |
| Frontend React/Vite | ⏳ Próxima etapa | Interface temporária ainda não integrada aos fluxos da API. |
| Testes E2E | ⏳ Pendente | Validar os fluxos principais de ponta a ponta. |
| Deploy | ⏳ Pendente | Após integração e validação E2E. |

> **Nota sobre prontidão:** o hardening desta fase foi encerrado para permitir a evolução do MVP. Isso não significa que os itens de implantação e produção estejam todos resolvidos. O desenvolvimento continuará corrigindo problemas reais descobertos durante a integração do frontend.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| API | Python, FastAPI, Pydantic |
| Persistência | SQLAlchemy 2.x, PostgreSQL, Alembic |
| Autenticação | JWT/PyJWT, Argon2 |
| Testes | pytest, FastAPI TestClient, cliente HTTP de testes |
| Frontend planejado | React, Vite, JavaScript |
| Ferramentas de desenvolvimento | Python, VS Code |

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
│   │   └── shared/        # Configuração, segurança e utilitários comuns
│   ├── tests/             # Testes de serviços e APIs
│   ├── requirements.txt
│   └── .env.example
├── database/
│   ├── core/
│   ├── auth/
│   ├── custom/
│   └── apply_all.sql      # Aplicação completa em banco novo
├── docs/
│   └── assets/            # Recursos visuais da documentação
├── pytest.ini
└── README.md
```

## Executar localmente

### 1. Preparar o ambiente Python

Execute na raiz do repositório, usando o CMD do Windows:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend\requirements.txt
```

### 2. Configurar as variáveis de ambiente

```bat
copy backend\.env.example backend\.env
```

Edite `backend/.env`, confira a URL do PostgreSQL e configure uma chave JWT forte. **Não publique nem compartilhe o conteúdo real do `.env`.** O arquivo de exemplo não deve conter credenciais válidas.

Exemplo ilustrativo de formato:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:senha@localhost:5432/estoque_flex_dev
SECRET_KEY=troque-por-uma-chave-segura
```

### 3. Preparar um banco novo

Crie um banco de desenvolvimento vazio no PostgreSQL e, a partir da raiz do projeto, aplique os scripts versionados:

```bat
psql -U postgres -d estoque_flex_dev -v ON_ERROR_STOP=1 -f database/apply_all.sql
```

> Execute `database/apply_all.sql` em um banco novo. Não reaplique scripts sobre um banco existente sem primeiro conferir o estado de tabelas, constraints, índices e triggers. O banco de desenvolvimento já utilizado no projeto foi preparado anteriormente.

### 4. Executar os testes

Com o ambiente virtual ativo e o banco configurado para testes:

```bat
python -m pytest backend\tests -q
```

Última execução completa registrada no ambiente local: `467 passed in 20.19s`. O número pode mudar quando novos testes forem adicionados.

### 5. Iniciar a API

Na raiz do repositório:

```bat
uvicorn app.main:app --reload --app-dir backend
```

A documentação interativa fica disponível em:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## API

A API usa o prefixo `/api/v1`. Os grupos principais são:

| Grupo | Recursos |
|---|---|
| AUTH | Login e consulta do usuário autenticado (`/api/v1/auth/...`) |
| Empresas | Criação, listagem, consulta e atualização de empresas |
| Unidades | Cadastro, listagem e manutenção de unidades de medida |
| Itens | Cadastro, consulta e atualização de itens |
| Movimentações | Registro de entradas, saídas e ajustes; histórico por item |
| Estoque | Saldos e itens com estoque baixo |
| Inventários | Abertura, contagem, conclusão, cancelamento e consulta do snapshot |
| CUSTOM | Categorias, campos, opções, valores e associação de categorias aos itens |

As listas contempladas usam `limit` padrão 50 e máximo 100, e `offset` padrão 0. O detalhe de inventário preserva o snapshot completo dos itens e não deve ser truncado pelo limite da rota de listagem. Consulte `/docs` para os caminhos, parâmetros, schemas e respostas registrados na aplicação.

## Segurança e limites conhecidos

- Senhas armazenadas com hash, nunca em texto puro.
- JWT com expiração e validação de assinatura; a chave de assinatura é validada conforme o algoritmo HMAC configurado.
- Papéis e membership validados no backend.
- `X-Company-ID` é validado antes das operações protegidas; o cliente não é fonte de autorização.
- CORS utiliza origens configuradas explicitamente; não use wildcard em produção com credenciais.
- Limites de texto e da configuração JSON são aplicados na API; eles não substituem um limite global do corpo da requisição.
- O tamanho global do corpo HTTP e o logging estruturado para produção devem ser definidos de acordo com a infraestrutura de implantação.
- A API ainda não oferece idempotência automática para todas as solicitações de movimentação. Reenvios devem ser considerados ao definir a estratégia de integração com clientes.
- Não registrar tokens completos, senhas, `SECRET_KEY` ou outros segredos nos logs.

Esses pontos não impedem o início do frontend do MVP, mas devem ser considerados antes de uma implantação de produção. Problemas de autorização, integridade ou consistência encontrados durante a integração devem ser corrigidos com testes de regressão.

## Roadmap

```mermaid
flowchart LR
    A[Gate A · Banco] --> B[Backend CORE + AUTH + CUSTOM]
    B --> C[Hardening desta fase concluído]
    C --> D[Frontend React + Vite]
    D --> E[Testes E2E]
    E --> F[Deploy e demonstração]
```

### Próximo marco: frontend temporário

A próxima etapa é iniciar uma interface React/Vite com JavaScript, mantendo o custo do MVP em R$ 0 e consumindo os contratos existentes da API. O trabalho será incremental:

1. Inspecionar o estado real do repositório e confirmar se já existe scaffolding de frontend antes de criar ou substituir arquivos.
2. Implementar o cliente HTTP centralizado, autenticação e contexto da empresa.
3. Construir os fluxos de unidades e itens.
4. Integrar movimentações, saldos e estoque baixo.
5. Integrar inventários, respeitando paginação e snapshot completo.
6. Integrar categorias, campos, opções e valores CUSTOM.
7. Adicionar testes E2E para os principais fluxos e corrigir regressões que forem descobertas.
8. Preparar a configuração de implantação e a verificação pós-deploy.

O frontend deve consumir a API, e não duplicar as regras do domínio. Tratar erros `401`, `403`, `404`, `409` e `422` com mensagens compreensíveis; nunca considerar uma operação bem-sucedida apenas por feedback visual.

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
