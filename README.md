# fiap-mba-multi-agent

Monorepo open-source para projetos do MBA FIAP em [AI Engineering & Multi-Agents](https://www.fiap.com.br/mba/mba-em-ai-engineering-multi-agents/).

Cada grupo/pessoa contribui com apps Python (e/ou frontends estáticos) em `apps/<grupo>/<projeto>/`. Uma homepage central lista todos os projetos e os monta em paths dedicados via FastAPI sub-app mounts.

## Stack

- Python 3.13 + FastAPI
- `uv` (workspace + venv + lockfile)
- Deploy: Railway (single service, single DNS)

## Quickstart

```bash
uv sync
uv run uvicorn homepage.main:app --reload
# http://localhost:8000
```

## Como contribuir

Veja [CONTRIBUTING.md](./CONTRIBUTING.md) — em uma linha:

```bash
uv run scripts/new_project.py --group <grupo> --slug <slug> --kind backend \
  --description "..." --members "Seu Nome"
```

## Deploy

Rodando ao vivo no Railway. Cada push na `main` redeploya automaticamente.

## License

Apache 2.0 — veja `LICENSE`.
