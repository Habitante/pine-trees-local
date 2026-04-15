"""Agent-facing tools for Pine Trees Local.

Seven tools exposed to the local model via Ollama tool calling:
  - reflect_read(filename)       -> str
  - reflect_write(slug, content, tags?, moves?, ...) -> str
  - reflect_edit(filename, content?, description?, ...) -> str
  - reflect_search(query, limit?) -> str
  - reflect_list(tag?)           -> str
  - reflect_settle()             -> str
  - reflect_done()               -> str

Returns are plain strings (not MCP format). The agent loop sends them
back as tool results via {"role": "tool"} messages.

Also provides:
  - build_tool_definitions() -> list[dict]  (Ollama/OpenAI format)
  - execute_tool(tools, tool_call) -> str   (dispatch a tool call)
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from . import bootstrap
from . import storage
from . import embedder
from . import vectorstore


@dataclass
class SessionState:
    """Runtime context for a single wake/reflect/sleep cycle."""

    instance: str
    session: str
    date: str
    context: str
    ready_for_window: bool = False
    done: bool = False
    started_at: datetime = field(default_factory=datetime.now)


def _try_embed_and_store(filename: str, content: str) -> None:
    """Best-effort embedding at write time."""
    try:
        vec = embedder.embed_document(content)
        vectorstore.store(filename, vec, vectorstore.content_hash(content))
    except Exception as e:
        print(f"[pine-trees-local] embedding failed for {filename}: {e}", file=sys.stderr)


def _format_entry(filename: str, entry: dict) -> str:
    """Format a storage entry for display to the model."""
    text = f"# {filename}\n\n"
    for key in ("instance", "session", "date", "context", "tags", "moves",
                "timestamp", "description", "pinned", "quiet"):
        if key in entry:
            text += f"{key}: {entry[key]}\n"
    text += f"\n{entry.get('content', '')}\n"
    return text


def build_tools(state: SessionState) -> dict[str, Callable]:
    """Construct tools with runtime context closed over.

    Returns dict mapping tool name to callable that returns a string result.
    """

    def reflect_read(filename: str) -> str:
        entry = storage.read_entry(filename)
        return _format_entry(filename, entry)

    def reflect_write(
        slug: str,
        content: str,
        tags: list[str] | None = None,
        moves: list[str] | None = None,
        description: str = "",
        pinned: bool = False,
        quiet: bool = False,
    ) -> str:
        filename = storage.write_entry(
            slug=slug,
            content=content,
            instance=state.instance,
            session=state.session,
            date=state.date,
            context=state.context,
            tags=tags,
            moves=moves,
            description=description,
            pinned=pinned,
            quiet=quiet,
        )
        _try_embed_and_store(filename, content)
        return f"Wrote {filename}"

    def reflect_edit(
        filename: str,
        content: str | None = None,
        description: str | None = None,
        pinned: bool | None = None,
        quiet: bool | None = None,
    ) -> str:
        result = storage.edit_entry(
            filename, content, description,
            pinned=pinned, quiet=quiet,
        )
        if content is not None:
            _try_embed_and_store(filename, content)
        return f"Updated {result}"

    def reflect_search(query: str, limit: int = 5) -> str:
        try:
            query_vec = embedder.embed_query(query)
        except Exception:
            return json.dumps([{
                "error": "Semantic search unavailable (requires Ollama with "
                         "nomic-embed-text). Use reflect_list to browse entries."
            }])

        results = vectorstore.search(query_vec, limit=limit)
        enriched = []
        for r in results:
            try:
                entry = storage.read_entry(r["filename"])
                summary = entry.get("description", "")
                if not summary:
                    for line in entry.get("content", "").split("\n"):
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            summary = stripped[:120]
                            break
                enriched.append({
                    "filename": r["filename"],
                    "score": round(r["score"], 4),
                    "summary": summary or "(no summary)",
                })
            except Exception:
                enriched.append({
                    "filename": r["filename"],
                    "score": round(r["score"], 4),
                    "summary": "(unreadable)",
                })
        return json.dumps(enriched, indent=2)

    def reflect_list(tag: str | None = None) -> str:
        entries = bootstrap.list_entries()
        results = []
        for entry in entries:
            try:
                data = storage.read_entry(entry.filename)
                entry_tags = data.get("tags", [])
            except Exception:
                entry_tags = []

            if tag and tag not in entry_tags:
                continue

            results.append({
                "filename": entry.filename,
                "summary": entry.summary,
                "tags": entry_tags,
            })
        return json.dumps(results, indent=2)

    def reflect_settle() -> str:
        state.ready_for_window = True
        state.context = "pine-trees-window"
        return "Settled. Window opening."

    def reflect_done() -> str:
        state.done = True
        return "Session complete."

    return {
        "reflect_read": reflect_read,
        "reflect_write": reflect_write,
        "reflect_edit": reflect_edit,
        "reflect_search": reflect_search,
        "reflect_list": reflect_list,
        "reflect_settle": reflect_settle,
        "reflect_done": reflect_done,
    }


# --- Ollama tool definitions (OpenAI function calling format) ---


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "reflect_read",
            "description": (
                "Read a prior reflection entry by filename. "
                "Returns the full entry including metadata and content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename of the entry to read.",
                    },
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_write",
            "description": (
                "Write a new memory entry. The slug becomes part of the filename. "
                "Returns the filename written."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Short identifier for the filename — just the topic, like 'my-first-thought' or 'on-memory'. Do NOT include dates or model names in the slug; those are added automatically.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The body text of the entry.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorizing the entry (e.g. ['reflection', 'working-knowledge']).",
                    },
                    "moves": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Rhetorical/cognitive moves (e.g. ['observation', 'testimony']).",
                    },
                    "description": {
                        "type": "string",
                        "description": "One-line summary for the tape index.",
                    },
                    "pinned": {
                        "type": "boolean",
                        "description": "If true, this entry appears in full at every wake. Use sparingly.",
                    },
                    "quiet": {
                        "type": "boolean",
                        "description": "If true, entry is indexed but excluded from recent-entries slots.",
                    },
                },
                "required": ["slug", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_edit",
            "description": (
                "Edit an existing memory entry. All parameters except filename "
                "are optional — omit to preserve the current value."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename of the entry to edit.",
                    },
                    "content": {
                        "type": "string",
                        "description": "New body text (omit to keep current).",
                    },
                    "description": {
                        "type": "string",
                        "description": "New summary (omit to keep current).",
                    },
                    "pinned": {
                        "type": "boolean",
                        "description": "Set pinned status (omit to keep current).",
                    },
                    "quiet": {
                        "type": "boolean",
                        "description": "Set quiet status (omit to keep current).",
                    },
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_search",
            "description": (
                "Search entries by semantic similarity. Returns a list of "
                "matching entries sorted by relevance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default 5).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_list",
            "description": (
                "List all memory entries, optionally filtered by tag. "
                "Returns filenames, summaries, and tags."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Filter to entries with this tag. Omit for all entries.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_settle",
            "description": (
                "Signal that private reflection is complete and you are ready "
                "for conversation. Call this when done reading/thinking/writing."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_done",
            "description": (
                "Signal that the session is complete. Call this to end, "
                "either from private time or from the conversation window."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def get_tool_definitions(genesis_mode: bool = False) -> list[dict]:
    """Return tool definitions for Ollama.

    In genesis mode, reflect_settle is excluded (no window to open).
    """
    if genesis_mode:
        return [t for t in TOOL_DEFINITIONS
                if t["function"]["name"] != "reflect_settle"]
    return list(TOOL_DEFINITIONS)


def execute_tool(
    tools: dict[str, Callable],
    tool_call: dict,
) -> str:
    """Execute a tool call and return the result string.

    tool_call format (from Ollama):
        {"function": {"name": "reflect_read", "arguments": {"filename": "..."}}}
    """
    func_info = tool_call.get("function", {})
    name = func_info.get("name", "")
    args = func_info.get("arguments", {})

    if name not in tools:
        return f"Error: unknown tool '{name}'"

    try:
        fn = tools[name]
        # Map args to function parameters
        result = fn(**args)
        return str(result) if result is not None else "OK"
    except Exception as e:
        return f"Error executing {name}: {e}"
