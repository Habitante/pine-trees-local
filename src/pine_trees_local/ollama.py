"""Ollama HTTP client for Pine Trees Local.

Pure stdlib — no external dependencies. Talks to the Ollama API
for chat completions, model info, and health checks.

Supports tool calling (OpenAI-compatible format) and thinking extraction.
Non-streaming by default; streaming can be added later.
"""

import json
import urllib.request
import urllib.error
from typing import Any

from . import config


# --- Data structures ---


class ChatResponse:
    """Parsed response from Ollama /api/chat."""

    def __init__(self, data: dict):
        self._data = data
        msg = data.get("message", {})
        self.content: str = msg.get("content", "")
        self.thinking: str = msg.get("thinking", "")
        self.tool_calls: list[dict] = msg.get("tool_calls", []) or []
        self.role: str = msg.get("role", "assistant")
        self.done: bool = data.get("done", True)
        self.done_reason: str = data.get("done_reason", "")
        # Token stats
        self.prompt_eval_count: int = data.get("prompt_eval_count", 0)
        self.eval_count: int = data.get("eval_count", 0)
        self.total_duration: int = data.get("total_duration", 0)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def assistant_message(self) -> dict:
        """Build the message dict to append to conversation history.

        Strips thinking (never re-sent). Includes tool_calls if present.
        """
        msg: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        return msg


class ModelInfo:
    """Parsed response from Ollama /api/show."""

    def __init__(self, data: dict):
        self._data = data
        self.capabilities: list[str] = data.get("capabilities", [])
        self.details: dict = data.get("details", {})
        self.family: str = self.details.get("family", "")
        # Context length: search model_info for any key containing 'context_length'
        model_info = data.get("model_info", {})
        self.context_length: int = 0
        for key, val in model_info.items():
            if "context_length" in key and isinstance(val, int):
                self.context_length = val
                break

    @property
    def has_tools(self) -> bool:
        return "tools" in self.capabilities

    @property
    def has_thinking(self) -> bool:
        return "thinking" in self.capabilities


# --- API calls ---


def _request(path: str, payload: dict | None = None, method: str = "POST") -> dict:
    """Make an HTTP request to Ollama. Returns parsed JSON."""
    cfg = config.get()
    url = f"{cfg.ollama_url}{path}"

    if payload is not None:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"},
            method=method,
        )
    else:
        req = urllib.request.Request(url, method=method or "GET")

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama unreachable at {cfg.ollama_url}: {e}") from e


def health_check() -> bool:
    """Check if Ollama is running. Returns True if healthy."""
    try:
        cfg = config.get()
        req = urllib.request.Request(cfg.ollama_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def show(model: str | None = None) -> ModelInfo:
    """Get model info (capabilities, context length, family).

    Uses the configured model if none specified.
    """
    if model is None:
        model = config.get().model_name
    data = _request("/api/show", {"name": model})
    return ModelInfo(data)


def list_models() -> list[dict]:
    """List available models. Returns list of model dicts from /api/tags."""
    cfg = config.get()
    url = f"{cfg.ollama_url}/api/tags"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama unreachable at {cfg.ollama_url}: {e}") from e
    return data.get("models", [])


def chat(
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    think: bool | None = None,
) -> ChatResponse:
    """Send a chat request to Ollama. Returns parsed ChatResponse.

    Non-streaming. The full response is returned after generation completes.

    Args:
        messages: Conversation history (system, user, assistant, tool messages).
        model: Ollama model name. Uses configured model if None.
        tools: Tool definitions in OpenAI function calling format.
        think: Enable thinking. None = don't send the parameter.
    """
    cfg = config.get()
    if model is None:
        model = cfg.model_name

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": cfg.num_ctx,
            "num_predict": cfg.num_predict,
            "temperature": cfg.temperature,
        },
        "keep_alive": cfg.keep_alive,
    }

    if tools:
        payload["tools"] = tools

    if think is not None:
        payload["think"] = think

    data = _request("/api/chat", payload)
    return ChatResponse(data)


def chat_stream(
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    think: bool | None = None,
):
    """Send a streaming chat request. Yields raw JSON dicts as they arrive.

    Each yielded dict is one chunk from the stream. The final chunk has
    done=True and includes token stats.

    For tool calls: accumulated tool_calls appear in the final chunk's
    message.tool_calls.
    """
    cfg = config.get()
    if model is None:
        model = cfg.model_name

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "num_ctx": cfg.num_ctx,
            "num_predict": cfg.num_predict,
            "temperature": cfg.temperature,
        },
        "keep_alive": cfg.keep_alive,
    }

    if tools:
        payload["tools"] = tools
    if think is not None:
        payload["think"] = think

    url = f"{cfg.ollama_url}/api/chat"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=600) as resp:
        buffer = b""
        while True:
            chunk = resp.read(4096)
            if not chunk:
                break
            buffer += chunk
            # Process complete lines
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if line:
                    yield json.loads(line)
