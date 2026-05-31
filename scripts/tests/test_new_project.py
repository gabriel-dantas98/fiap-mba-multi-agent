from pathlib import Path

import pytest

from scripts.new_project import create_project


def test_creates_backend(tmp_path: Path):
    create_project(
        tmp_path,
        group="grupo-alpha",
        slug="chat-bot",
        kind="backend",
        description="A bot",
        members=["Alice"],
    )
    base = tmp_path / "grupo_alpha" / "chat_bot"
    assert (base / "project.yaml").exists()
    assert (base / "main.py").exists()
    assert (base / "pyproject.toml").exists()
    text = (base / "project.yaml").read_text()
    assert "mount_path: /grupo-alpha/chat-bot" in text
    assert "entry: apps.grupo_alpha.chat_bot.main:app" in text


def test_rejects_duplicate(tmp_path: Path):
    create_project(tmp_path, group="g", slug="s", kind="backend", description="d", members=["a"])
    with pytest.raises(FileExistsError):
        create_project(
            tmp_path, group="g", slug="s", kind="backend", description="d", members=["a"]
        )


def test_invalid_slug(tmp_path: Path):
    with pytest.raises(ValueError, match="slug"):
        create_project(
            tmp_path, group="g", slug="Bad Slug", kind="backend", description="d", members=["a"]
        )


def test_creates_frontend(tmp_path: Path):
    create_project(tmp_path, group="g", slug="ui", kind="frontend", description="d", members=["a"])
    base = tmp_path / "g" / "ui"
    assert (base / "dist" / "index.html").exists()
    assert "kind: frontend" in (base / "project.yaml").read_text()
