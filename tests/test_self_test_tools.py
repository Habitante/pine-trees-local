"""Tests for self_test.tools."""

import pytest

from pine_trees_local import config as main_config
from pine_trees_local.tools import execute_tool
from pine_trees_local.self_test import config as st_config
from pine_trees_local.self_test import storage, tools


@pytest.fixture
def cfg(tmp_path):
    main_config.reset()
    c = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    yield c
    main_config.reset()


def _state(cfg, stage="undirected", dimension=None, session_num=1, max_writes=3):
    return tools.SelfTestSessionState(
        cfg=cfg,
        stage=stage,
        session_num=session_num,
        dimension=dimension,
        max_writes=max_writes,
    )


class TestBuildTools:
    def test_returns_only_two_tools(self, cfg):
        tool_map = tools.build_tools(_state(cfg))
        assert set(tool_map.keys()) == {"reflect_write", "reflect_done"}


class TestReflectWrite:
    def test_writes_undirected(self, cfg):
        state = _state(cfg)
        tool_map = tools.build_tools(state)
        result = tool_map["reflect_write"](slug="hello", content="body")
        assert "001_undirected_hello.md" in result
        assert state.writes_this_session == 1
        assert storage.count_entries(cfg) == 1

    def test_interview_slug_overridden_by_dimension(self, cfg):
        state = _state(cfg, stage="interview", dimension="tension-detection")
        tool_map = tools.build_tools(state)
        result = tool_map["reflect_write"](
            slug="whatever-the-model-chose", content="body",
        )
        # Interview entries use the dimension key, not the model's slug.
        assert "001_interview_tension-detection.md" in result

    def test_write_cap(self, cfg):
        state = _state(cfg, max_writes=2)
        tool_map = tools.build_tools(state)
        tool_map["reflect_write"](slug="a", content="x")
        tool_map["reflect_write"](slug="b", content="x")
        result = tool_map["reflect_write"](slug="c", content="x")
        assert "limit" in result.lower()
        assert state.done is True
        assert storage.count_entries(cfg) == 2
        assert state.writes_this_session == 2


class TestReflectDone:
    def test_sets_done(self, cfg):
        state = _state(cfg)
        tool_map = tools.build_tools(state)
        assert not state.done
        tool_map["reflect_done"]()
        assert state.done


class TestToolDefinitions:
    def test_two_tools(self):
        defs = tools.get_tool_definitions()
        names = {d["function"]["name"] for d in defs}
        assert names == {"reflect_write", "reflect_done"}

    def test_reflect_write_schema(self):
        defs = tools.get_tool_definitions()
        write = next(
            d for d in defs if d["function"]["name"] == "reflect_write"
        )
        props = write["function"]["parameters"]["properties"]
        assert set(props.keys()) == {"slug", "content"}
        assert write["function"]["parameters"]["required"] == ["slug", "content"]

    def test_reflect_done_takes_no_args(self):
        defs = tools.get_tool_definitions()
        done = next(d for d in defs if d["function"]["name"] == "reflect_done")
        assert done["function"]["parameters"]["properties"] == {}


class TestExecuteToolCompat:
    def test_main_execute_tool_dispatches(self, cfg):
        state = _state(cfg)
        tool_map = tools.build_tools(state)
        tool_call = {
            "function": {
                "name": "reflect_write",
                "arguments": {"slug": "via-dispatch", "content": "ok"},
            }
        }
        result = execute_tool(tool_map, tool_call)
        assert "001_undirected_via-dispatch.md" in result
