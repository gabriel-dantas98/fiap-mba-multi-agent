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
