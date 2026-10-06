# 📦 Estoque Flex

<p align="center">
  <strong>Sistema web de estoque flexível, configurável e multiempresa.</strong>
</p>

<p align="center">
  Controle de estoque com uma estrutura fixa para regras críticas e uma camada configurável para diferentes tipos de negócio.
</p>

---

## ✨ Sobre o projeto

O **Estoque Flex** é um sistema de gerenciamento de estoque pensado para pequenos negócios que precisam de controle confiável sem perder flexibilidade.

A arquitetura separa:

```text
CORE
→ controla o estoque

CUSTOM
→ descreve e personaliza o estoque
```

Assim, as regras fundamentais permanecem estáveis enquanto cada empresa pode configurar categorias, campos personalizados, opções e valores sem alterar o núcleo do estoque.

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

- cadastro de empresas;
- unidades de medida;
- itens;
- entradas, saídas e ajustes;
- saldo calculado por histórico;
- estoque mínimo;
- inventário físico;
- categorias configuráveis;
- campos personalizados;
- opções para campos do tipo lista;
- valores personalizados;
- arquitetura multiempresa;
- uso em desktop e dispositivos móveis.

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

Regra de dependência:

```text
CUSTOM → CORE ✅
CORE → CUSTOM ❌
```

---

## 🏗️ Arquitetura do backend

O backend será um **modular monolith**.

Fluxo principal:

```text
HTTP / Router
      ↓
Pydantic Schema
      ↓
Service / regra de negócio
      ↓
SQLAlchemy
      ↓
PostgreSQL
```

O `main.py` permanece pequeno e atua como ponto de montagem da aplicação. Regras de negócio não devem ser concentradas nele.

Estrutura-alvo:

```text
backend/
├── app/
│   ├── main.py
│   ├── shared/
│   ├── health/
│   ├── auth/
│   ├── core/
│   │   ├── empresas/
│   │   ├── unidades/
│   │   └── itens/
│   ├── stock/
│   │   ├── movimentacoes/
│   │   ├── saldos/
│   │   └── inventarios/
│   └── custom/
│       ├── categorias/
│       ├── campos/
│       ├── campo_opcoes/
│       └── valores_item/
├── tests/
├── requirements.txt
└── .env.example
```

### Estado atual do backend

A fundação começou com:

```text
backend/app/main.py
backend/app/core/
backend/app/db/
```

O primeiro endpoint já está definido:

```text
GET /api/v1/health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

A fundação completa ainda precisa passar pelo Gate do backend, incluindo configuração, conexão PostgreSQL, testes com pytest/TestClient e validação de `SELECT 1`.

---

## 🗄️ Banco de dados

O projeto utiliza **PostgreSQL**.

### CORE

Implementado:

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

Scripts CORE:

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

Implementado:

```text
custom.categorias
custom.item_categorias
custom.campos
custom.campo_opcoes
custom.valores_item
```

Scripts CUSTOM:

```text
100–106
```

---

## 📊 Saldo de estoque

O saldo não é mantido como um número editável no item.

Ele é derivado do histórico:

```text
ENTRADAS
+ AJUSTES DE ENTRADA
- SAÍDAS
- AJUSTES DE SAÍDA
= SALDO ATUAL
```

Isso mantém as movimentações como fonte de verdade e preserva o histórico.

---

## 📏 Quantidade e unidade

Quantidade e unidade são separadas.

Exemplos:

```text
12.75 Metros
1.5 Rolos
20 Unidades
3.2 Kg
```

Cada unidade pode definir se aceita valores decimais.

Itens que já possuem movimentações não podem trocar de unidade, preservando a coerência histórica.

---

## 🧩 Campos personalizados

Uma empresa pode criar a categoria:

```text
Tecidos
```

e definir seus próprios campos:

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

O banco também protege regras como isolamento por empresa, tipos de valores, opções pertencentes ao campo correto, campos inativos e recategorização de itens com valores personalizados.

---

## 🔄 Inventário

O inventário compara saldo do sistema e contagem física.

Exemplo:

```text
Saldo do sistema: 12.5
Contagem física:   12
Diferença:         -0.5
```

Resultado:

```text
AJUSTE_SAIDA 0.5
```

O saldo não é alterado silenciosamente.

A conclusão do inventário deve gerar os ajustes de forma atômica.

---

## 🧪 Testes e Gates

A estratégia inclui:

```text
unit tests
schema tests
database integration tests
service tests
API tests
end-to-end tests
```

### Gate A — Banco

O Gate A do banco está **verde**.

Foram validados em banco limpo:

- CORE isoladamente;
- CORE + CUSTOM;
- constraints;
- triggers;
- views;
- isolamento multiempresa;
- cálculo de saldo;
- inventário e ajustes;
- regras de integração do CUSTOM.

A suíte automatizada está em:

```text
tests/database/run_gate_a.sql
```

Execução:

```text
psql -U postgres -d estoque_flex_test -v ON_ERROR_STOP=1 -f tests/database/run_gate_a.sql
```

Resultado esperado:

```text
GATE A: TODOS OS TESTES PASSARAM
```

### Próximo gate

O próximo objetivo é o **Gate B — Backend**:

```text
GET /api/v1/health → 200
SELECT 1 → sucesso
pytest → verde
```

---

## 🔐 Segurança e multiempresa

A aplicação deve impedir que uma empresa acesse ou relacione registros de outra.

Exemplo inválido:

```text
Item da Empresa A
+
Categoria da Empresa B
```

A validação será feita em múltiplas camadas:

```text
Frontend
↓
API / Pydantic
↓
Service
↓
PostgreSQL
```

O banco já possui proteções importantes contra relações entre empresas diferentes. A camada de API ainda deverá aplicar o isolamento por usuário/empresa quando a autenticação for implementada.

---

## 👤 Desenvolvimento

Fluxo de desenvolvimento:

```text
entender a etapa
→ decidir
→ implementar
→ executar
→ testar
→ explicar o resultado
→ avançar
```

As partes críticas devem ser executadas e testadas antes de serem consideradas concluídas.

---

## 🛠️ Tecnologias

### Backend

- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic
- pytest

### Banco

- PostgreSQL

### Frontend

- React
- Vite
- JavaScript

### Desenvolvimento

- Git
- GitHub
- VS Code

---

## 🚧 Status atual

> **Em desenvolvimento — Gate A do banco concluído; fundação do backend em andamento.**

### Banco

- [x] Arquitetura CORE definida
- [x] Arquitetura CUSTOM definida
- [x] CORE implementado e revisado
- [x] CUSTOM 100–106 implementado
- [x] Integração CORE + CUSTOM
- [x] Testes automatizados do banco
- [x] Gate A verde

### Backend

- [x] Arquitetura definida
- [x] Esqueleto FastAPI inicial
- [x] Endpoint `GET /api/v1/health` definido
- [ ] Configuração da aplicação
- [ ] Conexão SQLAlchemy/PostgreSQL
- [ ] `SELECT 1`
- [ ] pytest/TestClient
- [ ] Tratamento inicial de erros
- [ ] Autenticação
- [ ] CRUDs
- [ ] Movimentações
- [ ] Inventário
- [ ] API CUSTOM

### Frontend

- [x] Stack definida
- [ ] Interface
- [ ] Integração REST
- [ ] Responsividade
- [ ] Testes de fluxo

---

## 🗺️ Roadmap

```text
[CONCLUÍDO]
Banco CORE + CUSTOM
        ↓
[CONCLUÍDO]
Testes automatizados + Gate A
        ↓
[ATUAL]
Fundação FastAPI
        ↓
Auth + multiempresa
        ↓
CRUD CORE
        ↓
Movimentações + saldo
        ↓
API CUSTOM
        ↓
Inventários
        ↓
Frontend React
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
→ integração
→ interface
→ refinamento
```

---

## 💰 Custo

O projeto foi planejado para poder ser desenvolvido com ferramentas gratuitas.

```text
Python       → gratuito
FastAPI      → gratuito
PostgreSQL   → gratuito
SQLAlchemy   → gratuito
React        → gratuito
Vite         → gratuito
Git/GitHub   → gratuito
pytest       → gratuito
VS Code      → gratuito
```

---

## 💡 Visão futura

Possíveis evoluções:

- relatórios;
- dashboard analítico;
- previsão de reposição;
- auditoria por usuário;
- ficha técnica de produção;
- código de barras;
- fornecedores;
- importação/exportação;
- conversão entre unidade de compra e unidade de consumo;
- integrações externas.

---

<p align="center">
  <strong>Estoque Flex</strong><br>
  Flexible inventory architecture for real-world businesses.
</p>
