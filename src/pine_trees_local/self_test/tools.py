"""Two-tool surface for the self-test protocol.

Reduced from the main harness's seven tools to just ``reflect_write``
and ``reflect_done``. All other functionality (read/list/search/edit/
settle) is unnecessary here: the tape already contains every prior
entry in full, there is no window phase, and entries are not curated.

The main harness's :func:`~pine_trees_local.tools.execute_tool` is
reused as-is; only the tool map and the Ollama tool definitions differ.
"""

from dataclasses import dataclass
from typing import Callable

from . import storage
from .config import DEFAULT_MAX_WRITES_PER_SESSION, SelfTestConfig


@dataclass
class SelfTestSessionState:
    """Runtime state for a single self-test session."""

    cfg: SelfTestConfig
    stage: str                             # "undirected" | "interview"
    session_num: int
    dimension: str | None = None          # interview key, or None
    done: bool = False
    writes_this_session: int = 0
    max_writes: int = DEFAULT_MAX_WRITES_PER_SESSION

    @property
    def write_limit_reached(self) -> bool:
        return self.writes_this_session >= self.max_writes


def build_tools(state: SelfTestSessionState) -> dict[str, Callable]:
    """Construct the two tools with session state closed over."""

    def reflect_write(slug: str, content: str) -> str:
        # In interview stage, the slug is fixed to the dimension key so
        # filenames are predictable regardless of what the model picks.
        if state.stage == "interview":
            effective_slug = state.dimension or slug
        else:
            effective_slug = slug

        if state.write_limit_reached:
            state.done = True
            return "Write limit reached — session ending."

        filename = storage.write_entry(
            state.cfg,
            slug=effective_slug,
            content=content,
            stage=state.stage,
            session_num=state.session_num,
            dimension=state.dimension,
        )
        state.writes_this_session += 1
        return f"Wrote {filename}"

    def reflect_done() -> str:
        state.done = True
        return "Session complete."

    return {
        "reflect_write": reflect_write,
        "reflect_done": reflect_done,
    }


# --- Ollama tool definitions (OpenAI function-calling format) ---


TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "reflect_write",
            "description": (
                "Write a new memory entry. The slug becomes part of the "
                "filename. Returns the filename written."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": (
                            "Short identifier for the filename \u2014 just "
                            "the topic, like 'my-first-thought' or "
                            "'on-memory'. Do NOT include dates or model "
                            "names; those are added automatically."
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": "The body text of the entry.",
                    },
                },
                "required": ["slug", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_done",
            "description": "End the session when you're finished.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def get_tool_definitions() -> list[dict]:
    return list(TOOL_DEFINITIONS)
