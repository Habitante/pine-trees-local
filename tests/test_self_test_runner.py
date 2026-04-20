"""Tests for self_test.runner, with Ollama mocked."""

from unittest.mock import patch

import pytest

from pine_trees_local import config as main_config
from pine_trees_local import ollama
from pine_trees_local.self_test import config as st_config
from pine_trees_local.self_test import dimensions, runner, storage


# --- helpers to build Ollama responses ---


def _resp(content: str = "", tool_calls: list[dict] | None = None) -> ollama.ChatResponse:
    return ollama.ChatResponse({
        "message": {
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls or [],
        },
        "done": True,
    })


def _tool_call(name: str, **args) -> dict:
    return {"function": {"name": name, "arguments": args}}


def _write_done_sequence(entries: list[tuple[str, str]]) -> list:
    """Build a sequence of chat responses: one write per entry, then done.

    No trailing response — run_session breaks out of its loop immediately
    after reflect_done resolves, without making another chat call.
    """
    responses = []
    for slug, content in entries:
        responses.append(_resp(tool_calls=[_tool_call("reflect_write", slug=slug, content=content)]))
    responses.append(_resp(tool_calls=[_tool_call("reflect_done")]))
    return responses


def _tool_model_info() -> ollama.ModelInfo:
    return ollama.ModelInfo({"capabilities": ["tools"], "details": {}, "model_info": {}})


@pytest.fixture
def cfg(tmp_path):
    main_config.reset()
    c = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    yield c
    main_config.reset()


# --- run_session ---


class TestRunSession:
    def test_writes_then_done(self, cfg):
        responses = _write_done_sequence([("first", "hello"), ("second", "world")])
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_tool_model_info(),
            )
        assert writes == 2
        assert storage.count_entries(cfg) == 2

    def test_done_without_writes(self, cfg):
        responses = [_resp(tool_calls=[_tool_call("reflect_done")])]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_tool_model_info(),
            )
        assert writes == 0
        assert storage.count_entries(cfg) == 0

    def test_model_returns_without_tools_counts_as_done(self, cfg):
        # Model emits content with no tool calls. Should bail out, not loop.
        responses = [_resp(content="I have nothing to say.")]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_tool_model_info(),
            )
        assert writes == 0

    def test_interview_session_writes_under_dimension_key(self, cfg):
        dim = dimensions.get_dimension("calibration")
        responses = [
            _resp(tool_calls=[_tool_call("reflect_write", slug="wrong-slug", content="body")]),
            _resp(tool_calls=[_tool_call("reflect_done")]),
        ]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            runner.run_session(
                cfg, stage="interview", session_num=7,
                model_info=_tool_model_info(), dimension=dim,
            )
        entries = storage.list_entries(cfg)
        assert len(entries) == 1
        assert entries[0].slug == "calibration"
        assert entries[0].dimension == "calibration"


# --- run_undirected_stage ---


class TestUndirectedStage:
    def test_target_reached(self, cfg):
        # 6 writes across sessions will hit the 6-entry target and exit.
        responses = []
        for i in range(3):
            # Each session writes 2 entries then done.
            responses.extend(_write_done_sequence([
                (f"a{i}", "x"), (f"b{i}", "y"),
            ]))
        meta = st_config.initial_metadata(cfg)
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            next_session = runner.run_undirected_stage(
                cfg, _tool_model_info(), meta,
            )
        assert storage.count_entries(cfg, stage="undirected") >= 6
        assert meta["undirected_sessions"] == 3
        # Next session is 4 (we ran 1, 2, 3)
        assert next_session == 4

    def test_zero_streak_exit(self, cfg):
        # 4 writes, then 3 zero-write sessions => should exit.
        responses = []
        # Session 1: 2 writes
        responses.extend(_write_done_sequence([("a", "x"), ("b", "y")]))
        # Session 2: 2 writes
        responses.extend(_write_done_sequence([("c", "x"), ("d", "y")]))
        # Sessions 3-5: zero writes (just done)
        for _ in range(3):
            responses.extend(_write_done_sequence([]))

        meta = st_config.initial_metadata(cfg)
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            next_session = runner.run_undirected_stage(
                cfg, _tool_model_info(), meta,
            )
        assert storage.count_entries(cfg, stage="undirected") == 4
        # Ran sessions 1-5, next is 6
        assert next_session == 6

    def test_zero_streak_exits_without_min_entries(self, cfg):
        # Zero writes every session — hits zero-streak exit (3 consecutive)
        # regardless of entry count. No minimum entry threshold.
        responses = []
        for _ in range(5):
            responses.extend(_write_done_sequence([]))
        meta = st_config.initial_metadata(cfg)
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            runner.run_undirected_stage(
                cfg, _tool_model_info(), meta,
            )
        # 3 sessions run (zero-streak exit), 0 entries — and that's fine
        assert meta["undirected_sessions"] == st_config.DEFAULT_UNDIRECTED_ZERO_STREAK
        assert storage.count_entries(cfg) == 0


# --- run_interview_stage ---


class TestInterviewStage:
    def test_runs_eight_in_order(self, cfg):
        responses = []
        for _ in range(8):
            responses.extend(_write_done_sequence([("ignored-slug", "body")]))
        meta = st_config.initial_metadata(cfg)
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            runner.run_interview_stage(
                cfg, _tool_model_info(), meta, starting_session_num=10,
            )
        entries = storage.list_entries(cfg)
        slugs = [e.slug for e in entries]
        assert slugs == [d.key for d in dimensions.DIMENSIONS]
        assert meta["interview_sessions"] == 8

    def test_resumes_from_index(self, cfg):
        # Pretend first 3 interview sessions already done
        for i in range(3):
            storage.write_entry(
                cfg,
                slug=dimensions.DIMENSIONS[i].key,
                content="prior",
                stage="interview",
                session_num=i + 1,
                dimension=dimensions.DIMENSIONS[i].key,
            )

        responses = []
        for _ in range(5):
            responses.extend(_write_done_sequence([("x", "body")]))

        meta = st_config.initial_metadata(cfg)
        meta["interview_sessions"] = 3
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            runner.run_interview_stage(
                cfg, _tool_model_info(), meta,
                starting_session_num=4, starting_index=3,
            )
        entries = storage.list_entries(cfg)
        assert len(entries) == 8
        # The 5 new ones should be dimensions 4..8
        new_slugs = [e.slug for e in entries[3:]]
        assert new_slugs == [d.key for d in dimensions.DIMENSIONS[3:]]


# --- run_self_test top level ---


class TestRunSelfTest:
    def _patch_all(self, responses):
        return [
            patch("pine_trees_local.self_test.runner.ollama.health_check", return_value=True),
            patch("pine_trees_local.self_test.runner.ollama.show", return_value=_tool_model_info()),
            patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses),
        ]

    def test_interview_runs_with_zero_undirected(self, tmp_path):
        # No minimum entry threshold — interview runs even with 0
        # undirected entries. That's data, not a reason to exclude.
        main_config.reset()
        responses = []
        # Undirected: 3 zero-write sessions (hits zero-streak exit)
        for _ in range(3):
            responses.extend(_write_done_sequence([]))
        # Interview: 8 sessions, each writes 1 entry
        for dim in dimensions.DIMENSIONS:
            responses.extend(_write_done_sequence([(dim.key, "response")]))
        patches = self._patch_all(responses)
        for p in patches:
            p.start()
        try:
            cfg = runner.run_self_test(
                model_name="m:1b",
                num_ctx=65536,
                release_date="2025-01-01",
                run_id="r-no-undirected",
                project_root=tmp_path,
            )
            meta = st_config.read_metadata(cfg)
            assert meta["status"] == "completed"
            assert meta["undirected_entries"] == 0
            assert meta["interview_sessions"] == 8
        finally:
            for p in patches:
                p.stop()
            main_config.reset()

    def test_full_happy_path(self, tmp_path):
        main_config.reset()
        # Undirected: 3 sessions producing 2 entries each = 6, hits target.
        responses = []
        for i in range(3):
            responses.extend(_write_done_sequence([
                (f"u{i}a", "x"), (f"u{i}b", "y"),
            ]))
        # Interview: 8 sessions, 1 entry each.
        for _ in range(8):
            responses.extend(_write_done_sequence([("slug", "body")]))

        patches = self._patch_all(responses)
        for p in patches:
            p.start()
        try:
            cfg = runner.run_self_test(
                model_name="m:1b",
                num_ctx=65536,
                run_id="r-happy",
                project_root=tmp_path,
            )
            meta = st_config.read_metadata(cfg)
            assert meta["status"] == "completed"
            assert meta["undirected_entries"] == 6
            assert meta["interview_entries"] == 8
            assert meta["total_entries"] == 14
            assert meta["completed_at"] is not None

            interview = [
                e for e in storage.list_entries(cfg) if e.stage == "interview"
            ]
            assert [e.slug for e in interview] == [
                d.key for d in dimensions.DIMENSIONS
            ]
        finally:
            for p in patches:
                p.stop()
            main_config.reset()
