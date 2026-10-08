# 📦 Estoque Flex

<p align="center">
  <strong>Sistema web de estoque flexível, configurável e multiempresa.</strong>
</p>

<p align="center">
  Controle de estoque com estrutura fixa para regras críticas e uma camada configurável para diferentes tipos de negócio.
</p>

---

## ✨ Sobre o projeto

O **Estoque Flex** é um sistema web de gerenciamento de estoque desenvolvido para pequenos negócios que precisam de controle confiável sem perder flexibilidade.

A arquitetura separa:

```text
CORE
→ controla as regras fundamentais do estoque

CUSTOM
→ descreve e personaliza os itens

AUTH
→ controla usuários, empresas, papéis e autenticação
```

A ideia central é manter estáveis as regras essenciais do estoque, permitindo que cada empresa configure suas próprias características sem modificar o núcleo do sistema.

Exemplo:

```text
Item: Linha Rosa

Unidade: Rolo
Saldo: 1.5

Categoria: Linhas

Campos personalizados:
├── Cor: Rosa Bebê
├── Marca: Círculo
└── Especial: Sim
```

---

## 🎯 Objetivo

Criar uma aplicação web capaz de atender diferentes pequenos negócios sem exigir alterações estruturais no banco sempre que surgir uma nova característica de produto ou matéria-prima.

A V1 foi projetada para permitir:

* cadastro e gerenciamento de empresas;
* unidades de medida;
* cadastro de itens;
* entradas, saídas e ajustes;
* saldo calculado a partir do histórico;
* estoque mínimo;
* inventário físico;
* categorias configuráveis;
* campos personalizados;
* opções para campos do tipo lista;
* valores personalizados;
* autenticação;
* controle de acesso por papel;
* isolamento entre empresas;
* uso em desktop e dispositivos móveis.

---

## 🧠 Princípio da arquitetura

> **A estrutura fixa controla o estoque. A estrutura configurável descreve o estoque.**

### CORE

Responsável pelas regras fundamentais:

```text
empresa
unidade
item
movimentação
saldo
estoque mínimo
inventário
```

### CUSTOM

Responsável pela personalização:

```text
categoria
campo personalizado
tipo de dado
opção
valor personalizado
```

### AUTH

Responsável pela identidade e autorização:

```text
usuário
empresa
vínculo usuário/empresa
papel
autenticação
autorização
```

### Regra de dependência

```text
CUSTOM → CORE ✅
AUTH   → CORE ✅

CORE   → CUSTOM ❌
CORE   → AUTH   ❌
```

O CORE permanece independente de autenticação e de customizações.

Quando uma operação precisa combinar diferentes módulos, a aplicação utiliza uma camada de **Application/Orchestration**, evitando acoplamento indevido entre os domínios.

---

## 🏗️ Arquitetura do backend

O backend utiliza um **Modular Monolith**.

Fluxo principal:

```text
HTTP / Router
      ↓
Pydantic Schema
      ↓
Service / Regra de negócio
      ↓
SQLAlchemy
      ↓
PostgreSQL
```

O `main.py` permanece pequeno e funciona como ponto de montagem da aplicação.

Ele não deve concentrar:

```text
regras de negócio
cálculo de saldo
queries complexas
validações específicas de domínio
```

### Estrutura atual

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   └── company_service.py
│   │
│   ├── shared/
│   │   ├── base.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── dependencies.py
│   │   ├── company_dependencies.py
│   │   └── authorization.py
│   │
│   ├── health/
│   │   └── router.py
│   │
│   ├── auth/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── company_service.py
│   │   └── router.py
│   │
│   └── core/
│       ├── models.py
│       ├── schemas.py
│       ├── service.py
│       ├── router.py
│       ├── unit_models.py
│       ├── unit_schemas.py
│       ├── unit_service.py
│       └── unit_router.py
│
├── tests/
├── requirements.txt
└── .env.example
```

A estrutura poderá ser reorganizada futuramente conforme o crescimento do sistema, mas sem criar complexidade arquitetural sem necessidade.

---

## 🔐 Autenticação e autorização

A autenticação já possui implementação funcional no backend.

Tecnologias utilizadas:

```text
OAuth2 Password Flow
JWT
PyJWT
pwdlib
Argon2
```

### Login

```text
POST /api/v1/auth/login
```

O usuário é autenticado e recebe um JWT.

O token contém a identidade do usuário por meio de:

```json
{
  "sub": "ID_DO_USUARIO",
  "exp": "EXPIRACAO"
}
```

A empresa não é fixada no JWT porque o mesmo usuário pode pertencer a várias empresas.

### Usuário atual

```text
GET /api/v1/auth/me
```

O endpoint utiliza o usuário identificado pelo token.

### Validação do token

O backend verifica:

```text
token válido
token não expirado
assinatura correta
usuário existente
usuário ativo
```

Falhas de autenticação resultam em:

```text
401 Unauthorized
```

---

## 👥 Multiempresa

Um usuário pode participar de várias empresas.

O vínculo é representado por:

```text
auth.empresa_usuarios
```

Cada vínculo possui:

```text
empresa_id
usuario_id
papel
ativo
```

### Papéis da V1

```text
OWNER
OPERATOR
VIEWER
```

### Contexto da empresa

A empresa ativa é identificada por:

```text
X-Company-ID
```

A autorização verifica:

```text
usuário autenticado
        ↓
empresa solicitada
        ↓
membership ativa
        ↓
empresa ativa
        ↓
papel permitido
```

Isso evita que a identidade do usuário seja confundida com o contexto da empresa.

### Exemplo

```text
Usuário A
├── Empresa A → OWNER
└── Empresa B → VIEWER
```

Uma requisição para a Empresa A utiliza:

```http
X-Company-ID: <ID_EMPRESA_A>
```

O backend valida o vínculo antes de permitir a operação.

### Isolamento

Uma empresa nunca deve conseguir acessar registros de outra.

Exemplo inválido:

```text
Item da Empresa A
+
Categoria da Empresa B
```

As consultas dos recursos que já foram implementados utilizam o contexto da empresa para restringir os dados.

---

## 🏢 Empresas

CRUD inicial implementado:

```text
POST  /api/v1/empresas
GET   /api/v1/empresas
GET   /api/v1/empresas/{id}
PATCH /api/v1/empresas/{id}
```

Ao criar uma empresa:

```text
criar empresa
↓
criar vínculo do usuário
↓
usuário recebe OWNER
```

Essa operação é orquestrada pela camada:

```text
application/company_service.py
```

mantendo o CORE independente do AUTH.

### Inativação e reativação

Empresas podem ser inativadas sem apagar seus dados.

O `OWNER` pode:

```text
ativa
↓
desativar
↓
reativar
```

A rota administrativa de gestão mantém o vínculo do usuário mesmo quando a empresa está inativa, permitindo sua posterior reativação.

---

## 📏 Unidades

CRUD inicial implementado:

```text
POST  /api/v1/unidades
GET   /api/v1/unidades
GET   /api/v1/unidades/{id}
PATCH /api/v1/unidades/{id}
```

Cada unidade pertence a uma empresa.

Exemplos:

```text
Unidade
Metro
Rolo
Kg
Litro
Caixa
```

Uma unidade possui:

```text
nome
símbolo
permite_decimal
ativo
empresa_id
```

Exemplo:

```text
Rolo
permite_decimal = true
```

pode representar:

```text
1.5 rolos
```

Enquanto uma unidade configurada para não aceitar decimais deve trabalhar somente com quantidades inteiras.

---

## 🗄️ Banco de dados

O projeto utiliza **PostgreSQL**.

### CORE

```text
core.empresas
core.unidades
core.itens
core.movimentacoes
core.inventarios
core.inventario_itens
```

Views:

```text
core.vw_saldos_estoque
core.vw_itens_estoque_baixo
```

Scripts:

```text
001_create_schemas.sql
002_create_empresas.sql
003_create_unidades.sql
004_create_itens.sql
005_create_movimentacoes.sql
006_create_inventarios.sql
007_create_inventario_itens.sql
008_create_view_saldos.sql
009_create_view_estoque_baixo.sql
```

### CUSTOM

```text
custom.categorias
custom.item_categorias
custom.campos
custom.campo_opcoes
custom.valores_item
```

Scripts:

```text
100_create_custom_schema.sql
101_create_categorias.sql
102_create_item_categorias.sql
103_create_campos.sql
104_create_campo_opcoes.sql
105_create_valores_item.sql
106_create_validacoes_custom.sql
```

### AUTH

```text
auth.usuarios
auth.empresa_usuarios
```

Scripts:

```text
110_create_auth_schema.sql
111_create_usuarios.sql
112_create_empresa_usuarios.sql
```

---

## 📊 Saldo de estoque

O saldo não é mantido como um número editável no item.

A fonte de verdade é o histórico de movimentações:

```text
ENTRADAS
+ AJUSTES DE ENTRADA
- SAÍDAS
- AJUSTES DE SAÍDA
= SALDO ATUAL
```

Isso permite:

```text
rastreabilidade
histórico
auditoria operacional
correções por compensação
```

Uma movimentação incorreta não deve ser apagada para esconder o erro.

O modelo esperado é:

```text
movimento incorreto
↓
movimento compensatório
↓
movimento correto
```

---

## 📦 Itens

O cadastro de itens pertence ao CORE.

Um item terá, entre outros dados:

```text
empresa
nome
unidade
estoque mínimo
ativo
```

Características específicas do negócio não devem ser adicionadas diretamente ao CORE.

Exemplo:

```text
cor
marca
material
gramatura
tamanho
impermeável
```

Esses dados pertencem à camada CUSTOM.

### Estado atual

```text
Modelo SQL          → implementado no banco
Modelo ORM          → ainda não é o próximo checkpoint
CRUD API            → próximo passo
```

---

## 🧩 Campos personalizados

Uma empresa pode configurar suas próprias categorias e campos.

Exemplo:

```text
Categoria:
Tecidos
```

Campos:

```text
Cor          → TEXTO_CURTO
Gramatura    → DECIMAL
Impermeável  → BOOLEANO
Preço        → DINHEIRO
Material     → LISTA
```

Tipos planejados para a V1:

```text
TEXTO_CURTO
TEXTO_LONGO
INTEIRO
DECIMAL
DINHEIRO
BOOLEANO
DATA
LISTA
```

A configuração permite adaptar o sistema a diferentes tipos de negócio sem alterar a estrutura principal do estoque.

### Regras importantes

O backend deverá garantir:

```text
campos obrigatórios
opções pertencentes ao campo correto
valores compatíveis com o tipo
isolamento por empresa
campos inativos
opções inativas
recategorização segura
```

---

## 📦 Movimentações e estoque

As movimentações serão responsáveis por registrar:

```text
ENTRADA
SAÍDA
AJUSTE
```

O fluxo futuro deverá respeitar:

```text
requisição
↓
validação
↓
transaction
↓
verificação do saldo
↓
registro da movimentação
↓
commit
```

O estoque negativo será bloqueado por padrão.

Para operações concorrentes no mesmo item, a implementação deverá utilizar transação e mecanismo de serialização/row lock apropriado.

---

## 🔄 Inventário

O inventário compara o saldo registrado pelo sistema com a contagem física.

Exemplo:

```text
Saldo do sistema: 12.5
Contagem física:  12

Diferença: -0.5
```

O resultado esperado é:

```text
AJUSTE_SAIDA 0.5
```

O saldo não deve ser alterado silenciosamente.

A conclusão do inventário deve executar de forma atômica:

```text
calcular diferença
↓
gerar ajustes
↓
concluir inventário
```

---

## 🧪 Testes

O projeto utiliza:

```text
pytest
FastAPI TestClient
SQLAlchemy
PostgreSQL de teste
```

A estratégia inclui:

```text
unit tests
schema tests
database integration tests
service tests
API tests
E2E tests
```

### Testes já implementados

A base atual possui testes para:

```text
configuração
database connection
health
segurança
hash de senha
JWT
expiração de token
token inválido
usuário inativo
AuthService
ORM AUTH
roles
contexto de empresa
isolamento multiempresa
CRUD de empresas
CRUD de unidades
```

A suíte completa foi executada durante o desenvolvimento e está verde após as últimas alterações.

---

## 🚦 Gates do projeto

### Gate A — Banco

**🟢 CONCLUÍDO**

Validado em banco PostgreSQL limpo:

```text
CORE
CORE + CUSTOM
constraints
triggers
views
saldo
inventário
integrações CUSTOM
regras de isolamento
```

Suíte:

```text
tests/database/run_gate_a.sql
```

---

### Gate B — Backend

**🟡 EM ANDAMENTO**

Já concluído:

```text
✅ FastAPI
✅ configuração
✅ conexão PostgreSQL
✅ SQLAlchemy
✅ health
✅ pytest/TestClient
✅ security foundation
✅ AUTH ORM
✅ AuthService
✅ login
✅ current_user
✅ /auth/me
✅ contexto de empresa
✅ roles
✅ isolamento multiempresa
✅ CRUD de Empresas
✅ CRUD de Unidades
```

Ainda pendente:

```text
⏳ CRUD de Itens
⏳ movimentações
⏳ saldo via API
⏳ estoque baixo
⏳ inventário
⏳ API CUSTOM
⏳ paginação completa
⏳ tratamento global de erros
⏳ hardening
⏳ lint
⏳ suíte final
```

---

### Gate C — Frontend

**⚪ PENDENTE**

```text
interface
integração REST
responsividade
autenticação
estados de loading
empty states
tratamento de erros
```

---

### Gate D — E2E

**⚪ PENDENTE**

Fluxo obrigatório:

```text
login
→ empresa
→ unidade
→ categoria
→ campos
→ item
→ entrada
→ saída
→ saldo
→ estoque baixo
→ inventário
→ ajuste
```

---

## 🛡️ Regras de segurança

O projeto utiliza:

```text
Argon2
JWT
OAuth2 Password Flow
variáveis de ambiente
isolamento multiempresa
controle por papel
```

Senhas nunca são armazenadas em texto puro.

Segredos ficam fora do código:

```text
.env
```

E o repositório utiliza:

```text
.env.example
```

sem credenciais reais.

Nunca registrar em logs:

```text
senha
JWT completo
SECRET_KEY
```

---

## 🧱 Regras de integridade

Algumas decisões importantes já estão congeladas.

### Histórico

Movimentações e inventários não devem ser apagados de forma destrutiva.

### Estoque

Não existe quantidade manual no item como fonte principal de verdade.

### Unidade

Quantidade e unidade são conceitos separados:

```text
1.5
+
Rolo
```

### Unidade após histórico

Uma mudança de unidade deve ser bloqueada quando o item já possui movimentações.

### Categoria

A troca de categoria de um item com valores CUSTOM incompatíveis deverá ser bloqueada até que os valores sejam resolvidos.

### Campo obrigatório

Campos CUSTOM obrigatórios serão validados no service, pois a ausência de um valor é representada pela ausência de uma linha em `custom.valores_item`.

---

## 🛠️ Tecnologias

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy 2.x
* Alembic
* PyJWT
* pwdlib
* Argon2
* pytest

### Banco

* PostgreSQL

### Frontend

* React
* Vite
* JavaScript

### Desenvolvimento

* Git
* GitHub
* VS Code

---

## 📁 Organização do banco

A sequência dos scripts foi planejada para facilitar reconstrução de um banco limpo:

```text
database/
├── core/
├── custom/
├── auth/
└── shared/
```

Aplicação completa:

```text
database/apply_all.sql
```

O objetivo é permitir que o ambiente possa ser reconstruído a partir dos scripts versionados.

---

## 💰 Custo

O MVP foi projetado para funcionar com custo obrigatório de:

```text
R$ 0,00
```

Ferramentas principais:

```text
Python       → gratuito
FastAPI      → gratuito
PostgreSQL   → gratuito
SQLAlchemy   → gratuito
Alembic      → gratuito
React        → gratuito
Vite         → gratuito
pytest       → gratuito
Git          → gratuito
GitHub       → gratuito
VS Code      → gratuito
```

O desenvolvimento local não depende de serviços pagos.

Deploy remoto gratuito poderá ser utilizado posteriormente apenas para demonstração, desde que não se torne requisito para concluir a V1.

---

## 🔧 Configuração local

O ambiente utiliza variáveis de ambiente.

Exemplo:

```text
DATABASE_URL=
SECRET_KEY=
ENVIRONMENT=
CORS_ORIGINS=
```

O arquivo real:

```text
.env
```

não deve ser versionado.

Utilize:

```text
.env.example
```

como referência.

### Dependências

As dependências atuais incluem:

```text
fastapi
uvicorn
sqlalchemy
psycopg
pydantic-settings
alembic
pytest
httpx2
pwdlib[argon2]
pyjwt
python-multipart
email-validator
```

As versões devem ser congeladas em um checkpoint posterior, depois do build do backend estar totalmente estabilizado.

---

## 🗺️ Roadmap

```text
[CONCLUÍDO]
Banco CORE + CUSTOM
        ↓
[CONCLUÍDO]
Gate A
        ↓
[CONCLUÍDO]
Fundação Backend
        ↓
[CONCLUÍDO]
AUTH + JWT
        ↓
[CONCLUÍDO]
Multiempresa + Roles
        ↓
[CONCLUÍDO]
CRUD Empresas
        ↓
[CONCLUÍDO]
CRUD Unidades
        ↓
[ATUAL]
CRUD Itens
        ↓
Movimentações + Saldo
        ↓
API CUSTOM
        ↓
Inventários
        ↓
Testes finais do backend
        ↓
Frontend React
        ↓
Integração + UX
        ↓
E2E + Hardening
        ↓
Deploy
```

Prioridade:

```text
integridade
→ funcionamento
→ testes
→ segurança
→ integração
→ interface
→ refinamento
```

---

## 🚧 Status atual

> **Em desenvolvimento — Gate A concluído e núcleo inicial do backend funcional. O próximo passo é implementar o CRUD de Itens.**

### Banco

* [x] Arquitetura CORE
* [x] Arquitetura CUSTOM
* [x] AUTH
* [x] CORE implementado e revisado
* [x] CUSTOM implementado
* [x] Integração CORE + CUSTOM
* [x] Testes automatizados
* [x] Gate A

### Backend

* [x] Arquitetura modular
* [x] Configuração
* [x] PostgreSQL
* [x] SQLAlchemy
* [x] FastAPI
* [x] Health
* [x] pytest/TestClient
* [x] Segurança
* [x] JWT
* [x] Login
* [x] Current user
* [x] `/auth/me`
* [x] Contexto de empresa
* [x] Roles
* [x] Isolamento multiempresa
* [x] CRUD Empresas
* [x] CRUD Unidades
* [ ] CRUD Itens
* [ ] Movimentações
* [ ] Saldo via API
* [ ] Estoque baixo
* [ ] Inventário
* [ ] API CUSTOM
* [ ] Hardening final
* [ ] E2E

### Frontend

* [x] Stack definida
* [ ] Interface
* [ ] Login
* [ ] Dashboard
* [ ] Gestão de itens
* [ ] Movimentações
* [ ] Inventário
* [ ] CUSTOM
* [ ] Integração REST
* [ ] Responsividade
* [ ] Testes de fluxo

---

## 🔄 Fluxo de desenvolvimento

O projeto é desenvolvido de forma incremental:

```text
auditar
→ decidir
→ implementar
→ executar
→ testar
→ tentar quebrar
→ corrigir
→ documentar
→ commit
→ próxima etapa
```

Nenhuma regra crítica é considerada concluída apenas porque o código foi escrito.

A implementação precisa ser:

```text
executada
+
testada
+
validada
```

---

## 🌱 Desenvolvimento solo

O Estoque Flex é desenvolvido integralmente por **Gabriel Almeida**.

A estratégia atual prioriza:

```text
microetapas
+
testes frequentes
+
checkpoints Git
+
documentação viva
```

O projeto não depende da divisão original de tarefas entre integrantes.

GitHub é utilizado como:

```text
backup
histórico
checkpoint
versionamento
base para CI futura
```

Repositório:

```text
GabrielJalmeida/baby-belo
```

---

## 🧭 Próximo passo

O próximo domínio a ser implementado é:

```text
CORE → ITENS
```

A sequência planejada é:

```text
modelo ORM do Item
↓
schemas
↓
service
↓
router
↓
isolamento por empresa
↓
validação de unidade
↓
estoque mínimo
↓
PATCH
↓
testes
↓
checkpoint Git
```

Depois:

```text
Itens
↓
Movimentações
↓
Saldo
↓
Estoque baixo
```

A implementação de CUSTOM e Inventários ocorrerá depois que o núcleo operacional do estoque estiver funcionando.

---

## 📌 Decisões arquiteturais importantes

Estas decisões não devem ser alteradas sem motivo técnico ou evidência dos testes:

```text
PostgreSQL
FastAPI
SQLAlchemy 2.x
Alembic
pytest
React + Vite
REST
Modular Monolith
CORE independente
CUSTOM → CORE
AUTH → CORE
CORE → AUTH proibido
saldo baseado em movimentações
quantidade NUMERIC(18,4)
unidade separada da quantidade
histórico preservado
inventário gera ajustes
estoque negativo bloqueado por padrão
multiempresa
JWT com sub = user_id
empresa não fixada no JWT
email case-insensitive unique
Argon2 para senhas
```

---

## 📚 Documentação

Documentos principais:

```text
docs/
├── PLANO_BANCO_ESTOQUE_FLEX.md
├── ESTOQUE_FLEX_PLANO_MESTRE_V1.md
├── GUIA_BACKEND_INICIANTE_ESTOQUE_FLEX.md
└── ESTOQUE_FLEX_PLANO_MESTRE_V2.1_CONTINUIDADE.md
```

O **Plano Mestre V2/V2.1** é a principal referência de continuidade do desenvolvimento.

---

## 📈 Visão futura

Depois da V1, o projeto poderá evoluir para:

```text
relatórios
dashboard analítico
previsão de reposição
auditoria por usuário
ficha técnica de produção
código de barras
fornecedores
importação/exportação
conversão entre unidades
integrações externas
```

Esses recursos não fazem parte do núcleo obrigatório da V1.

---

<p align="center">
  <strong>Estoque Flex</strong><br>
  Flexible inventory architecture for real-world businesses.
</p>
