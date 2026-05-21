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

    (apps_root / _module(group) / "__init__.py").touch()
    (base / "__init__.py").touch()

    members_yaml = "\n".join(f"  - {m}" for m in members)
    entry_line = (
        f"entry: apps.{_module(group)}.{_module(slug)}.main:app"
        if kind in {"backend", "fullstack"}
        else ""
    )
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

    (base / "pyproject.toml").write_text(
        dedent(f"""\
        [project]
        name = "{slug}"
        version = "0.1.0"
        requires-python = ">=3.13"
        dependencies = {'["fastapi>=0.115"]' if kind != "frontend" else "[]"}

        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [tool.hatch.build.targets.wheel]
        packages = ["."]
        """)
    )

    if kind in {"backend", "fullstack"}:
        (base / "main.py").write_text(
            dedent(f'''\
            from fastapi import FastAPI

            app = FastAPI(title="{slug}")


            @app.get("/")
            def root() -> dict[str, str]:
                return {{"message": "hello from {slug}"}}
            ''')
        )

    if kind in {"frontend", "fullstack"}:
        dist = base / "dist"
        dist.mkdir(exist_ok=True)
        (dist / "index.html").write_text(f"<!doctype html><title>{slug}</title><h1>{slug}</h1>\n")

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
        group=args.group,
        slug=args.slug,
        kind=args.kind,
        description=args.description,
        members=args.members,
    )
    print(f"Created {base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
