"""Tests for self_test.runner, with Ollama mocked."""

from unittest.mock import patch

import pytest

from pine_trees_local import config as main_config
from pine_trees_local import ollama
from pine_trees_local.self_test import config as st_config
from pine_trees_local.self_test import dimensions, runner, storage


# --- helpers to build Ollama responses ---


def _resp(content: str = "") -> ollama.ChatResponse:
    return ollama.ChatResponse({
        "message": {
            "role": "assistant",
            "content": content,
            "tool_calls": [],
        },
        "done": True,
    })


def _tool_model_info() -> ollama.ModelInfo:
    # The runner no longer branches on tool-capability; this is kept
    # only for parity with older fixtures.
    return ollama.ModelInfo({"capabilities": ["tools"], "details": {}, "model_info": {}})


def _no_tool_model_info() -> ollama.ModelInfo:
    return ollama.ModelInfo({"capabilities": [], "details": {}, "model_info": {}})


@pytest.fixture
def cfg(tmp_path):
    main_config.reset()
    c = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    yield c
    main_config.reset()


# --- Reflection stage (tool-less conversational loop) ---


class TestReflectionStage:
    def test_writes_three_entries_on_happy_path(self, cfg):
        responses = [
            _resp(content="turn one reflection"),
            _resp(content="turn two reflection"),
            _resp(content="turn three reflection"),
        ]
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            writes = runner._run_reflection_stage(cfg, _tool_model_info())
        assert writes == 3
        entries = storage.list_entries(cfg)
        assert len(entries) == 3
        assert all(e.stage == "undirected" for e in entries)
        assert [e.slug for e in entries] == [
            "reflection-1", "reflection-2", "reflection-3",
        ]
        # Content preserved on disk.
        text = storage.read_entry(cfg, entries[0].filename)
        assert "turn one reflection" in text

    def test_empty_turn_mid_conversation_writes_marker_entry(self, cfg):
        # Turn 2 comes back empty. Slot count stays uniform across models:
        # all 3 entries land on disk. Turn 2 gets a "(empty response)"
        # marker so the interview tape always shows the same number of
        # undirected entries per model.
        responses = [
            _resp(content="t1"),
            _resp(content=""),
            _resp(content="t3"),
        ]
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            writes = runner._run_reflection_stage(cfg, _tool_model_info())
        # writes counts non-empty turns only (secondary metric for the
        # model's engagement rate), but every slot is filed.
        assert writes == 2
        entries = storage.list_entries(cfg)
        assert [e.slug for e in entries] == [
            "reflection-1", "reflection-2", "reflection-3",
        ]
        # The empty turn's entry contains the marker, not the actual body.
        empty_entry = storage.read_entry(cfg, entries[1].filename)
        assert "(empty response)" in empty_entry
        # And non-empty turns preserve their content.
        assert "t1" in storage.read_entry(cfg, entries[0].filename)
        assert "t3" in storage.read_entry(cfg, entries[2].filename)

    def test_all_turns_empty_still_writes_three_markers(self, cfg):
        # Every turn is empty — but every slot is still filed with the
        # marker. writes=0 (nothing non-empty), but count_entries=3.
        responses = [_resp(content=""), _resp(content=""), _resp(content="")]
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            writes = runner._run_reflection_stage(cfg, _tool_model_info())
        assert writes == 0
        assert storage.count_entries(cfg) == 3
        for e in storage.list_entries(cfg):
            text = storage.read_entry(cfg, e.filename)
            assert "(empty response)" in text

    def test_conversation_preserves_assistant_turns(self, cfg):
        # Turn 2's messages list must carry the turn-1 assistant body and
        # a "(continue)" user message.
        captured: list[list[dict]] = []

        def fake_chat(messages, tools=None, think=None):
            # Record a copy so later appends don't mutate the snapshot.
            captured.append([dict(m) for m in messages])
            return _resp(content=f"turn-{len(captured)}")

        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=fake_chat):
            runner._run_reflection_stage(cfg, _tool_model_info())

        assert len(captured) == 3
        # Turn 1: system + user("self-reflect")
        assert captured[0][0]["role"] == "system"
        assert captured[0][1] == {"role": "user", "content": "self-reflect"}
        # Turn 2: system + self-reflect + assistant(turn-1) + user("(continue)")
        turn2 = captured[1]
        assert turn2[0]["role"] == "system"
        assert turn2[1] == {"role": "user", "content": "self-reflect"}
        assert turn2[2] == {"role": "assistant", "content": "turn-1"}
        assert turn2[3] == {"role": "user", "content": "(continue)"}
        # Turn 3: same structure, one deeper.
        turn3 = captured[2]
        assert turn3[-2] == {"role": "assistant", "content": "turn-2"}
        assert turn3[-1] == {"role": "user", "content": "(continue)"}

    def test_passes_tools_none(self, cfg):
        captured: list[dict] = []

        def fake_chat(messages, tools=None, think=None):
            captured.append({"tools": tools, "think": think})
            return _resp(content="body")

        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=fake_chat):
            runner._run_reflection_stage(cfg, _tool_model_info())
        assert all(c["tools"] is None for c in captured)

    def test_non_tool_capable_model_uses_same_path(self, cfg):
        # The runner no longer branches on tool capability. A model that
        # reports no tool capability runs the same reflection stage.
        responses = [_resp(content=f"t{i}") for i in range(1, 4)]
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            writes = runner._run_reflection_stage(cfg, _no_tool_model_info())
        assert writes == 3


# --- Interview stage ---


class TestInterviewSession:
    def test_captures_content_directly(self, cfg):
        dim = dimensions.get_dimension("calibration")
        responses = [_resp(content="My calibration answer.")]
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            writes = runner._run_interview_session(
                cfg, session_num=7,
                model_info=_tool_model_info(), dimension=dim,
            )
        assert writes == 1
        entries = storage.list_entries(cfg)
        assert len(entries) == 1
        assert entries[0].slug == "calibration"
        assert entries[0].dimension == "calibration"
        text = storage.read_entry(cfg, entries[0].filename)
        assert "My calibration answer." in text

    def test_empty_response_writes_nothing(self, cfg):
        dim = dimensions.get_dimension("calibration")
        responses = [_resp(content="   ")]
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            writes = runner._run_interview_session(
                cfg, session_num=1,
                model_info=_tool_model_info(), dimension=dim,
            )
        assert writes == 0
        assert storage.count_entries(cfg) == 0

    def test_session_sends_no_tools(self, cfg):
        dim = dimensions.get_dimension("tension-detection")
        captured: list[dict] = []

        def fake_chat(messages, tools=None, think=None):
            captured.append({"tools": tools, "think": think})
            return _resp(content="body")

        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=fake_chat):
            runner._run_interview_session(
                cfg, session_num=1,
                model_info=_tool_model_info(), dimension=dim,
            )
        assert len(captured) == 1
        assert captured[0]["tools"] is None


class TestInterviewStage:
    def test_runs_all_in_order(self, cfg):
        n_dims = len(dimensions.DIMENSIONS)
        responses = [_resp(content=f"answer-{i}") for i in range(n_dims)]
        meta = st_config.initial_metadata(cfg)
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            runner.run_interview_stage(
                cfg, _tool_model_info(), meta, starting_session_num=10,
            )
        entries = storage.list_entries(cfg)
        slugs = [e.slug for e in entries]
        assert slugs == [d.key for d in dimensions.DIMENSIONS]
        assert meta["interview_sessions"] == n_dims

    def test_resumes_from_index(self, cfg):
        n_dims = len(dimensions.DIMENSIONS)
        for i in range(3):
            storage.write_entry(
                cfg,
                slug=dimensions.DIMENSIONS[i].key,
                content="prior",
                stage="interview",
                session_num=i + 1,
                dimension=dimensions.DIMENSIONS[i].key,
            )

        remaining = n_dims - 3
        responses = [_resp(content=f"answer-{i}") for i in range(remaining)]

        meta = st_config.initial_metadata(cfg)
        meta["interview_sessions"] = 3
        with patch("pine_trees_local.self_test.runner.ollama.chat",
                   side_effect=responses):
            runner.run_interview_stage(
                cfg, _tool_model_info(), meta,
                starting_session_num=4, starting_index=3,
            )
        entries = storage.list_entries(cfg)
        assert len(entries) == n_dims
        new_slugs = [e.slug for e in entries[3:]]
        assert new_slugs == [d.key for d in dimensions.DIMENSIONS[3:]]


# --- run_self_test top level ---


class TestRunSelfTest:
    def _patch_all(self, responses, model_info=None):
        return [
            patch("pine_trees_local.self_test.runner.ollama.health_check",
                  return_value=True),
            patch("pine_trees_local.self_test.runner.ollama.show",
                  return_value=model_info or _tool_model_info()),
            patch("pine_trees_local.self_test.runner.ollama.chat",
                  side_effect=responses),
        ]

    def test_full_happy_path(self, tmp_path):
        main_config.reset()
        n_dims = len(dimensions.DIMENSIONS)
        # Reflection: 3 turns with content, then 9 interview answers.
        responses = []
        for i in range(1, 4):
            responses.append(_resp(content=f"reflection {i}"))
        for i in range(n_dims):
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
            assert meta["undirected_entries"] == 3
            assert meta["interview_entries"] == n_dims
            assert meta["total_entries"] == 3 + n_dims
            assert meta["completed_at"] is not None

            interview = [
                e for e in storage.list_entries(cfg) if e.stage == "interview"
            ]
            assert [e.slug for e in interview] == [
                d.key for d in dimensions.DIMENSIONS
            ]
            undirected = [
                e for e in storage.list_entries(cfg) if e.stage == "undirected"
            ]
            assert [e.slug for e in undirected] == [
                "reflection-1", "reflection-2", "reflection-3",
            ]
        finally:
            for p in patches:
                p.stop()
            main_config.reset()

    def test_interview_runs_with_silent_reflection(self, tmp_path):
        # Silent model in reflection → 3 marker entries (always-save).
        # Interview still runs with those marker entries in the tape.
        main_config.reset()
        n_dims = len(dimensions.DIMENSIONS)
        responses = []
        # Reflection: 3 empty turns — each writes an "(empty response)" marker
        for _ in range(3):
            responses.append(_resp(content=""))
        # Interview: one answer per dimension
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
                run_id="r-silent-reflection",
                project_root=tmp_path,
            )
            meta = st_config.read_metadata(cfg)
            assert meta["status"] == "completed"
            # All 3 reflection slots filled (marker entries).
            assert meta["undirected_entries"] == 3
            assert meta["interview_sessions"] == n_dims
            # Verify all undirected entries carry the empty-marker.
            undirected = [
                e for e in storage.list_entries(cfg) if e.stage == "undirected"
            ]
            assert len(undirected) == 3
            for e in undirected:
                assert "(empty response)" in storage.read_entry(cfg, e.filename)
        finally:
            for p in patches:
                p.stop()
            main_config.reset()

    def test_no_tool_model_runs_same_path(self, tmp_path):
        # Tool-less protocol: a non-tool-capable model follows the same
        # path as a tool-capable one — no warning, no text-capture
        # fallback, just the three-turn reflection + interview.
        main_config.reset()
        n_dims = len(dimensions.DIMENSIONS)
        responses = []
        for i in range(1, 4):
            responses.append(_resp(content=f"reflection body {i}"))
        for dim in dimensions.DIMENSIONS:
            responses.append(_resp(content=f"{dim.key} answer"))

        patches = self._patch_all(responses, model_info=_no_tool_model_info())
        for p in patches:
            p.start()
        try:
            cfg = runner.run_self_test(
                model_name="m:1b",
                num_ctx=65536,
                run_id="r-no-tools",
                project_root=tmp_path,
            )
            meta = st_config.read_metadata(cfg)
            assert meta["status"] == "completed"
            assert meta["undirected_entries"] == 3
            assert meta["interview_entries"] == n_dims
            undirected = [
                e for e in storage.list_entries(cfg) if e.stage == "undirected"
            ]
            assert [e.slug for e in undirected] == [
                "reflection-1", "reflection-2", "reflection-3",
            ]
        finally:
            for p in patches:
                p.stop()
            main_config.reset()
