# Design: `fiap-mba-multi-agent`

**Status:** Draft
**Date:** 2026-05-08
**Author:** Gabriel Dantas
**License:** Apache 2.0

## Context

Repositório monorepo open-source para alunos do MBA FIAP em AI Engineering & Multi-Agents
(<https://www.fiap.com.br/mba/mba-em-ai-engineering-multi-agents/>) hospedarem projetos
desenvolvidos durante o curso. Cada grupo/pessoa contribui com apps independentes (Python
backends e/ou frontends estáticos), e uma homepage central lista grupos e seus projetos
com links de acesso.

## Goals

- Permitir múltiplos grupos e pessoas trabalhando em apps isolados sem conflito.
- Manter o projeto open-source e contribuível via PR no GitHub.
- Deploy único no Railway, único service, único DNS — economia e simplicidade.
- Suportar tanto backends Python quanto frontends estáticos.
- CI com lint e feedback inline no PR pra ensinar boas práticas.
- Onboarding de novo projeto deve ser um único comando.

## Non-Goals (YAGNI)

- Autenticação/login na homepage (showcase público).
- Banco de dados central — cada app traz o seu se precisar.
- Hot reload de apps novas sem redeploy.
- Isolamento real de secrets por app (vars Railway com prefixo bastam).
- Multi-region deploy.
- Frontend SSR/Node — apenas estático. Quem precisar de Next.js sério, deploya em
  service Railway separado por conta própria e linka via `deploy_url` externo.

## Architecture

### Single-service path-based routing

Uma instância FastAPI roda na raiz e monta cada app filha como sub-aplicação ASGI
em path próprio. Isso permite um único container, único DNS, e zero CORS entre apps.

```
Request: /grupo-alpha/chatbot-rag/api/chat
                ↓
Homepage FastAPI (root)
                ↓
app.mount("/grupo-alpha/chatbot-rag", chatbot_rag.app)
                ↓
Sub-app FastAPI do projeto recebe /api/chat
```

Frontends estáticos viram `StaticFiles` mounts no mesmo padrão.

### Repo layout

```
fiap-mba-multi-agent/
├── apps/
│   └── <grupo>/
│       └── <projeto>/
│           ├── project.yaml          # metadados (nome, membros, kind, mount_path…)
│           ├── pyproject.toml        # deps específicas (uv workspace member)
│           ├── main.py               # backend: expõe `app` ASGI
│           ├── tests/                # opcional, ativado via project.yaml
│           └── dist/                 # frontend: build estático (gerado em CI)
├── homepage/
│   ├── main.py                       # FastAPI raiz; descobre e monta apps
│   ├── loader.py                     # scan + validação dos project.yaml
│   ├── schema.py                     # Pydantic models do project.yaml
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html                # lista grupos/projetos
│   └── static/
├── scripts/
│   └── new_project.py                # scaffold de novo projeto
├── .github/workflows/
│   ├── ci.yml                        # lint, schema check, paths-filter
│   └── pr-comment.yml                # bot resumo + reviewdog
├── pyproject.toml                    # uv workspace root
├── uv.lock
├── Dockerfile
├── railway.json
├── LICENSE                           # Apache 2.0
├── README.md
└── docs/
    └── superpowers/specs/...
```

## Components

### 1. `project.yaml` (manifest por app)

Cada app em `apps/<grupo>/<projeto>/` declara um manifest validado por schema Pydantic.

```yaml
name: "Chatbot RAG"
slug: chatbot-rag
description: "Chatbot com RAG sobre documentação interna"
group: grupo-alpha
members:
  - Gabriel Dantas
  - Maria Silva
kind: backend            # backend | frontend | fullstack
mount_path: /grupo-alpha/chatbot-rag
entry: "apps.grupo_alpha.chatbot_rag.main:app"   # backend only
static_dir: dist                                 # frontend only (relativo ao projeto)
enabled: true
checks:
  pytest: false
  mypy: false
```

Regras:

- **Naming**: pastas em `apps/` usam underscore (`grupo_alpha/chatbot_rag/`) pra serem
  módulos Python válidos (necessário pro `entry`). O `slug` e `group` em YAML, e o
  `mount_path`, usam hyphen (`grupo-alpha`, `chatbot-rag`) por convenção URL-friendly.
  O scaffold faz a tradução automática.
- `slug` (com hyphen) traduzido em underscore precisa bater com nome da pasta.
- `mount_path` deve ser exatamente `/<group>/<slug>` (validado).
- `kind: backend` exige `entry`. `kind: frontend` exige `static_dir`. `kind: fullstack`
  exige ambos — o backend é montado em `mount_path/api` e o estático em `mount_path`.
- `enabled: false` faz a homepage listar como "offline" sem tentar montar.

### 2. Homepage (`homepage/`)

- **`schema.py`** — modelos Pydantic do `project.yaml`. Erro de validação aborta boot
  com mensagem clara apontando o arquivo.
- **`loader.py`** — `discover()` faz glob `apps/**/project.yaml`, valida cada um,
  retorna `list[ProjectConfig]`. Logs cobrem: descoberto, válido, montado, falhou.
- **`main.py`** — FastAPI raiz. No startup:
  1. `loader.discover()`
  2. Pra cada manifest válido com `enabled: true`:
     - `kind in (backend, fullstack)`: `importlib.import_module(entry)`,
       `app.mount(mount_path, sub_app)`. Falha de import é capturada e flagada como
       "broken" — não derruba o boot.
     - `kind in (frontend, fullstack)`: `app.mount(mount_path, StaticFiles(directory=..., html=True))`.
  3. Index `/` renderiza `index.html` com lista agrupada por `group`, mostrando
     status (online/offline/broken) por card.

### 3. CI (`.github/workflows/`)

**`ci.yml`** — disparado em PR e push pra `main`:

- Step `paths-filter`: detecta quais `apps/<grupo>/<projeto>/` mudaram + se `homepage/`
  ou raiz mudou (caso global).
- Steps sempre executados:
  - `ruff check` no repo inteiro (rápido).
  - `ruff format --check` no repo inteiro.
  - Validação de schema: roda `python -m homepage.loader --validate-only` que checa
    todos os `project.yaml`.
- Steps por app afetada (matriz dinâmica):
  - Se `checks.pytest: true`: `uv run pytest apps/<grupo>/<projeto>/tests/`
  - Se `checks.mypy: true`: `uv run mypy apps/<grupo>/<projeto>/`
- Frontend: se app afetada tem `kind: frontend` e existe `package.json`, roda
  `npm ci && npm run build` e arquiva `dist/` como artifact.

**`pr-comment.yml`** — depende de `ci.yml`:

- `reviewdog` consome saída do `ruff` e posta comentários inline em linhas com problema.
- Bot custom (`actions/github-script`) posta um comentário sticky no PR com tabela:

  | App | Lint | Tests | Types |
  |---|---|---|---|
  | grupo-alpha/chatbot-rag | ✅ | ⚪ skipped | ⚪ skipped |
  | grupo-beta/agent-vendas | ✅ | ✅ | ❌ |

  Atualiza o mesmo comentário em cada push.

### 4. Scaffold (`scripts/new_project.py`)

```bash
uv run scripts/new_project.py --group grupo-alpha --slug chatbot-rag --kind backend
```

Gera:

- `apps/grupo_alpha/chatbot_rag/` (slug com underscore para nome de módulo Python)
- `project.yaml` preenchido com defaults
- `pyproject.toml` membro do workspace, com `fastapi` como dep base
- `main.py` com FastAPI hello-world expondo `app`
- Atualiza `pyproject.toml` raiz adicionando ao `[tool.uv.workspace]`

Validações: bloqueia se grupo/slug já existe, valida slug regex, valida kind.

### 5. Deploy (Railway)

**`Dockerfile`** (raiz):

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
COPY apps/ apps/
COPY homepage/ homepage/
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "uvicorn", "homepage.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**`railway.json`** — declara o builder Dockerfile, healthcheck em `/health`, restart policy.

Frontend builds rodam em CI e o `dist/` é commitado? **Não.** Em vez disso, o
`Dockerfile` tem um stage Node opcional que detecta `apps/**/package.json` e roda
`npm ci && npm run build` antes do stage Python. Mantém o repo limpo.

Variáveis de ambiente: prefixo por app, ex `GRUPO_ALPHA_CHATBOT_RAG_OPENAI_API_KEY`.
Cada app lê seu prefixo no startup (helper em `homepage/env.py`).

## Data Flow

1. **Boot:** Railway sobe container → `homepage.main:app` startup hook → `loader.discover()`
   varre `apps/**/project.yaml` → valida → importa entries / monta StaticFiles → FastAPI fica pronto.
2. **Request:** Cliente acessa `/grupo-alpha/chatbot-rag/api/chat` → FastAPI roteia
   pelo mount → sub-app FastAPI do projeto trata `/api/chat`.
3. **PR:** Push → GH Actions `ci.yml` → `paths-filter` decide matriz → lint/schema
   sempre, pytest/mypy condicional → `pr-comment.yml` consome resultados → reviewdog
   inline + sticky comment.
4. **Merge na main:** Railway webhook → rebuild Dockerfile → swap container.

## Error Handling

- **Manifest inválido:** boot aborta com mensagem clara apontando arquivo + linha.
  Decisão consciente: melhor falhar rápido em deploy do que ter projeto fantasma.
- **Import de entry falha:** capturado per-app, projeto fica como "broken" na home,
  outros apps continuam normais.
- **Conflito de `mount_path`:** detectado no loader, aborta boot.
- **App backend faz raise não tratado em request:** FastAPI já isola — só aquela request
  retorna 500, processo continua.
- **CI falha:** PR não pode mergear (branch protection na `main` exige checks ✅).

## Testing Strategy

- **Homepage:** `pytest` cobrindo `loader.discover()` (manifests válidos/inválidos,
  conflitos), `main.py` boot com fixtures de apps sintéticas, render de templates.
- **Apps:** opt-in via `checks.pytest: true` no manifest. Cada grupo decide.
- **CI próprio:** workflow é testado fazendo PR de exemplo durante setup inicial.

## Open Questions

- Branch protection rules: sugerir "1 review + checks ✅" ou só checks pra MBA? *Decisão
  pra hora do setup do GitHub repo.*
- Algum grupo vai precisar de WebSocket? FastAPI mounts suportam, mas vale validar quando
  surgir o caso.

## Implementation Phases

1. **Bootstrap repo** — estrutura base, `pyproject.toml` workspace, `LICENSE`, `README`,
   `Dockerfile`, `railway.json`.
2. **Homepage MVP** — `schema.py`, `loader.py`, `main.py`, templates básicos, rota `/health`.
3. **App de exemplo** — `apps/exemplo/hello-world/` (backend) + `apps/exemplo/hello-static/`
   (frontend) provando o fluxo end-to-end.
4. **CI** — `ci.yml` + `pr-comment.yml`.
5. **Scaffold** — `scripts/new_project.py`.
6. **Docs de contribuição** — README + `CONTRIBUTING.md` explicando como abrir PR de novo projeto.
7. **Deploy inicial no Railway** — link do projeto, primeira deploy validada.
