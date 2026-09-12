# 📦 Estoque Flex

<p align="center">
  <strong>Sistema web de estoque flexível, configurável e multiempresa.</strong>
</p>

<p align="center">
  Controle de estoque com uma estrutura fixa para regras críticas e uma camada configurável para diferentes tipos de negócio.
</p>

---

## ✨ Sobre o projeto

O **Estoque Flex** é um sistema de gerenciamento de estoque pensado inicialmente para uma empresa de produção personalizada, mas sua arquitetura evoluiu para um modelo genérico e configurável.

A ideia central é separar:

```text
CORE
→ controla o estoque

CUSTOM
→ descreve o estoque
```

Assim, a estrutura principal continua estável enquanto cada empresa pode criar suas próprias categorias, unidades, campos personalizados e opções de cadastro.

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

## 🏗️ Estrutura

```text
estoque-flex/
├── backend/
├── database/
│   ├── core/
│   ├── custom/
│   └── shared/
├── docs/
├── frontend/
├── tests/
├── .gitignore
└── README.md
```

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

Views planejadas:

```text
core.vw_saldos_estoque
core.vw_itens_estoque_baixo
```

### CUSTOM

```text
custom.categorias
custom.item_categorias
custom.campos
custom.campo_opcoes
custom.valores_item
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

Isso evita manter duas fontes diferentes de verdade.

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

---

## 🛠️ Tecnologias

### Backend
- Python
- FastAPI
- SQLAlchemy
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

## 🧪 Testes

A estratégia inclui:

```text
unit tests
schema tests
database integration tests
service tests
API tests
end-to-end tests
```

Casos críticos:

- mistura de dados entre empresas;
- movimentações inválidas;
- saída maior que o saldo;
- campos personalizados com tipos incorretos;
- opções pertencentes ao campo errado;
- inventário e ajustes;
- concorrência em movimentações.

---

## 👥 Desenvolvimento em equipe

O backend foi dividido por risco e complexidade.

### Domain / Integration
Responsável por:
- arquitetura;
- integrações;
- movimentações;
- inventário;
- transações;
- multiempresa;
- módulo CUSTOM avançado;
- testes de integração.

### CORE
Responsável por:
- empresas;
- unidades;
- itens;
- CRUDs principais;
- consultas simples.

### Backend Apprentice
Responsável inicialmente por:
- health check;
- schemas Pydantic;
- testes simples;
- rotas de baixo risco;
- posteriormente um CRUD simples seguindo um módulo de referência.

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

---

## 🚧 Status

> **Em desenvolvimento**

### Banco
- [x] Arquitetura CORE definida
- [x] Arquitetura CUSTOM definida
- [x] Scripts CUSTOM planejados
- [ ] Testes automatizados do CUSTOM
- [ ] Revisão do CORE real
- [ ] Integração CORE + CUSTOM

### Backend
- [x] Arquitetura planejada
- [x] Divisão de responsabilidades
- [ ] Fundação FastAPI
- [ ] Autenticação
- [ ] CRUDs
- [ ] Movimentações
- [ ] Inventário
- [ ] Integração completa

### Frontend
- [x] Stack definida
- [ ] Interface
- [ ] Integração REST
- [ ] Responsividade
- [ ] Testes de fluxo

---

## 📚 Documentação

A pasta `docs/` concentra planejamento e decisões técnicas.

Documentos principais:

```text
PLANO_BANCO_ESTOQUE_FLEX.md
ESTOQUE_FLEX_PLANO_MESTRE_V1.md
GUIA_BACKEND_INICIANTE_ESTOQUE_FLEX.md
```

---

## 🗺️ Roadmap

```text
Banco CORE + CUSTOM
        ↓
Testes automatizados
        ↓
FastAPI + SQLAlchemy
        ↓
Autenticação + CRUDs
        ↓
Movimentações + Saldo
        ↓
Inventário
        ↓
Integração CUSTOM
        ↓
Frontend
        ↓
E2E + Hardening
        ↓
Deploy
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

## 📌 Prioridade atual

```text
integridade
→ funcionamento
→ testes
→ integração
→ interface
→ refinamento
```

<p align="center">
  <strong>Estoque Flex</strong><br>
  Flexible inventory architecture for real-world businesses.
</p>
