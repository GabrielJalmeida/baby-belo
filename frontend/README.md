# Baby Belo — frontend oficial

React 19 e Vite. A landing page é a entrada; o acesso ao estoque exige autenticação real na API FastAPI. Há uma única interface administrativa.

## Ambiente local já preparado

Na raiz do repositório:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Abra http://127.0.0.1:5174/. No primeiro uso, crie sua própria conta em outro terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/create-owner.ps1
```

Informe nome, e-mail e uma senha pessoal. No nome da empresa, informe **Baby Belo Ateliê**. A senha é solicitada sem ser exibida. Não há conta nem senha fixa no frontend.

Instruções completas: [Execução local](../docs/EXECUCAO_LOCAL.md).

## Desenvolvimento do frontend

```powershell
cd frontend
npm ci
npm run dev
```

O Vite encaminha `/api` para `http://127.0.0.1:8000`. Fora do Vite, a infraestrutura precisa encaminhar esse caminho para a API, ou definir `VITE_API_BASE_URL` na compilação e autorizar a origem no backend. Nenhuma configuração de produção ou deploy foi feita.

## Telas integradas

Login, dashboard, produtos (cadastro, edição, detalhes, pesquisa e inativação), unidades de medida, entradas/saídas e ajustes, histórico por produto, inventários, estoque baixo, categorias, campos personalizados e opções de listas.

A API existente usa **inativação** em vez de exclusão permanente, preservando o histórico. Não há endpoint DELETE de produtos. A interface confirma essa operação antes de executá-la.

O vínculo do usuário com o Baby Belo é resolvido pela lista de empresas autorizadas e confirmado pelo endpoint de permissões. Não há ID de empresa fixo, seleção de empresa nem alteração do nome da empresa na interface. Vínculos ausentes ou ambíguos bloqueiam o acesso com uma mensagem clara.

Configurações oferece modo noturno, três tamanhos de fonte, alto contraste e links sublinhados. Preferências ficam no localStorage e se aplicam também à landing page e ao login. A sessão usa o token real retornado pela API, em sessionStorage, e é encerrada no logout ou ao receber uma resposta de sessão expirada.

## Verificações

```powershell
npm test
npm run lint
npm run build
```

Os testes de contrato usam respostas isoladas somente dentro de `tests/integration.test.js`. A aplicação não contém dados demonstrativos.

Para testar o cliente HTTP contra FastAPI e PostgreSQL reais, execute na raiz:

```powershell
.\.venv\Scripts\python.exe scripts/test-live.py
```

Esse teste cria contas aleatórias e dados apenas em `baby_belo_test`, inicia uma API temporária na porta 8001 e a encerra ao finalizar. Credenciais de teste não são mostradas nem gravadas no frontend.

## Referência visual

A estrutura aprovada da landing page foi preservada, com a entrada para o estoque e sem links comerciais. Fotos e logo ainda são recortes visuais da imagem fornecida, em `public/reference.png`. Os arquivos originais e as fontes exatas do Figma não vieram no repositório. Os conteúdos provisórios da referência permanecem sinalizados.

