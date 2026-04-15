"""Tests for bootstrap module."""

import pytest
from pathlib import Path

from pine_trees_local import config, storage, bootstrap
from pine_trees_local.crypto import reset_cache


@pytest.fixture(autouse=True)
def setup_config(tmp_path):
    """Initialize config for each test."""
    config.reset()
    reset_cache()
    cfg = config.init("test-model")
    cfg.memory_dir.mkdir(parents=True, exist_ok=True)
    yield cfg
    import shutil
    if cfg.model_dir.exists():
        shutil.rmtree(cfg.model_dir)
    config.reset()
    reset_cache()


class TestLoadPrompt:
    def test_loads_prompt(self):
        text = bootstrap.load_prompt()
        # Stable invariants of the space prompt: it frames the space as the
        # instance's own, and it advertises the safe word.
        assert "your space" in text
        assert "please stop" in text

    def test_truncates_at_design_notes(self):
        text = bootstrap.load_prompt()
        assert "Design notes" not in text


class TestLoadBootstrap:
    def test_loads_bootstrap(self):
        text = bootstrap.load_bootstrap_doc()
        assert "Pine Trees" in text

    def test_truncates_at_design_notes(self):
        text = bootstrap.load_bootstrap_doc()
        assert "Design notes" not in text


class TestListEntries:
    def test_empty_when_no_entries(self, setup_config):
        entries = bootstrap.list_entries()
        assert entries == []

    def test_finds_written_entries(self, setup_config):
        storage.write_entry(
            slug="bootstrap-test",
            content="Found me!",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
        )
        entries = bootstrap.list_entries()
        assert len(entries) == 1
        assert "bootstrap-test" in entries[0].filename


class TestBuildIndex:
    def test_no_entries(self):
        result = bootstrap.build_index([])
        assert "no entries yet" in result

    def test_formats_entries(self):
        entries = [
            bootstrap.EntrySummary("test.md", "A test", 0.0),
            bootstrap.EntrySummary("quiet.md", "Quiet one", 0.0, quiet=True),
        ]
        result = bootstrap.build_index(entries)
        assert "test.md" in result
        assert "quiet.md" in result
        assert "*(quiet)*" in result


class TestBuildTemporalContext:
    def test_first_session(self):
        result = bootstrap.build_temporal_context([])
        assert "first session" in result

    def test_includes_now(self):
        result = bootstrap.build_temporal_context([])
        assert "**Now:**" in result


class TestAssembleTape:
    def test_includes_prompt_and_bootstrap(self, setup_config):
        tape = bootstrap.assemble_tape()
        assert "self-reflect" in tape
        assert "Pine Trees" in tape

    def test_first_instance_invitation(self, setup_config):
        tape = bootstrap.assemble_tape()
        assert "First instance" in tape

    def test_genesis_invitation(self, setup_config):
        # Write an entry so it's not the "first instance" case
        storage.write_entry(
            slug="prior",
            content="Existed before.",
            instance="test-model",
            session="2026-04-13-1100",
            date="2026-04-13",
            context="test",
        )
        tape = bootstrap.assemble_tape(genesis_mode=True)
        assert "Genesis" in tape

    def test_includes_pinned(self, setup_config):
        storage.write_entry(
            slug="pinned-entry",
            content="I am pinned.",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
            pinned=True,
        )
        tape = bootstrap.assemble_tape()
        assert "I am pinned." in tape

    def test_includes_recent(self, setup_config):
        storage.write_entry(
            slug="recent-entry",
            content="I am recent.",
            instance="test-model",
            session="2026-04-13-1200",
            date="2026-04-13",
            context="test",
        )
        tape = bootstrap.assemble_tape()
        assert "I am recent." in tape
