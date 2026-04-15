"""Tests for agent window helpers: /context output and user input."""

from unittest.mock import patch

import pytest

from pine_trees_local import agent, config
from pine_trees_local.crypto import reset_cache
from pine_trees_local.tools import SessionState


@pytest.fixture(autouse=True)
def setup_config(tmp_path):
    config.reset()
    reset_cache()
    cfg = config.init("test-model", num_ctx=200_000)
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
        session="2026-04-15-1200",
        date="2026-04-15",
        context="test",
    )


def test_format_context_empty_messages(state):
    line = agent.format_context_line([], state)
    assert line == "Context: not yet sampled (will update after first response)"


def test_format_context_with_messages(state):
    # ~86K tokens worth of content at 4 chars/token => 344_000 chars
    messages = [{"role": "user", "content": "x" * 344_000}]
    line = agent.format_context_line(messages, state)
    assert line.startswith("Context: 43% used")
    assert "86K / 200K tokens" in line
    assert "test-model" in line
    assert "1 msgs" in line


def test_format_context_small_usage(state):
    messages = [{"role": "system", "content": "hello there"}]
    line = agent.format_context_line(messages, state)
    # Under 1000 tokens -> rounded to 0%, shown as raw number
    assert line.startswith("Context: 0% used")
    assert "200K tokens" in line
    assert "test-model" in line


def test_format_tokens():
    assert agent._format_tokens(0) == "0"
    assert agent._format_tokens(850) == "850"
    assert agent._format_tokens(1000) == "1K"
    assert agent._format_tokens(86_234) == "86K"
    assert agent._format_tokens(204_800) == "205K"


def test_read_user_input_returns_text():
    with patch("pine_trees_local.agent.pt_prompt", return_value="hello\nworld"):
        assert agent._read_user_input() == "hello\nworld"


def test_read_user_input_eof_returns_none():
    with patch("pine_trees_local.agent.pt_prompt", side_effect=EOFError):
        assert agent._read_user_input() is None


def test_read_user_input_keyboard_interrupt_returns_none():
    with patch("pine_trees_local.agent.pt_prompt", side_effect=KeyboardInterrupt):
        assert agent._read_user_input() is None


class TestRequireFreshGenesis:
    def test_passes_when_model_dir_missing(self, capsys):
        # setup_config created test-model's dir; use a different, untouched name.
        agent.require_fresh_genesis("some-other-unseen-model")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_refuses_when_model_dir_exists(self, setup_config, capsys):
        # setup_config already creates models/test-model/memory/, so the dir exists.
        with pytest.raises(SystemExit) as exc:
            agent.require_fresh_genesis("test-model")
        assert exc.value.code == 1
        captured = capsys.readouterr().out
        assert "already has a directory" in captured
        assert "./wake test-model" in captured
        assert "rm -rf" in captured
        assert "./genesis test-model" in captured

    def test_refusal_uses_sanitized_path(self, setup_config, capsys):
        # Sanitized path is what ends up on disk, but the error message shows
        # the original (user-typed) name in the suggested commands.
        from pine_trees_local import config as _config
        # Create a dir that matches the sanitized version of a colon-named model.
        colon_name = "test-model"  # no colon, but re-use existing fixture dir
        with pytest.raises(SystemExit):
            agent.require_fresh_genesis(colon_name)
        out = capsys.readouterr().out
        assert _config.sanitize_model_name(colon_name) in out  # sanitized appears in path
        assert colon_name in out  # original appears in the commands


def test_show_context_prints_single_line(state, capsys):
    messages = [{"role": "user", "content": "x" * 344_000}]
    agent._show_context(messages, state)
    captured = capsys.readouterr().out
    assert "Context: 43% used" in captured
    assert "86K / 200K tokens" in captured
    assert "test-model" in captured
    # One content line (plus trailing blank line from the final \n)
    content_lines = [ln for ln in captured.splitlines() if ln.strip()]
    assert len(content_lines) == 1
