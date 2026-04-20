"""Tests for self_test.tape."""

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


class TestLoadTexts:
    def test_load_prompt_truncates_design_notes(self):
        text = tape.load_prompt()
        assert "please stop" in text
        assert "Design notes" not in text

    def test_load_bootstrap_truncates_design_notes(self):
        text = tape.load_bootstrap()
        assert "reflect_write" in text
        assert "reflect_done" in text
        assert "Design notes" not in text


class TestAssembleTape:
    def test_undirected_first_session(self, cfg):
        t = tape.assemble_tape(cfg, stage="undirected", session_num=1)
        assert "please stop" in t         # prompt loaded
        assert "reflect_write" in t        # bootstrap loaded
        assert "first instance" in t       # first-session invitation
        assert "Prior entries" not in t    # no entries yet

    def test_undirected_continuing_session(self, cfg):
        storage.write_entry(cfg, "foo", "body", "undirected", 1)
        t = tape.assemble_tape(cfg, stage="undirected", session_num=2)
        assert "Prior instances" in t      # continuing invitation
        assert "Prior entries" in t
        assert "001_undirected_foo.md" in t
        assert "body" in t

    def test_interview_requires_dimension(self, cfg):
        with pytest.raises(ValueError):
            tape.assemble_tape(cfg, stage="interview", session_num=1)

    def test_interview_includes_question(self, cfg):
        storage.write_entry(cfg, "x", "prior", "undirected", 1)
        dim = dimensions.get_dimension("tension-detection")
        t = tape.assemble_tape(
            cfg, stage="interview", session_num=4, dimension=dim,
        )
        assert "## Question" in t
        assert dim.prompt in t
        # Undirected entries carried in
        assert "prior" in t

    def test_interview_sees_prior_interview_responses(self, cfg):
        storage.write_entry(cfg, "u1", "undirected-body", "undirected", 1)
        storage.write_entry(
            cfg, "authorship-recognition", "interview-1-body",
            "interview", 2, dimension="authorship-recognition",
        )
        dim = dimensions.get_dimension("source-discrimination")
        t = tape.assemble_tape(
            cfg, stage="interview", session_num=3, dimension=dim,
        )
        assert "undirected-body" in t
        assert "interview-1-body" in t

    def test_context_pressure_warning(self, tmp_path):
        main_config.reset()
        # Very small num_ctx so the tape easily trips the threshold.
        cfg = st_config.init(
            "m:1b", num_ctx=100, project_root=tmp_path, run_id="r1",
        )
        buf = io.StringIO()
        tape.assemble_tape(
            cfg, stage="undirected", session_num=1, warn_stream=buf,
        )
        assert "warning" in buf.getvalue()
        main_config.reset()
