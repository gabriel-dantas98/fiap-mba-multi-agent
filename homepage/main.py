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
