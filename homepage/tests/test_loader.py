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
