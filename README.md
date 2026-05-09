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
```

Veja `CONTRIBUTING.md` pra adicionar um projeto novo.

## License

Apache 2.0 — veja `LICENSE`.
