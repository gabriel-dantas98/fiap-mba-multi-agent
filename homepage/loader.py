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
