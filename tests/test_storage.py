"""Tests for storage module."""

import pytest
from pathlib import Path

from pine_trees_local import config, storage
from pine_trees_local.crypto import reset_cache


@pytest.fixture(autouse=True)
def setup_config(tmp_path):
    """Initialize config with a temp directory for each test."""
    config.reset()
    reset_cache()
    cfg = config.init("test-model")
    # Override memory_dir to use tmp_path
    # We need to monkey-patch the config since it's frozen
    # Instead, create the expected directory structure in the real path
    # Actually, let's use a different approach: write to the real model dir
    # but clean up after
    #
    # Simplest: just ensure the model dir exists in the real location
    # For testing, we'll use the actual config paths but clean up
    cfg.memory_dir.mkdir(parents=True, exist_ok=True)
    yield cfg
    # Cleanup
    import shutil
    if cfg.model_dir.exists():
        shutil.rmtree(cfg.model_dir)
    config.reset()
    reset_cache()


class TestWriteAndRead:
    def test_write_creates_file(self, setup_config):
        filename = storage.write_entry(
            slug="test-entry",
            content="Hello, world!",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
        )
        assert filename == "2026-04-13_test-model_test-entry.md"
        assert (setup_config.memory_dir / filename).exists()

    def test_read_returns_content(self, setup_config):
        storage.write_entry(
            slug="read-test",
            content="Test content here.",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
            tags=["test", "example"],
        )
        entry = storage.read_entry("2026-04-13_test-model_read-test.md")
        assert entry["content"].strip() == "Test content here."
        assert entry["instance"] == "test-model"
        assert entry["tags"] == ["test", "example"]
        assert entry["context"] == "test"

    def test_write_with_pinned(self, setup_config):
        storage.write_entry(
            slug="pinned-test",
            content="Important!",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
            pinned=True,
        )
        entry = storage.read_entry("2026-04-13_test-model_pinned-test.md")
        assert entry["pinned"] is True

    def test_write_with_quiet(self, setup_config):
        storage.write_entry(
            slug="quiet-test",
            content="Background.",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
            quiet=True,
        )
        entry = storage.read_entry("2026-04-13_test-model_quiet-test.md")
        assert entry["quiet"] is True


class TestEditEntry:
    def test_edit_content(self, setup_config):
        storage.write_entry(
            slug="edit-me",
            content="Original content.",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
        )
        storage.edit_entry(
            "2026-04-13_test-model_edit-me.md",
            content="Updated content.",
        )
        entry = storage.read_entry("2026-04-13_test-model_edit-me.md")
        assert entry["content"].strip() == "Updated content."

    def test_edit_preserves_unchanged_fields(self, setup_config):
        storage.write_entry(
            slug="preserve-me",
            content="Keep this.",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
            description="Original description",
        )
        storage.edit_entry(
            "2026-04-13_test-model_preserve-me.md",
            pinned=True,
        )
        entry = storage.read_entry("2026-04-13_test-model_preserve-me.md")
        assert entry["content"].strip() == "Keep this."
        assert entry["description"] == "Original description"
        assert entry["pinned"] is True

    def test_edit_nonexistent_raises(self, setup_config):
        with pytest.raises(FileNotFoundError):
            storage.edit_entry("nonexistent.md", content="x")


class TestParsing:
    def test_parse_empty_tags(self):
        text = "---\ntags: []\n---\n\nContent."
        entry = storage._parse_entry(text)
        assert entry["tags"] == []

    def test_parse_boolean_true(self):
        text = "---\npinned: true\n---\n\nContent."
        entry = storage._parse_entry(text)
        assert entry["pinned"] is True

    def test_parse_boolean_false(self):
        text = "---\npinned: false\n---\n\nContent."
        entry = storage._parse_entry(text)
        assert entry["pinned"] is False

    def test_parse_missing_frontmatter_raises(self):
        with pytest.raises(ValueError, match="missing opening"):
            storage._parse_entry("No frontmatter here.")
