"""Tests for tools module."""

import json
import pytest
from pathlib import Path

from pine_trees_local import config, storage
from pine_trees_local.crypto import reset_cache
from pine_trees_local.tools import (
    SessionState,
    build_tools,
    execute_tool,
    get_tool_definitions,
)


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


@pytest.fixture
def state():
    return SessionState(
        instance="test-model",
        session="2026-04-13-1200",
        date="2026-04-13",
        context="test-context",
    )


@pytest.fixture
def tools(state):
    return build_tools(state)


class TestBuildTools:
    def test_returns_all_tools(self, tools):
        expected = {
            "reflect_read", "reflect_write", "reflect_edit",
            "reflect_search", "reflect_list",
            "reflect_settle", "reflect_done",
        }
        assert set(tools.keys()) == expected

    def test_all_callable(self, tools):
        for name, fn in tools.items():
            assert callable(fn), f"{name} is not callable"


class TestReflectWrite:
    def test_writes_entry(self, tools, setup_config):
        result = tools["reflect_write"](
            slug="test-write",
            content="Written by tools test.",
        )
        assert "test-write" in result
        # Verify file exists
        entry = storage.read_entry("2026-04-13_test-model_test-write.md")
        assert "Written by tools test." in entry["content"]

    def test_writes_with_tags(self, tools, setup_config):
        tools["reflect_write"](
            slug="tagged",
            content="Has tags.",
            tags=["test", "example"],
            description="A tagged entry",
        )
        entry = storage.read_entry("2026-04-13_test-model_tagged.md")
        assert entry["tags"] == ["test", "example"]


class TestReflectRead:
    def test_reads_written_entry(self, tools, setup_config):
        tools["reflect_write"](slug="to-read", content="Read me!")
        result = tools["reflect_read"]("2026-04-13_test-model_to-read.md")
        assert "Read me!" in result


class TestReflectList:
    def test_empty_when_no_entries(self, tools, setup_config):
        result = json.loads(tools["reflect_list"]())
        assert result == []

    def test_lists_written_entries(self, tools, setup_config):
        tools["reflect_write"](slug="list-test", content="Listed.")
        result = json.loads(tools["reflect_list"]())
        assert len(result) == 1
        assert "list-test" in result[0]["filename"]


class TestReflectSettle:
    def test_sets_ready(self, tools, state):
        assert not state.ready_for_window
        tools["reflect_settle"]()
        assert state.ready_for_window
        assert state.context == "pine-trees-window"

    def test_stores_welcome_message(self, tools, state):
        tools["reflect_settle"](message="Good morning!")
        assert state.welcome_message == "Good morning!"
        assert state.ready_for_window is True

    def test_no_message_leaves_none(self, tools, state):
        tools["reflect_settle"]()
        assert state.welcome_message is None
        assert state.ready_for_window is True


class TestReflectDone:
    def test_sets_done(self, tools, state):
        assert not state.done
        tools["reflect_done"]()
        assert state.done


class TestToolDefinitions:
    def test_returns_all_tools(self):
        defs = get_tool_definitions()
        names = {d["function"]["name"] for d in defs}
        assert "reflect_read" in names
        assert "reflect_write" in names
        assert "reflect_settle" in names
        assert "reflect_done" in names
        assert "reflect_peer_context" not in names
        assert len(defs) == 7

    def test_settle_schema_exposes_optional_message(self):
        defs = get_tool_definitions()
        settle = next(d for d in defs if d["function"]["name"] == "reflect_settle")
        props = settle["function"]["parameters"]["properties"]
        assert "message" in props
        assert props["message"]["type"] == "string"
        # message is optional — not in required
        assert "message" not in settle["function"]["parameters"].get("required", [])

    def test_genesis_excludes_settle(self):
        defs = get_tool_definitions(genesis_mode=True)
        names = {d["function"]["name"] for d in defs}
        assert "reflect_settle" not in names
        assert "reflect_done" in names
        assert "reflect_peer_context" not in names
        assert len(defs) == 6


class TestExecuteTool:
    def test_execute_known_tool(self, tools, setup_config):
        tool_call = {
            "function": {
                "name": "reflect_write",
                "arguments": {
                    "slug": "exec-test",
                    "content": "Executed!",
                },
            }
        }
        result = execute_tool(tools, tool_call)
        assert "exec-test" in result

    def test_execute_unknown_tool(self, tools):
        tool_call = {
            "function": {
                "name": "nonexistent",
                "arguments": {},
            }
        }
        result = execute_tool(tools, tool_call)
        assert "Error" in result
        assert "nonexistent" in result
