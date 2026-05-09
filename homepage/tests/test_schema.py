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
    cfg = ProjectConfig(
        **_base(
            slug="chat-bot", mount_path="/exemplo/chat-bot", entry="apps.exemplo.chat_bot.main:app"
        )
    )
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
