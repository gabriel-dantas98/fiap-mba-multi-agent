"""Slug rules shared by manifests (schema) and scaffolding (new_project)."""

from __future__ import annotations

import re

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SLUG_PATTERN = SLUG_RE.pattern


def slug_to_package_dir(name: str) -> str:
    """Map manifest slug/group to the Python package directory name."""
    return name.replace("-", "_")


def assert_valid_slug(label: str, value: str) -> None:
    if not SLUG_RE.match(value):
        raise ValueError(f"invalid {label} slug: {value!r}")
