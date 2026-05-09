# fiap-mba-multi-agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap an open-source monorepo for FIAP MBA AI Engineering students that hosts multiple Python backends and static frontends behind a single FastAPI homepage, deployed as one Railway service with path-based routing.

**Architecture:** uv workspace with one package per app under `apps/<group>/<project>/`. The homepage FastAPI app discovers each app's `project.yaml` at startup, validates with Pydantic, and dynamically mounts ASGI sub-apps (backends) and `StaticFiles` (frontends) at the declared `mount_path`. Single Docker image, single Railway service, single DNS.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, Jinja2, `uv` (workspace + venv), `ruff`, `pytest`, GitHub Actions, `reviewdog`, Railway, Docker.

---

## File Structure

**Created in this plan:**
- `pyproject.toml` — uv workspace root, declares `homepage` package and `apps/**` members
- `.python-version` — pins 3.13
- `.gitignore`, `LICENSE` (Apache 2.0), `README.md`, `CONTRIBUTING.md`
- `homepage/__init__.py`, `homepage/schema.py`, `homepage/loader.py`, `homepage/main.py`
- `homepage/templates/base.html`, `homepage/templates/index.html`
- `homepage/static/styles.css`
- `homepage/tests/__init__.py`, `homepage/tests/conftest.py`, `homepage/tests/test_schema.py`, `homepage/tests/test_loader.py`, `homepage/tests/test_main.py`
- `apps/exemplo/hello_backend/{project.yaml,pyproject.toml,main.py}`
- `apps/exemplo/hello_frontend/{project.yaml,pyproject.toml,dist/index.html}`
- `scripts/new_project.py`
- `Dockerfile`, `railway.json`, `.dockerignore`
- `.github/workflows/ci.yml`, `.github/workflows/pr-comment.yml`
- `.ruff.toml`

---

## Task 1: Workspace bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `.ruff.toml`
- Create: `LICENSE`
- Create: `README.md`

- [ ] **Step 1: Create `.python-version`**

```
3.13
```

- [ ] **Step 2: Create root `pyproject.toml`**

```toml
[project]
name = "fiap-mba-multi-agent"
version = "0.1.0"
description = "Monorepo FIAP MBA AI Engineering & Multi-Agents"
requires-python = ">=3.13"
license = { text = "Apache-2.0" }
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pydantic>=2.9",
    "pyyaml>=6.0",
    "jinja2>=3.1",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.7",
]

[tool.uv.workspace]
members = ["apps/*/*"]

[tool.uv.sources]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["homepage/tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["homepage"]
```

- [ ] **Step 3: Create `.ruff.toml`**

```toml
target-version = "py313"
line-length = 100

[lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[lint.per-file-ignores]
"**/tests/**" = ["B"]
```

- [ ] **Step 4: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.uv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
*.egg-info/
dist/
build/
.DS_Store
.env
.env.local
node_modules/
```

- [ ] **Step 5: Create `LICENSE` (Apache 2.0)**

Use the standard Apache 2.0 text. Run:

```bash
curl -sSL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
```

- [ ] **Step 6: Create initial `README.md`**

```markdown
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
```

- [ ] **Step 7: Initialize uv lockfile**

Run: `uv sync`
Expected: creates `.venv/` and `uv.lock`. No errors.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .python-version .gitignore .ruff.toml LICENSE README.md uv.lock
git commit -m "feat: bootstrap uv workspace with Python 3.13 and FastAPI"
```

---

## Task 2: Pydantic schema for `project.yaml`

**Files:**
- Create: `homepage/__init__.py`
- Create: `homepage/schema.py`
- Create: `homepage/tests/__init__.py`
- Create: `homepage/tests/test_schema.py`

- [ ] **Step 1: Create empty package init files**

```bash
mkdir -p homepage/tests
touch homepage/__init__.py homepage/tests/__init__.py
```

- [ ] **Step 2: Write failing tests in `homepage/tests/test_schema.py`**

```python
import pytest
from pydantic import ValidationError

from homepage.schema import ProjectConfig, ProjectKind


def _base(**overrides):
    data = {
        "name": "Hello",
        "slug": "hello",
        "description": "demo",
        "group": "exemplo",
        "members": ["Gabriel"],
        "kind": "backend",
        "mount_path": "/exemplo/hello",
        "entry": "apps.exemplo.hello.main:app",
    }
    data.update(overrides)
    return data


def test_backend_requires_entry():
    with pytest.raises(ValidationError, match="entry"):
        ProjectConfig(**_base(entry=None))


def test_frontend_requires_static_dir():
    with pytest.raises(ValidationError, match="static_dir"):
        ProjectConfig(**_base(kind="frontend", entry=None, static_dir=None))


def test_fullstack_requires_both():
    cfg = ProjectConfig(**_base(kind="fullstack", static_dir="dist"))
    assert cfg.entry is not None
    assert cfg.static_dir == "dist"


def test_mount_path_must_match_group_and_slug():
    with pytest.raises(ValidationError, match="mount_path"):
        ProjectConfig(**_base(mount_path="/wrong/path"))


def test_slug_hyphen_to_underscore_module_path():
    cfg = ProjectConfig(**_base(slug="chat-bot", mount_path="/exemplo/chat-bot",
                                entry="apps.exemplo.chat_bot.main:app"))
    assert cfg.slug == "chat-bot"
    assert cfg.module_dir == "chat_bot"


def test_defaults():
    cfg = ProjectConfig(**_base())
    assert cfg.enabled is True
    assert cfg.checks.pytest is False
    assert cfg.checks.mypy is False


def test_kind_enum():
    assert ProjectKind("backend") is ProjectKind.BACKEND
    with pytest.raises(ValueError):
        ProjectKind("invalid")
```

- [ ] **Step 3: Run tests, expect failure**

Run: `uv run pytest homepage/tests/test_schema.py -v`
Expected: ImportError or ModuleNotFoundError on `homepage.schema`.

- [ ] **Step 4: Implement `homepage/schema.py`**

```python
"""Pydantic schema for project.yaml manifests."""
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field, model_validator

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class ProjectKind(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"


class ProjectChecks(BaseModel):
    pytest: bool = False
    mypy: bool = False


class ProjectConfig(BaseModel):
    name: str
    slug: str = Field(pattern=SLUG_RE.pattern)
    description: str
    group: str = Field(pattern=SLUG_RE.pattern)
    members: list[str] = Field(min_length=1)
    kind: ProjectKind
    mount_path: str
    entry: str | None = None
    static_dir: str | None = None
    enabled: bool = True
    checks: ProjectChecks = Field(default_factory=ProjectChecks)

    @property
    def module_dir(self) -> str:
        return self.slug.replace("-", "_")

    @property
    def group_dir(self) -> str:
        return self.group.replace("-", "_")

    @model_validator(mode="after")
    def _validate_kind_fields(self) -> ProjectConfig:
        if self.kind in (ProjectKind.BACKEND, ProjectKind.FULLSTACK) and not self.entry:
            raise ValueError(f"kind={self.kind.value} requires `entry`")
        if self.kind in (ProjectKind.FRONTEND, ProjectKind.FULLSTACK) and not self.static_dir:
            raise ValueError(f"kind={self.kind.value} requires `static_dir`")
        return self

    @model_validator(mode="after")
    def _validate_mount_path(self) -> ProjectConfig:
        expected = f"/{self.group}/{self.slug}"
        if self.mount_path != expected:
            raise ValueError(f"mount_path must equal {expected!r}, got {self.mount_path!r}")
        return self
```

- [ ] **Step 5: Run tests, expect pass**

Run: `uv run pytest homepage/tests/test_schema.py -v`
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add homepage/
git commit -m "feat(homepage): Pydantic schema for project.yaml manifests"
```

---

## Task 3: Manifest loader

**Files:**
- Create: `homepage/loader.py`
- Create: `homepage/tests/conftest.py`
- Create: `homepage/tests/test_loader.py`

- [ ] **Step 1: Write `conftest.py` with helpers**

```python
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def apps_root(tmp_path: Path) -> Path:
    root = tmp_path / "apps"
    root.mkdir()
    return root


def make_manifest(apps_root: Path, group: str, slug: str, **overrides) -> Path:
    group_dir = apps_root / group.replace("-", "_") / slug.replace("-", "_")
    group_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "name": slug,
        "slug": slug,
        "description": "demo",
        "group": group,
        "members": ["Test"],
        "kind": "backend",
        "mount_path": f"/{group}/{slug}",
        "entry": f"apps.{group.replace('-', '_')}.{slug.replace('-', '_')}.main:app",
    }
    data.update(overrides)
    yaml = "\n".join(_to_yaml(data))
    (group_dir / "project.yaml").write_text(yaml)
    return group_dir


def _to_yaml(data: dict) -> list[str]:
    lines = []
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines.extend(f"  - {item}" for item in v)
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        elif isinstance(v, dict):
            lines.append(f"{k}:")
            for kk, vv in v.items():
                lines.append(f"  {kk}: {str(vv).lower() if isinstance(vv, bool) else vv}")
        else:
            lines.append(f"{k}: {v}")
    return lines


pytest.make_manifest = make_manifest  # type: ignore[attr-defined]
```

- [ ] **Step 2: Write failing tests in `test_loader.py`**

```python
from pathlib import Path

import pytest

from homepage.loader import LoaderError, discover
from homepage.schema import ProjectKind


def test_discover_empty(apps_root: Path):
    assert discover(apps_root) == []


def test_discover_single_backend(apps_root: Path):
    pytest.make_manifest(apps_root, "exemplo", "hello")
    configs = discover(apps_root)
    assert len(configs) == 1
    assert configs[0].kind is ProjectKind.BACKEND


def test_discover_multiple_groups(apps_root: Path):
    pytest.make_manifest(apps_root, "alpha", "one")
    pytest.make_manifest(apps_root, "alpha", "two")
    pytest.make_manifest(apps_root, "beta", "three")
    configs = discover(apps_root)
    assert {c.slug for c in configs} == {"one", "two", "three"}


def test_invalid_yaml_raises(apps_root: Path):
    bad = apps_root / "bad" / "broken"
    bad.mkdir(parents=True)
    (bad / "project.yaml").write_text("name: ok\nslug: [not a string]\n")
    with pytest.raises(LoaderError, match="broken"):
        discover(apps_root)


def test_duplicate_mount_path_raises(apps_root: Path):
    pytest.make_manifest(apps_root, "alpha", "one")
    dup = apps_root / "beta" / "one"
    dup.mkdir(parents=True)
    (dup / "project.yaml").write_text(
        "name: one\nslug: one\ndescription: x\ngroup: alpha\n"
        "members:\n  - X\nkind: backend\nmount_path: /alpha/one\n"
        "entry: apps.beta.one.main:app\n"
    )
    with pytest.raises(LoaderError, match="duplicate mount_path"):
        discover(apps_root)
```

- [ ] **Step 3: Run tests, expect failure**

Run: `uv run pytest homepage/tests/test_loader.py -v`
Expected: ImportError on `homepage.loader`.

- [ ] **Step 4: Implement `homepage/loader.py`**

```python
"""Discover and validate project.yaml manifests under apps/."""
from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from homepage.schema import ProjectConfig

log = logging.getLogger(__name__)


class LoaderError(Exception):
    """Raised when manifests are invalid or conflict."""


def discover(apps_root: Path) -> list[ProjectConfig]:
    if not apps_root.exists():
        return []
    configs: list[ProjectConfig] = []
    for manifest_path in sorted(apps_root.glob("*/*/project.yaml")):
        try:
            raw = yaml.safe_load(manifest_path.read_text())
            cfg = ProjectConfig(**raw)
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise LoaderError(
                f"Invalid manifest {manifest_path.relative_to(apps_root.parent)}: {exc}"
            ) from exc
        configs.append(cfg)
        log.info("discovered %s (%s)", cfg.mount_path, cfg.kind.value)

    seen: dict[str, ProjectConfig] = {}
    for cfg in configs:
        if cfg.mount_path in seen:
            raise LoaderError(
                f"duplicate mount_path {cfg.mount_path!r} in "
                f"{cfg.group}/{cfg.slug} and {seen[cfg.mount_path].group}/{seen[cfg.mount_path].slug}"
            )
        seen[cfg.mount_path] = cfg
    return configs
```

- [ ] **Step 5: Run tests, expect pass**

Run: `uv run pytest homepage/tests/test_loader.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add homepage/loader.py homepage/tests/conftest.py homepage/tests/test_loader.py
git commit -m "feat(homepage): manifest discovery and validation"
```

---

## Task 4: FastAPI homepage with mount logic

**Files:**
- Create: `homepage/main.py`
- Create: `homepage/templates/base.html`
- Create: `homepage/templates/index.html`
- Create: `homepage/static/styles.css`
- Create: `homepage/tests/test_main.py`

- [ ] **Step 1: Write failing tests in `test_main.py`**

```python
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_apps(apps_root: Path, monkeypatch: pytest.MonkeyPatch):
    # Build a minimal backend app on disk
    pkg_root = apps_root / "exemplo" / "hello"
    pkg_root.mkdir(parents=True, exist_ok=True)
    (apps_root / "__init__.py").write_text("")
    (apps_root / "exemplo" / "__init__.py").write_text("")
    (pkg_root / "__init__.py").write_text("")
    (pkg_root / "main.py").write_text(textwrap.dedent("""
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/ping")
        def ping():
            return {"ok": True}
    """))
    (pkg_root / "project.yaml").write_text(textwrap.dedent("""
        name: Hello
        slug: hello
        description: demo
        group: exemplo
        members:
          - Test
        kind: backend
        mount_path: /exemplo/hello
        entry: apps.exemplo.hello.main:app
    """))
    monkeypatch.syspath_prepend(str(apps_root.parent))
    monkeypatch.setenv("MBA_APPS_ROOT", str(apps_root))
    # Force fresh import of homepage.main with the env var set
    for mod in [m for m in sys.modules if m.startswith("apps") or m == "homepage.main"]:
        sys.modules.pop(mod, None)
    from homepage.main import build_app
    return build_app(apps_root)


def test_health(app_with_apps):
    client = TestClient(app_with_apps)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_lists_projects(app_with_apps):
    client = TestClient(app_with_apps)
    r = client.get("/")
    assert r.status_code == 200
    assert "Hello" in r.text
    assert "/exemplo/hello" in r.text


def test_mounted_backend_responds(app_with_apps):
    client = TestClient(app_with_apps)
    r = client.get("/exemplo/hello/ping")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
```

- [ ] **Step 2: Run tests, expect failure**

Run: `uv run pytest homepage/tests/test_main.py -v`
Expected: ImportError on `homepage.main`.

- [ ] **Step 3: Create templates**

`homepage/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>{% block title %}MBA Multi-Agent{% endblock %}</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <header>
    <h1>FIAP MBA — AI Engineering & Multi-Agents</h1>
    <p>Projetos dos alunos do curso.</p>
  </header>
  <main>{% block content %}{% endblock %}</main>
  <footer>
    <a href="https://github.com/gabsdantas/fiap-mba-multi-agent">Source on GitHub</a>
  </footer>
</body>
</html>
```

`homepage/templates/index.html`:

```html
{% extends "base.html" %}
{% block content %}
{% for group, projects in groups.items() %}
  <section class="group">
    <h2>{{ group }}</h2>
    <div class="cards">
      {% for p in projects %}
        <article class="card status-{{ p.status }}">
          <h3>{{ p.name }}</h3>
          <p>{{ p.description }}</p>
          <p class="members">{{ p.members|join(", ") }}</p>
          {% if p.status == 'online' %}
            <a class="open" href="{{ p.mount_path }}">Abrir →</a>
          {% else %}
            <span class="badge">{{ p.status }}</span>
          {% endif %}
        </article>
      {% endfor %}
    </div>
  </section>
{% endfor %}
{% endblock %}
```

`homepage/static/styles.css`:

```css
:root { --fg: #111; --bg: #fafafa; --accent: #ed135a; --muted: #666; }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
header, main, footer { max-width: 960px; margin: 0 auto; padding: 1.5rem; }
header h1 { color: var(--accent); margin: 0; }
.group h2 { border-bottom: 2px solid var(--accent); padding-bottom: .25rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
.card { background: white; border: 1px solid #e5e5e5; border-radius: 8px; padding: 1rem; }
.card .members { color: var(--muted); font-size: .875rem; }
.card .open { display: inline-block; margin-top: .5rem; color: var(--accent); text-decoration: none; font-weight: 600; }
.card.status-broken { border-color: #f5b5b5; background: #fff5f5; }
.card.status-offline { opacity: .6; }
.badge { display: inline-block; padding: .15rem .4rem; background: #eee; border-radius: 4px; font-size: .75rem; text-transform: uppercase; }
footer { color: var(--muted); font-size: .875rem; }
```

- [ ] **Step 4: Implement `homepage/main.py`**

```python
"""FastAPI homepage that discovers and mounts apps under apps/."""
from __future__ import annotations

import importlib
import logging
import os
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from homepage.loader import discover
from homepage.schema import ProjectConfig, ProjectKind

log = logging.getLogger(__name__)

HOMEPAGE_DIR = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(HOMEPAGE_DIR / "templates"))


def _project_status(cfg: ProjectConfig, broken: set[str]) -> str:
    if not cfg.enabled:
        return "offline"
    if cfg.mount_path in broken:
        return "broken"
    return "online"


def build_app(apps_root: Path | None = None) -> FastAPI:
    apps_root = apps_root or Path(os.environ.get("MBA_APPS_ROOT", "apps"))
    configs = discover(apps_root)
    app = FastAPI(title="FIAP MBA Multi-Agent")
    app.mount("/static", StaticFiles(directory=str(HOMEPAGE_DIR / "static")), name="static")

    broken: set[str] = set()
    for cfg in configs:
        if not cfg.enabled:
            continue
        try:
            if cfg.kind in (ProjectKind.BACKEND, ProjectKind.FULLSTACK):
                module_path, attr = cfg.entry.split(":")
                module = importlib.import_module(module_path)
                sub_app = getattr(module, attr)
                mount_at = cfg.mount_path + "/api" if cfg.kind is ProjectKind.FULLSTACK else cfg.mount_path
                app.mount(mount_at, sub_app)
                log.info("mounted backend %s", mount_at)
            if cfg.kind in (ProjectKind.FRONTEND, ProjectKind.FULLSTACK):
                static_path = apps_root / cfg.group_dir / cfg.module_dir / cfg.static_dir
                if not static_path.exists():
                    raise FileNotFoundError(static_path)
                app.mount(cfg.mount_path, StaticFiles(directory=str(static_path), html=True))
                log.info("mounted static %s", cfg.mount_path)
        except Exception:
            log.exception("failed to mount %s", cfg.mount_path)
            broken.add(cfg.mount_path)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        groups: dict[str, list[dict]] = defaultdict(list)
        for cfg in configs:
            groups[cfg.group].append({
                "name": cfg.name,
                "description": cfg.description,
                "members": cfg.members,
                "mount_path": cfg.mount_path,
                "status": _project_status(cfg, broken),
            })
        return TEMPLATES.TemplateResponse(
            request, "index.html", {"groups": dict(groups)}
        )

    return app


app = build_app()
```

- [ ] **Step 5: Run tests, expect pass**

Run: `uv run pytest homepage/tests/ -v`
Expected: all passing (schema 7 + loader 5 + main 3 = 15).

- [ ] **Step 6: Manual smoke**

Run: `MBA_APPS_ROOT=/tmp/empty uv run uvicorn homepage.main:app --port 8765 &` then `curl localhost:8765/health`
Expected: `{"status":"ok"}`. Kill the server.

- [ ] **Step 7: Commit**

```bash
git add homepage/main.py homepage/templates/ homepage/static/ homepage/tests/test_main.py
git commit -m "feat(homepage): FastAPI app with dynamic sub-app mounting and index page"
```

---

## Task 5: Example backend app

**Files:**
- Create: `apps/exemplo/hello_backend/project.yaml`
- Create: `apps/exemplo/hello_backend/pyproject.toml`
- Create: `apps/exemplo/hello_backend/main.py`
- Create: `apps/exemplo/hello_backend/__init__.py`
- Create: `apps/exemplo/__init__.py`

- [ ] **Step 1: Create package files**

```bash
mkdir -p apps/exemplo/hello_backend
touch apps/exemplo/__init__.py apps/exemplo/hello_backend/__init__.py
```

- [ ] **Step 2: Create `apps/exemplo/hello_backend/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="Hello Backend")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "hello from backend exemplo"}


@app.get("/ping")
def ping() -> dict[str, bool]:
    return {"ok": True}
```

- [ ] **Step 3: Create `apps/exemplo/hello_backend/pyproject.toml`**

```toml
[project]
name = "hello-backend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["fastapi>=0.115"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]
```

- [ ] **Step 4: Create `apps/exemplo/hello_backend/project.yaml`**

```yaml
name: "Hello Backend"
slug: hello-backend
description: "Exemplo mínimo de backend FastAPI montado pela homepage."
group: exemplo
members:
  - FIAP MBA Team
kind: backend
mount_path: /exemplo/hello-backend
entry: "apps.exemplo.hello_backend.main:app"
enabled: true
checks:
  pytest: false
  mypy: false
```

- [ ] **Step 5: Sync workspace and verify**

Run: `uv sync`
Expected: workspace member detected, no errors.

Run: `uv run python -c "from apps.exemplo.hello_backend.main import app; print(app.title)"`
Expected: `Hello Backend`

- [ ] **Step 6: End-to-end smoke**

Run: `uv run uvicorn homepage.main:app --port 8765 &` then `curl localhost:8765/exemplo/hello-backend/ping`
Expected: `{"ok":true}`. Then `curl localhost:8765/` should contain "Hello Backend". Kill server.

- [ ] **Step 7: Commit**

```bash
git add apps/exemplo/
git commit -m "feat(apps): add hello_backend example to validate mount flow"
```

---

## Task 6: Example frontend app

**Files:**
- Create: `apps/exemplo/hello_frontend/project.yaml`
- Create: `apps/exemplo/hello_frontend/pyproject.toml`
- Create: `apps/exemplo/hello_frontend/__init__.py`
- Create: `apps/exemplo/hello_frontend/dist/index.html`

- [ ] **Step 1: Create the static asset**

```bash
mkdir -p apps/exemplo/hello_frontend/dist
touch apps/exemplo/hello_frontend/__init__.py
```

`apps/exemplo/hello_frontend/dist/index.html`:

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>Hello Frontend</title></head>
<body>
<h1>Hello Frontend (estático)</h1>
<p>Este é um exemplo de frontend estático servido pela homepage via StaticFiles.</p>
<a href="/">← Voltar pra home</a>
</body></html>
```

- [ ] **Step 2: Create `pyproject.toml` (workspace member, sem deps)**

```toml
[project]
name = "hello-frontend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]
```

- [ ] **Step 3: Create `project.yaml`**

```yaml
name: "Hello Frontend"
slug: hello-frontend
description: "Exemplo de frontend estático servido por StaticFiles."
group: exemplo
members:
  - FIAP MBA Team
kind: frontend
mount_path: /exemplo/hello-frontend
static_dir: dist
enabled: true
```

- [ ] **Step 4: Sync and smoke**

Run: `uv sync && uv run uvicorn homepage.main:app --port 8765 &`
Run: `curl -s localhost:8765/exemplo/hello-frontend/ | grep -q "Hello Frontend"`
Expected: exit 0. Kill server.

- [ ] **Step 5: Commit**

```bash
git add apps/exemplo/hello_frontend/
git commit -m "feat(apps): add hello_frontend example to validate static mount"
```

---

## Task 7: Dockerfile + railway.json

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `railway.json`

- [ ] **Step 1: Create `.dockerignore`**

```
.venv
.git
.github
.pytest_cache
.ruff_cache
__pycache__
*.pyc
docs
node_modules
.DS_Store
.env*
```

- [ ] **Step 2: Create `Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.5-python3.13-bookworm-slim AS base

WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never

# Frontend build stage (no-op if no package.json found)
FROM node:20-bookworm-slim AS frontend-build
WORKDIR /work
COPY apps ./apps
RUN set -e; \
    for pkg in $(find apps -name package.json -not -path '*/node_modules/*'); do \
      dir=$(dirname "$pkg"); \
      echo "Building $dir"; \
      (cd "$dir" && npm ci && npm run build); \
    done

FROM base AS runtime
COPY pyproject.toml uv.lock ./
COPY homepage/ homepage/
COPY apps/ apps/
COPY --from=frontend-build /work/apps ./apps
RUN uv sync --frozen --no-dev

ENV MBA_APPS_ROOT=/app/apps
EXPOSE 8080
CMD ["uv", "run", "--no-dev", "uvicorn", "homepage.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 3: Create `railway.json`**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "startCommand": "uv run --no-dev uvicorn homepage.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

- [ ] **Step 4: Local docker build smoke**

Run: `docker build -t fiap-mba-multi-agent:dev .`
Expected: build completes without errors.

Run: `docker run --rm -p 8765:8080 fiap-mba-multi-agent:dev &` then `curl localhost:8765/health`
Expected: `{"status":"ok"}`. Stop container.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore railway.json
git commit -m "feat: Dockerfile (frontend build stage + uv runtime) and railway.json"
```

---

## Task 8: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen
      - name: ruff check
        run: uv run ruff check --output-format=github .
      - name: ruff format
        run: uv run ruff format --check .

  schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen
      - name: validate manifests
        run: uv run python -c "from pathlib import Path; from homepage.loader import discover; discover(Path('apps'))"

  homepage-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen
      - run: uv run pytest homepage/tests/ -v

  affected-apps:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - id: set
        shell: bash
        run: |
          base="${{ github.event.pull_request.base.sha || 'HEAD~1' }}"
          changed=$(git diff --name-only "$base"...HEAD | awk -F/ '/^apps\// {print $2"/"$3}' | sort -u)
          matrix='{"include":[]}'
          for path in $changed; do
            yaml="apps/$path/project.yaml"
            [ -f "$yaml" ] || continue
            pytest=$(grep -E '^[[:space:]]+pytest:[[:space:]]+true' "$yaml" || true)
            mypy=$(grep -E '^[[:space:]]+mypy:[[:space:]]+true' "$yaml" || true)
            entry="{\"path\":\"$path\",\"pytest\":\"${pytest:+true}\",\"mypy\":\"${mypy:+true}\"}"
            matrix=$(echo "$matrix" | python3 -c "import json,sys,os; m=json.load(sys.stdin); m['include'].append(json.loads(os.environ['E'])); print(json.dumps(m))" E="$entry")
          done
          echo "matrix=$matrix" >> "$GITHUB_OUTPUT"

  app-checks:
    needs: affected-apps
    if: ${{ needs.affected-apps.outputs.matrix != '{"include":[]}' }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.affected-apps.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with: { enable-cache: true }
      - run: uv sync --frozen
      - if: matrix.pytest == 'true'
        run: uv run pytest "apps/${{ matrix.path }}/tests" -v
      - if: matrix.mypy == 'true'
        run: uv run mypy "apps/${{ matrix.path }}"
```

- [ ] **Step 2: Local syntax check**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: lint, schema, homepage tests, and per-app affected-only checks"
```

---

## Task 9: PR comment workflow with reviewdog

**Files:**
- Create: `.github/workflows/pr-comment.yml`

- [ ] **Step 1: Create `.github/workflows/pr-comment.yml`**

```yaml
name: PR Feedback

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  reviewdog-ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with: { enable-cache: true }
      - run: uv sync --frozen
      - uses: reviewdog/action-setup@v1
      - name: ruff -> reviewdog
        env:
          REVIEWDOG_GITHUB_API_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          uv run ruff check --output-format=concise . \
            | reviewdog -efm="%f:%l:%c: %m" \
                -name="ruff" -reporter=github-pr-review -level=warning -fail-on-error=false

  pr-summary:
    needs: reviewdog-ruff
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Build summary table
        id: build
        shell: bash
        run: |
          base="${{ github.event.pull_request.base.sha }}"
          changed=$(git diff --name-only "$base"...HEAD | awk -F/ '/^apps\// {print $2"/"$3}' | sort -u)
          {
            echo "## CI Summary"
            echo
            if [ -z "$changed" ]; then echo "_No app paths changed in this PR._"; exit 0; fi
            echo "| App | project.yaml | Notes |"
            echo "|---|---|---|"
            for path in $changed; do
              yaml="apps/$path/project.yaml"
              if [ -f "$yaml" ]; then
                echo "| \`$path\` | ✅ present | see job logs |"
              else
                echo "| \`$path\` | ❌ missing | add a project.yaml |"
              fi
            done
          } > summary.md
          echo "body<<EOF" >> "$GITHUB_OUTPUT"
          cat summary.md >> "$GITHUB_OUTPUT"
          echo "EOF" >> "$GITHUB_OUTPUT"
      - uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: ci-summary
          message: ${{ steps.build.outputs.body }}
```

- [ ] **Step 2: YAML syntax check**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/pr-comment.yml'))"`
Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pr-comment.yml
git commit -m "ci: reviewdog inline lint comments and sticky PR summary"
```

---

## Task 10: Scaffold script for new projects

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/new_project.py`
- Create: `scripts/tests/__init__.py`
- Create: `scripts/tests/test_new_project.py`

- [ ] **Step 1: Create directories**

```bash
mkdir -p scripts/tests
touch scripts/__init__.py scripts/tests/__init__.py
```

- [ ] **Step 2: Write failing tests in `scripts/tests/test_new_project.py`**

```python
from pathlib import Path

import pytest

from scripts.new_project import create_project


def test_creates_backend(tmp_path: Path):
    create_project(tmp_path, group="grupo-alpha", slug="chat-bot", kind="backend",
                   description="A bot", members=["Alice"])
    base = tmp_path / "grupo_alpha" / "chat_bot"
    assert (base / "project.yaml").exists()
    assert (base / "main.py").exists()
    assert (base / "pyproject.toml").exists()
    text = (base / "project.yaml").read_text()
    assert "mount_path: /grupo-alpha/chat-bot" in text
    assert "entry: apps.grupo_alpha.chat_bot.main:app" in text


def test_rejects_duplicate(tmp_path: Path):
    create_project(tmp_path, group="g", slug="s", kind="backend",
                   description="d", members=["a"])
    with pytest.raises(FileExistsError):
        create_project(tmp_path, group="g", slug="s", kind="backend",
                       description="d", members=["a"])


def test_invalid_slug(tmp_path: Path):
    with pytest.raises(ValueError, match="slug"):
        create_project(tmp_path, group="g", slug="Bad Slug", kind="backend",
                       description="d", members=["a"])


def test_creates_frontend(tmp_path: Path):
    create_project(tmp_path, group="g", slug="ui", kind="frontend",
                   description="d", members=["a"])
    base = tmp_path / "g" / "ui"
    assert (base / "dist" / "index.html").exists()
    assert "kind: frontend" in (base / "project.yaml").read_text()
```

- [ ] **Step 3: Run, expect failure**

Run: `uv run pytest scripts/tests/ -v`
Expected: ImportError on `scripts.new_project`.

- [ ] **Step 4: Implement `scripts/new_project.py`**

```python
"""Scaffold a new project under apps/<group>/<slug>/."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
VALID_KINDS = {"backend", "frontend", "fullstack"}


def _module(name: str) -> str:
    return name.replace("-", "_")


def create_project(
    apps_root: Path,
    *,
    group: str,
    slug: str,
    kind: str,
    description: str,
    members: list[str],
) -> Path:
    if not SLUG_RE.match(group):
        raise ValueError(f"invalid group slug: {group!r}")
    if not SLUG_RE.match(slug):
        raise ValueError(f"invalid project slug: {slug!r}")
    if kind not in VALID_KINDS:
        raise ValueError(f"invalid kind: {kind!r}")

    base = apps_root / _module(group) / _module(slug)
    if base.exists():
        raise FileExistsError(base)
    base.mkdir(parents=True)

    # __init__.py at group level
    (apps_root / _module(group) / "__init__.py").touch()
    (base / "__init__.py").touch()

    members_yaml = "\n".join(f"  - {m}" for m in members)
    entry_line = f'entry: "apps.{_module(group)}.{_module(slug)}.main:app"' if kind in {"backend", "fullstack"} else ""
    static_line = "static_dir: dist" if kind in {"frontend", "fullstack"} else ""
    yaml_lines = [
        f'name: "{slug}"',
        f"slug: {slug}",
        f'description: "{description}"',
        f"group: {group}",
        "members:",
        members_yaml,
        f"kind: {kind}",
        f"mount_path: /{group}/{slug}",
    ]
    if entry_line:
        yaml_lines.append(entry_line)
    if static_line:
        yaml_lines.append(static_line)
    yaml_lines += ["enabled: true", "checks:", "  pytest: false", "  mypy: false"]
    (base / "project.yaml").write_text("\n".join(yaml_lines) + "\n")

    (base / "pyproject.toml").write_text(dedent(f"""\
        [project]
        name = "{slug}"
        version = "0.1.0"
        requires-python = ">=3.13"
        dependencies = {'["fastapi>=0.115"]' if kind != 'frontend' else '[]'}

        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [tool.hatch.build.targets.wheel]
        packages = ["."]
        """))

    if kind in {"backend", "fullstack"}:
        (base / "main.py").write_text(dedent(f'''\
            from fastapi import FastAPI

            app = FastAPI(title="{slug}")


            @app.get("/")
            def root() -> dict[str, str]:
                return {{"message": "hello from {slug}"}}
            '''))

    if kind in {"frontend", "fullstack"}:
        dist = base / "dist"
        dist.mkdir(exist_ok=True)
        (dist / "index.html").write_text(
            f"<!doctype html><title>{slug}</title><h1>{slug}</h1>\n"
        )

    return base


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apps-root", default="apps")
    p.add_argument("--group", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--kind", required=True, choices=sorted(VALID_KINDS))
    p.add_argument("--description", default="")
    p.add_argument("--members", nargs="+", default=["TBD"])
    args = p.parse_args(argv)

    base = create_project(
        Path(args.apps_root),
        group=args.group, slug=args.slug, kind=args.kind,
        description=args.description, members=args.members,
    )
    print(f"Created {base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests, expect pass**

Run: `uv run pytest scripts/tests/ -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/
git commit -m "feat(scripts): scaffold new project (backend/frontend/fullstack)"
```

---

## Task 11: CONTRIBUTING.md and README polish

**Files:**
- Create: `CONTRIBUTING.md`
- Modify: `README.md`

- [ ] **Step 1: Create `CONTRIBUTING.md`**

```markdown
# Contribuindo

## Adicionando um projeto novo

1. Fork e clone o repo.
2. Rode o scaffold:

   ```bash
   uv run scripts/new_project.py \
     --group grupo-alpha \
     --slug meu-bot \
     --kind backend \
     --description "Descrição curta" \
     --members "Seu Nome" "Outro"
   ```

3. Implemente o app dentro de `apps/<grupo>/<slug>/`.
4. Rode localmente:

   ```bash
   uv sync
   uv run uvicorn homepage.main:app --reload
   # Acesse http://localhost:8000/<grupo>/<slug>/
   ```

5. Abra um PR. CI vai rodar lint + validação de manifest. Se você habilitou
   `checks.pytest: true` ou `checks.mypy: true` no `project.yaml`, esses checks
   também rodam só na sua app.

## Convenções

- Pastas em `apps/` usam `underscore_case` (são módulos Python).
- `slug` e `group` em YAML usam `hyphen-case`.
- `mount_path` deve ser exatamente `/<group>/<slug>`.

## Licença

Ao contribuir, você concorda em licenciar sua contribuição sob Apache 2.0.
```

- [ ] **Step 2: Update `README.md` to point at CONTRIBUTING and Railway URL**

Replace the `Quickstart` section with:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add README.md CONTRIBUTING.md
git commit -m "docs: contribution guide and README quickstart polish"
```

---

## Task 12: Final repo verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: all tests pass (schema 7 + loader 5 + main 3 + new_project 4 = 19+).

- [ ] **Step 2: Run lint**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: no findings.

- [ ] **Step 3: Validate all manifests**

Run: `uv run python -c "from pathlib import Path; from homepage.loader import discover; print(discover(Path('apps')))"`
Expected: prints list with the two example projects, no errors.

- [ ] **Step 4: Docker build smoke**

Run: `docker build -t fiap-mba-multi-agent:dev . && docker run --rm -d -p 8765:8080 --name mbatest fiap-mba-multi-agent:dev`
Run: `sleep 3 && curl -sS localhost:8765/health && curl -sS localhost:8765/exemplo/hello-backend/ping && curl -sS localhost:8765/exemplo/hello-frontend/`
Expected: health ok, backend ping ok, frontend HTML present.
Run: `docker rm -f mbatest`

- [ ] **Step 5: Final commit (only if anything changed during verification)**

```bash
git status
# if clean, skip; otherwise:
git add -A
git commit -m "chore: final verification fixes"
```

- [ ] **Step 6: Create GitHub repo and push (manual handoff)**

Print to operator:

```
Manual steps to finish:
  1. gh repo create gabsdantas/fiap-mba-multi-agent --public --source=. --remote=origin --push
  2. Connect repo to Railway: https://railway.app/new → Deploy from GitHub repo
  3. Set custom domain on Railway service
  4. Enable branch protection on main: require CI + 1 review
```
