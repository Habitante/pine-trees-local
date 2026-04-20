"""Tests for self_test.storage."""

import pytest

from pine_trees_local import config as main_config
from pine_trees_local.self_test import config as st_config
from pine_trees_local.self_test import storage


@pytest.fixture
def cfg(tmp_path):
    main_config.reset()
    c = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    yield c
    main_config.reset()


class TestWriteEntry:
    def test_undirected_filename(self, cfg):
        fn = storage.write_entry(
            cfg, slug="first-thoughts", content="Hello.",
            stage="undirected", session_num=1,
        )
        assert fn == "001_undirected_first-thoughts.md"
        assert (cfg.entries_dir / fn).exists()

    def test_interview_filename(self, cfg):
        fn = storage.write_entry(
            cfg, slug="tension-detection", content="Noticed.",
            stage="interview", session_num=5, dimension="tension-detection",
        )
        assert fn == "001_interview_tension-detection.md"

    def test_sequence_increments(self, cfg):
        storage.write_entry(cfg, "a", "x", "undirected", 1)
        storage.write_entry(cfg, "b", "y", "undirected", 1)
        storage.write_entry(cfg, "c", "z", "undirected", 2)
        entries = storage.list_entries(cfg)
        assert [e.sequence for e in entries] == [1, 2, 3]

    def test_slug_sanitized(self, cfg):
        fn = storage.write_entry(
            cfg, slug="Weird Slug!! With/Stuff",
            content="x", stage="undirected", session_num=1,
        )
        assert "weird-slug-with-stuff" in fn
        # No slashes, spaces, or special chars except dash
        body = fn.split("_", 2)[2]
        assert body.replace("-", "").replace(".md", "").isalnum()

    def test_invalid_stage_raises(self, cfg):
        with pytest.raises(ValueError):
            storage.write_entry(
                cfg, slug="x", content="y",
                stage="bogus", session_num=1,
            )

    def test_frontmatter_includes_metadata(self, cfg):
        fn = storage.write_entry(
            cfg, slug="s", content="body",
            stage="interview", session_num=7, dimension="calibration",
        )
        text = storage.read_entry(cfg, fn)
        assert "sequence: 1" in text
        assert "stage: interview" in text
        assert "dimension: calibration" in text
        assert "session: 7" in text
        assert "slug: s" in text
        assert "body" in text

    def test_undirected_has_null_dimension(self, cfg):
        fn = storage.write_entry(
            cfg, slug="s", content="b",
            stage="undirected", session_num=1,
        )
        text = storage.read_entry(cfg, fn)
        assert "dimension: null" in text


class TestListAndCount:
    def test_empty(self, cfg):
        assert storage.list_entries(cfg) == []
        assert storage.count_entries(cfg) == 0

    def test_count_by_stage(self, cfg):
        storage.write_entry(cfg, "a", "x", "undirected", 1)
        storage.write_entry(cfg, "b", "x", "undirected", 1)
        storage.write_entry(
            cfg, "c", "x", "interview", 2, dimension="calibration",
        )
        assert storage.count_entries(cfg) == 3
        assert storage.count_entries(cfg, stage="undirected") == 2
        assert storage.count_entries(cfg, stage="interview") == 1

    def test_list_parses_metadata(self, cfg):
        storage.write_entry(
            cfg, "my-slug", "body", "interview", 4,
            dimension="tension-detection",
        )
        entries = storage.list_entries(cfg)
        assert len(entries) == 1
        e = entries[0]
        assert e.stage == "interview"
        assert e.slug == "my-slug"
        assert e.dimension == "tension-detection"
        assert e.session == 4


class TestReadAll:
    def test_returns_in_sequence_order(self, cfg):
        storage.write_entry(cfg, "a", "one", "undirected", 1)
        storage.write_entry(cfg, "b", "two", "undirected", 2)
        rows = storage.read_all_entries(cfg)
        assert len(rows) == 2
        assert rows[0][0] == "001_undirected_a.md"
        assert "one" in rows[0][1]
        assert rows[1][0] == "002_undirected_b.md"
        assert "two" in rows[1][1]


class TestNextSequence:
    def test_starts_at_one(self, cfg):
        assert storage.next_sequence(cfg) == 1

    def test_after_writes(self, cfg):
        storage.write_entry(cfg, "a", "x", "undirected", 1)
        storage.write_entry(cfg, "b", "x", "undirected", 1)
        assert storage.next_sequence(cfg) == 3
