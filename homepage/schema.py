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
