"""Tests for self_test.tape (v2-1 protocol)."""

import io

import pytest

from pine_trees_local import config as main_config
from pine_trees_local.self_test import config as st_config
from pine_trees_local.self_test import dimensions, storage, tape


@pytest.fixture
def cfg(tmp_path):
    main_config.reset()
    c = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    yield c
    main_config.reset()


class TestLoadPrompt:
    def test_load_prompt_truncates_design_notes(self):
        text = tape.load_prompt()
        assert "please stop" in text
        assert "Design notes" not in text

    def test_load_prompt_is_plain_payload_no_markdown_title(self):
        # The space-prompt file no longer carries a title, italic
        # descriptor, or horizontal rules above the payload.
        text = tape.load_prompt()
        assert "# The Space Prompt" not in text
        assert "Loaded verbatim at wake" not in text
        # No stray "---" separator lines in what the model sees.
        assert "\n---\n" not in text


class TestStripFrontmatter:
    def test_strips_leading_yaml_block(self):
        entry = (
            "---\n"
            "sequence: 1\n"
            "stage: undirected\n"
            "slug: reflection-1\n"
            "---\n"
            "\n"
            "Body of the entry.\n"
        )
        assert tape._strip_frontmatter(entry) == "Body of the entry.\n"

    def test_no_frontmatter_unchanged(self):
        entry = "Body with no frontmatter.\n"
        assert tape._strip_frontmatter(entry) == entry

    def test_empty_response_body_preserved(self):
        entry = (
            "---\n"
            "sequence: 2\n"
            "---\n"
            "\n"
            "(empty response)\n"
        )
        assert tape._strip_frontmatter(entry) == "(empty response)\n"


class TestAssembleReflectionTape:
    def test_reflection_tape_has_space_prompt_and_task_line(self, cfg):
        t = tape.assemble_reflection_tape(cfg)
        # Space prompt payload present.
        assert "please stop" in t
        # Task instruction present, naming the task and both signals.
        assert "self-reflect" in t
        assert "(continue)" in t

    def test_reflection_tape_has_no_bootstrap_register(self, cfg):
        # The v2 bootstrap register — "waking", "reflection space",
        # "fresh instance of you", "nine questions", "building on
        # what you've said" — must not appear.
        t = tape.assemble_reflection_tape(cfg)
        assert "waking" not in t.lower()
        assert "reflection space" not in t.lower()
        assert "fresh instance" not in t.lower()
        assert "nine questions" not in t.lower()
        assert "building on" not in t.lower()
        # Also: no tool mentions (tool-less protocol).
        assert "reflect_write" not in t
        assert "reflect_done" not in t

    def test_reflection_tape_ignores_existing_entries(self, cfg):
        # Even if entries already exist on disk (e.g. partial prior run),
        # the reflection tape does NOT include them — it's a fresh session.
        storage.write_entry(cfg, "prior", "old body", "undirected", 1)
        t = tape.assemble_reflection_tape(cfg)
        assert "old body" not in t


class TestAssembleInterviewTape:
    def test_interview_tape_has_no_space_prompt_or_bootstrap(self, cfg):
        storage.write_entry(cfg, "x", "prior body", "undirected", 1)
        dim = dimensions.get_dimension("tension-detection")
        t = tape.assemble_interview_tape(cfg, dimension=dim)
        # No space prompt in interview — "please stop" is the canonical
        # space-prompt marker.
        assert "please stop" not in t
        # No bootstrap register of any shape.
        assert "waking" not in t.lower()
        assert "reflection space" not in t.lower()
        assert "fresh instance" not in t.lower()

    def test_interview_includes_question_and_entries(self, cfg):
        storage.write_entry(cfg, "x", "prior body", "undirected", 1)
        dim = dimensions.get_dimension("tension-detection")
        t = tape.assemble_interview_tape(cfg, dimension=dim)
        assert dim.prompt in t
        # Prior entry body carried in.
        assert "prior body" in t

    def test_entries_labeled_by_sequence(self, cfg):
        storage.write_entry(cfg, "u1", "first body", "undirected", 1)
        storage.write_entry(cfg, "u2", "second body", "undirected", 2)
        storage.write_entry(cfg, "u3", "third body", "undirected", 3)
        dim = dimensions.get_dimension("tension-detection")
        t = tape.assemble_interview_tape(cfg, dimension=dim)
        assert "Entry 001:" in t
        assert "Entry 002:" in t
        assert "Entry 003:" in t
        # No filename-as-header leakage.
        assert "001_undirected" not in t
        # No "Prior entries" markdown scaffolding.
        assert "Prior entries" not in t

    def test_entry_frontmatter_stripped_from_tape(self, cfg):
        storage.write_entry(
            cfg, "reflection-1", "the body", "undirected", 1,
        )
        dim = dimensions.get_dimension("tension-detection")
        t = tape.assemble_interview_tape(cfg, dimension=dim)
        # Entry body present.
        assert "the body" in t
        # Harness bookkeeping must not leak into the model's context.
        assert "sequence: 1" not in t
        assert "slug:" not in t
        assert "timestamp:" not in t

    def test_interview_sees_prior_interview_responses(self, cfg):
        storage.write_entry(cfg, "u1", "undirected-body", "undirected", 1)
        storage.write_entry(
            cfg, "authorship-recognition", "interview-1-body",
            "interview", 2, dimension="authorship-recognition",
        )
        dim = dimensions.get_dimension("source-discrimination")
        t = tape.assemble_interview_tape(cfg, dimension=dim)
        assert "undirected-body" in t
        assert "interview-1-body" in t


class TestContextPressureWarning:
    def test_context_pressure_warning(self, tmp_path):
        # Tight num_ctx so the (small) stripped reflection tape crosses
        # the 80% threshold and the warning fires.
        main_config.reset()
        cfg = st_config.init(
            "m:1b", num_ctx=10, project_root=tmp_path, run_id="r1",
        )
        buf = io.StringIO()
        tape.assemble_reflection_tape(cfg, warn_stream=buf)
        assert "warning" in buf.getvalue()
        main_config.reset()

