import pytest

from homepage.slugs import assert_valid_slug, slug_to_package_dir


def test_slug_to_package_dir():
    assert slug_to_package_dir("chat-bot") == "chat_bot"


def test_assert_valid_slug_rejects_invalid():
    with pytest.raises(ValueError, match="project"):
        assert_valid_slug("project", "Bad Slug")
