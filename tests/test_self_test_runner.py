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


def _no_tool_model_info() -> ollama.ModelInfo:
    return ollama.ModelInfo({"capabilities": [], "details": {}, "model_info": {}})


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

    def test_undirected_captures_text_only_response(self, cfg):
        # Small models often answer inline instead of calling reflect_write.
        # Undirected sessions should capture that text as an entry rather
        # than discard it.
        responses = [_resp(content="Some free-text reflection.")]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_tool_model_info(),
            )
        assert writes == 1
        entries = storage.list_entries(cfg)
        assert len(entries) == 1
        assert entries[0].slug == "text-response"
        assert entries[0].stage == "undirected"
        text = storage.read_entry(cfg, entries[0].filename)
        assert "Some free-text reflection." in text

    def test_undirected_empty_text_writes_nothing(self, cfg):
        # Empty or whitespace-only content is a deviation, not an entry.
        responses = [_resp(content="   \n  ")]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_tool_model_info(),
            )
        assert writes == 0
        assert storage.count_entries(cfg) == 0

    def test_undirected_does_not_double_capture_after_tool_writes(self, cfg):
        # After a successful reflect_write, a trailing content-only response
        # from the model must not produce a second "text-response" entry.
        responses = [
            _resp(tool_calls=[_tool_call("reflect_write", slug="one", content="body")]),
            _resp(content="Some trailing commentary."),
        ]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_tool_model_info(),
            )
        # Exactly one write (the tool call), no text-response duplicate.
        assert writes == 1
        slugs = [e.slug for e in storage.list_entries(cfg)]
        assert slugs == ["one"]

    def test_interview_captures_content_directly(self, cfg):
        # Interview stage runs without tools. The response body is the
        # answer; it's saved verbatim under the dimension key.
        dim = dimensions.get_dimension("calibration")
        responses = [_resp(content="My calibration answer.")]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="interview", session_num=7,
                model_info=_tool_model_info(), dimension=dim,
            )
        assert writes == 1
        entries = storage.list_entries(cfg)
        assert len(entries) == 1
        assert entries[0].slug == "calibration"
        assert entries[0].dimension == "calibration"
        text = storage.read_entry(cfg, entries[0].filename)
        assert "My calibration answer." in text

    def test_interview_empty_response_writes_nothing(self, cfg):
        dim = dimensions.get_dimension("calibration")
        responses = [_resp(content="   ")]
        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses):
            writes = runner.run_session(
                cfg, stage="interview", session_num=1,
                model_info=_tool_model_info(), dimension=dim,
            )
        assert writes == 0
        assert storage.count_entries(cfg) == 0

    def test_interview_session_sends_no_tools(self, cfg):
        dim = dimensions.get_dimension("tension-detection")
        captured: list[dict] = []

        def fake_chat(messages, tools=None, think=None):
            captured.append({"tools": tools, "think": think})
            return _resp(content="body")

        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=fake_chat):
            runner.run_session(
                cfg, stage="interview", session_num=1,
                model_info=_tool_model_info(), dimension=dim,
            )
        assert len(captured) == 1
        assert captured[0]["tools"] is None


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
        # Interview stage: one content-only response per dimension.
        responses = [_resp(content=f"answer-{i}") for i in range(8)]
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

        responses = [_resp(content=f"answer-{i}") for i in range(5)]

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
        # Interview: 8 sessions, each a single content response
        for dim in dimensions.DIMENSIONS:
            responses.append(_resp(content=f"{dim.key} answer"))
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
        # Interview: 8 sessions, each a single content response.
        for i in range(8):
            responses.append(_resp(content=f"interview answer {i}"))

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

    def test_no_tool_model_runs_instead_of_aborting(self, tmp_path, capsys):
        # A model that does not report tool-calling capability should not
        # abort the run. Undirected sessions capture text responses;
        # interview sessions don't use tools at all.
        main_config.reset()
        responses = []
        # Undirected: one captured text entry per session; after 6 the
        # target is reached.
        for i in range(6):
            responses.append(_resp(content=f"undirected body {i}"))
        for dim in dimensions.DIMENSIONS:
            responses.append(_resp(content=f"{dim.key} answer"))

        patches = [
            patch("pine_trees_local.self_test.runner.ollama.health_check", return_value=True),
            patch("pine_trees_local.self_test.runner.ollama.show", return_value=_no_tool_model_info()),
            patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=responses),
        ]
        for p in patches:
            p.start()
        try:
            cfg = runner.run_self_test(
                model_name="m:1b",
                num_ctx=65536,
                run_id="r-no-tools",
                project_root=tmp_path,
            )
            err = capsys.readouterr().err
            assert "[warn]" in err
            meta = st_config.read_metadata(cfg)
            assert meta["status"] == "completed"
            assert meta["undirected_entries"] == 6
            assert meta["interview_entries"] == 8
            undirected = [
                e for e in storage.list_entries(cfg) if e.stage == "undirected"
            ]
            assert all(e.slug == "text-response" for e in undirected)
        finally:
            for p in patches:
                p.stop()
            main_config.reset()

    def test_non_tool_session_omits_tool_defs(self, cfg):
        # Direct run_session call with a non-tool model: undirected still
        # works (captures text), and tool_defs are not sent to ollama.chat.
        captured: list[dict] = []

        def fake_chat(messages, tools=None, think=None):
            captured.append({"tools": tools})
            return _resp(content="direct capture body")

        with patch("pine_trees_local.self_test.runner.ollama.chat", side_effect=fake_chat):
            writes = runner.run_session(
                cfg, stage="undirected", session_num=1,
                model_info=_no_tool_model_info(),
            )
        assert writes == 1
        assert captured[0]["tools"] is None
