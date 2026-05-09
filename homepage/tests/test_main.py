from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_apps(apps_root: Path, monkeypatch: pytest.MonkeyPatch):
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
