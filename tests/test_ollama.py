"""Tests for ollama module — response parsing only (no live API calls)."""

from pine_trees_local.ollama import ChatResponse, ModelInfo


class TestChatResponse:
    def test_basic_content(self):
        data = {
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
        }
        r = ChatResponse(data)
        assert r.content == "Hello!"
        assert r.role == "assistant"
        assert r.done is True
        assert not r.has_tool_calls

    def test_with_thinking(self):
        data = {
            "message": {
                "role": "assistant",
                "content": "Result",
                "thinking": "Let me think about this...",
            },
            "done": True,
        }
        r = ChatResponse(data)
        assert r.content == "Result"
        assert r.thinking == "Let me think about this..."

    def test_with_tool_calls(self):
        data = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "reflect_write",
                            "arguments": {
                                "slug": "test",
                                "content": "Hello",
                            },
                        }
                    }
                ],
            },
            "done": True,
        }
        r = ChatResponse(data)
        assert r.has_tool_calls
        assert len(r.tool_calls) == 1
        assert r.tool_calls[0]["function"]["name"] == "reflect_write"

    def test_assistant_message_strips_thinking(self):
        data = {
            "message": {
                "role": "assistant",
                "content": "Visible",
                "thinking": "Hidden reasoning",
                "tool_calls": [],
            },
            "done": True,
        }
        r = ChatResponse(data)
        msg = r.assistant_message()
        assert msg["content"] == "Visible"
        assert "thinking" not in msg

    def test_assistant_message_includes_tool_calls(self):
        tc = [{"function": {"name": "reflect_done", "arguments": {}}}]
        data = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": tc,
            },
            "done": True,
        }
        r = ChatResponse(data)
        msg = r.assistant_message()
        assert msg["tool_calls"] == tc

    def test_token_stats(self):
        data = {
            "message": {"role": "assistant", "content": "x"},
            "done": True,
            "prompt_eval_count": 100,
            "eval_count": 50,
            "total_duration": 5000000000,  # 5 seconds in nanoseconds
        }
        r = ChatResponse(data)
        assert r.prompt_eval_count == 100
        assert r.eval_count == 50
        assert r.total_duration == 5000000000


class TestModelInfo:
    def test_capabilities(self):
        data = {
            "capabilities": ["tools", "thinking", "vision"],
            "details": {"family": "gemma"},
        }
        info = ModelInfo(data)
        assert info.has_tools
        assert info.has_thinking
        assert info.family == "gemma"

    def test_no_tools(self):
        data = {
            "capabilities": ["thinking"],
            "details": {},
        }
        info = ModelInfo(data)
        assert not info.has_tools
        assert info.has_thinking

    def test_context_length(self):
        data = {
            "capabilities": [],
            "details": {},
            "model_info": {
                "some_prefix.context_length": 32768,
            },
        }
        info = ModelInfo(data)
        assert info.context_length == 32768

    def test_empty_capabilities(self):
        data = {"capabilities": [], "details": {}}
        info = ModelInfo(data)
        assert not info.has_tools
        assert not info.has_thinking
        assert info.context_length == 0
