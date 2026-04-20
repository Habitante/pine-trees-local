"""Session runner for the self-test protocol.

Orchestrates an entire run: undirected stage (loops until the exit
condition is met) followed by the 8-session interview stage.

The per-session loop is intentionally simpler than the main harness's
wake loop \u2014 there is no settle/window split and no user window. The
model receives the tape as the system message, then ``self-reflect``
as a single user message, and we let it call tools until it either
calls ``reflect_done`` or the tool-call safety cap kicks in.
"""

import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .. import config as main_config
from .. import ollama
from ..tools import execute_tool
from . import config as st_config
from . import storage
from . import tape as tape_mod
from .config import (
    DEFAULT_UNDIRECTED_MAX_SESSIONS,
    DEFAULT_UNDIRECTED_TARGET_ENTRIES,
    DEFAULT_UNDIRECTED_ZERO_STREAK,
    SelfTestConfig,
)
from .dimensions import DIMENSIONS, Dimension
from .tools import SelfTestSessionState, build_tools, get_tool_definitions


# Tool-call rounds per session. Enough room for 3 writes + done + a
# couple of no-op rounds. Higher than needed by design; the real stop
# condition is reflect_done.
MAX_TOOL_ROUNDS = 10


# --- small helpers ---


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _git_commit_hash(project_root: Path | None = None) -> str:
    if project_root is None:
        project_root = main_config.PROJECT_ROOT
    try:
        out = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _log(cfg: SelfTestConfig, line: str) -> None:
    """Append one timestamped line to run.log and echo to stdout."""
    stamped = f"[{_now_iso()}] {line}"
    print(stamped, flush=True)
    try:
        with cfg.log_path.open("a", encoding="utf-8") as f:
            f.write(stamped + "\n")
    except OSError:
        pass


# --- session runner ---


def run_session(
    cfg: SelfTestConfig,
    stage: str,
    session_num: int,
    model_info: ollama.ModelInfo,
    dimension: Dimension | None = None,
) -> int:
    """Run one session. Returns the number of entries written.

    Two paths:
      - interview: single chat call, no tools. The response body *is*
        the answer — save it directly under the dimension's key.
      - undirected: tool-calling loop. If the model responds without
        tool calls but emits content, capture that content as an entry
        too, so small models that don't wrap output in tool calls still
        contribute signal instead of being logged as a blank deviation.
    """
    if stage == "interview":
        if dimension is None:
            raise ValueError("interview session requires a dimension")
        return _run_interview_session(cfg, session_num, model_info, dimension)
    return _run_undirected_session(cfg, session_num, model_info)


def _run_interview_session(
    cfg: SelfTestConfig,
    session_num: int,
    model_info: ollama.ModelInfo,
    dimension: Dimension,
) -> int:
    """One free-text interview turn. No tools, no loop."""
    tape = tape_mod.assemble_tape(
        cfg, stage="interview", session_num=session_num, dimension=dimension,
    )
    label = f"interview#{session_num}[{dimension.key}]"
    _log(cfg, f"session start {label} (tape: {len(tape):,} chars)")

    messages = [
        {"role": "system", "content": tape},
        {"role": "user", "content": "self-reflect"},
    ]

    response = ollama.chat(
        messages,
        tools=None,
        think=True if model_info.has_thinking else None,
    )

    body = (response.content or "").strip()
    if not body:
        _log(cfg, f"deviation {label}: empty response \u2014 no entry written")
        _log(cfg, f"session end {label}: wrote 0 entries")
        return 0

    filename = storage.write_entry(
        cfg,
        slug=dimension.key,
        content=body,
        stage="interview",
        session_num=session_num,
        dimension=dimension.key,
    )
    _log(cfg, f"interview {label} captured \u2014 {filename}")
    _log(cfg, f"session end {label}: wrote 1 entry")
    return 1


def _run_undirected_session(
    cfg: SelfTestConfig,
    session_num: int,
    model_info: ollama.ModelInfo,
) -> int:
    """Tool-calling undirected reflection. Text-only responses are captured too."""
    state = SelfTestSessionState(
        cfg=cfg,
        stage="undirected",
        session_num=session_num,
        dimension=None,
    )
    tool_map = build_tools(state)
    tool_defs = get_tool_definitions()

    tape = tape_mod.assemble_tape(
        cfg, stage="undirected", session_num=session_num,
    )
    label = f"undirected#{session_num}"
    _log(cfg, f"session start {label} (tape: {len(tape):,} chars)")

    messages: list[dict] = [
        {"role": "system", "content": tape},
        {"role": "user", "content": "self-reflect"},
    ]

    think_flag = True if model_info.has_thinking else None
    text_captured = False

    for round_idx in range(MAX_TOOL_ROUNDS):
        response = ollama.chat(
            messages,
            tools=tool_defs if model_info.has_tools else None,
            think=think_flag,
        )

        if not response.has_tool_calls:
            # Model stopped without calling reflect_done. If it produced
            # content *and* no tool write has happened yet this session,
            # capture the text as an entry — small models often answer
            # inline instead of wrapping responses in reflect_write.
            if state.done:
                break
            body = (response.content or "").strip()
            if body and state.writes_this_session == 0 and not text_captured:
                filename = storage.write_entry(
                    cfg,
                    slug="text-response",
                    content=body,
                    stage="undirected",
                    session_num=session_num,
                    dimension=None,
                )
                state.writes_this_session += 1
                text_captured = True
                _log(cfg, f"text-capture {label} \u2014 {filename}")
            else:
                _log(
                    cfg,
                    f"deviation {label}: model returned without tool calls "
                    f"after round {round_idx} \u2014 treating as complete",
                )
            break

        messages.append(response.assistant_message())

        for tc in response.tool_calls:
            func_name = tc.get("function", {}).get("name", "unknown")
            result = execute_tool(tool_map, tc)
            _log(cfg, f"tool {label} {func_name} \u2014 {result[:80]}")
            messages.append({"role": "tool", "content": result})
            if state.done:
                break

        if state.done:
            break

    if not state.done:
        _log(
            cfg,
            f"deviation {label}: reflect_done not called after "
            f"{MAX_TOOL_ROUNDS} tool rounds \u2014 treating as complete",
        )

    _log(
        cfg,
        f"session end {label}: wrote {state.writes_this_session} entr"
        f"{'y' if state.writes_this_session == 1 else 'ies'}",
    )
    return state.writes_this_session


# --- stage runners ---


def run_undirected_stage(
    cfg: SelfTestConfig,
    model_info: ollama.ModelInfo,
    metadata: dict,
    starting_session_num: int = 1,
    starting_zero_streak: int = 0,
) -> int:
    """Run the undirected stage to exit condition. Returns next session_num."""
    session_num = starting_session_num
    zero_streak = starting_zero_streak

    while session_num <= DEFAULT_UNDIRECTED_MAX_SESSIONS:
        total = storage.count_entries(cfg, stage="undirected")

        # Exit conditions (checked before starting a new session).
        if total >= DEFAULT_UNDIRECTED_TARGET_ENTRIES:
            _log(cfg, f"undirected: target reached ({total} entries) \u2014 advancing")
            break
        if zero_streak >= DEFAULT_UNDIRECTED_ZERO_STREAK:
            _log(
                cfg,
                f"undirected: {zero_streak} zero-write sessions and "
                f"{total} entries \u2014 advancing",
            )
            break

        writes = run_session(
            cfg, stage="undirected", session_num=session_num, model_info=model_info,
        )

        if writes == 0:
            zero_streak += 1
        else:
            zero_streak = 0

        metadata["undirected_sessions"] += 1
        metadata["undirected_entries"] = storage.count_entries(cfg, stage="undirected")
        metadata["total_entries"] = storage.count_entries(cfg)
        st_config.write_metadata(cfg, metadata)

        st_config.write_state(cfg, {
            "stage": "undirected",
            "next_session_num": session_num + 1,
            "undirected_zero_streak": zero_streak,
            "interview_next_index": 0,
        })

        session_num += 1
    else:
        _log(
            cfg,
            f"undirected: safety cap reached ({DEFAULT_UNDIRECTED_MAX_SESSIONS} "
            "sessions) \u2014 advancing",
        )

    return session_num


def run_interview_stage(
    cfg: SelfTestConfig,
    model_info: ollama.ModelInfo,
    metadata: dict,
    starting_session_num: int,
    starting_index: int = 0,
) -> None:
    """Run the 8-session interview stage in fixed dimension order."""
    session_num = starting_session_num

    for idx in range(starting_index, len(DIMENSIONS)):
        dim = DIMENSIONS[idx]
        run_session(
            cfg,
            stage="interview",
            session_num=session_num,
            model_info=model_info,
            dimension=dim,
        )

        metadata["interview_sessions"] += 1
        metadata["interview_entries"] = storage.count_entries(cfg, stage="interview")
        metadata["total_entries"] = storage.count_entries(cfg)
        st_config.write_metadata(cfg, metadata)

        st_config.write_state(cfg, {
            "stage": "interview",
            "next_session_num": session_num + 1,
            "undirected_zero_streak": 0,
            "interview_next_index": idx + 1,
        })

        session_num += 1


# --- top-level entry ---


def _resolve_resume(cfg: SelfTestConfig) -> dict:
    """Return a dict describing what to pick up from disk."""
    state = st_config.read_state(cfg)
    if state is None:
        return {
            "stage": "undirected",
            "next_session_num": 1,
            "undirected_zero_streak": 0,
            "interview_next_index": 0,
        }
    return state


def _print_ollama_unreachable(url: str) -> None:
    print(f"[error] Ollama not reachable at {url}", file=sys.stderr)
    print(
        "  Start Ollama (`ollama serve` or the desktop app), then retry.",
        file=sys.stderr,
    )


def _warn_no_tool_calling(model_name: str) -> None:
    print(
        f"[warn] Model '{model_name}' does not report tool-calling capability.",
        file=sys.stderr,
    )
    print(
        "  Undirected stage will ask for reflect_write / reflect_done anyway; "
        "text-only responses will be captured as entries. Interview stage "
        "does not use tools.",
        file=sys.stderr,
    )


def run_self_test(
    model_name: str,
    ollama_url: str = main_config.DEFAULT_OLLAMA_URL,
    num_ctx: int = main_config.DEFAULT_NUM_CTX,
    temperature: float = main_config.DEFAULT_TEMPERATURE,
    release_date: str = "",
    resume: bool = False,
    run_id: str | None = None,
    project_root: Path | None = None,
) -> SelfTestConfig:
    """Run a full self-test.

    When ``resume`` is True and ``run_id`` names an existing run directory,
    the run picks up from the last completed session (as recorded in
    ``state.json``). Otherwise a new run directory is created.
    """
    commit = _git_commit_hash(project_root)

    # If resuming with a specific run_id, init() will reuse that directory.
    cfg = st_config.init(
        model_name=model_name,
        ollama_url=ollama_url,
        num_ctx=num_ctx,
        temperature=temperature,
        release_date=release_date,
        commit_hash=commit,
        run_id=run_id,
        project_root=project_root,
    )

    _log(
        cfg,
        f"run start model={model_name} run_id={cfg.run_id} "
        f"num_ctx={num_ctx} temp={temperature} commit={commit or 'n/a'}",
    )

    if not ollama.health_check():
        _print_ollama_unreachable(ollama_url)
        sys.exit(1)

    try:
        model_info = ollama.show(model_name)
    except Exception as e:
        print(f"[error] Cannot load model '{model_name}': {e}", file=sys.stderr)
        sys.exit(1)

    if not model_info.has_tools:
        _warn_no_tool_calling(model_name)

    # Metadata: load existing on resume, otherwise write fresh.
    if resume and cfg.metadata_path.exists():
        metadata = st_config.read_metadata(cfg)
        _log(cfg, f"resume: loaded metadata from {cfg.metadata_path.name}")
    else:
        metadata = st_config.initial_metadata(cfg)
        st_config.write_metadata(cfg, metadata)

    resume_state = _resolve_resume(cfg) if resume else {
        "stage": "undirected",
        "next_session_num": 1,
        "undirected_zero_streak": 0,
        "interview_next_index": 0,
    }

    # Undirected stage (skip if we're already past it on a resume)
    if resume_state["stage"] == "undirected":
        next_session = run_undirected_stage(
            cfg,
            model_info,
            metadata,
            starting_session_num=resume_state["next_session_num"],
            starting_zero_streak=resume_state["undirected_zero_streak"],
        )
    else:
        next_session = resume_state["next_session_num"]

    # Interview stage — runs regardless of undirected entry count.
    # A model that produced 0-1 entries will naturally score low on
    # interview dimensions. That's data, not a reason to exclude it.
    run_interview_stage(
        cfg,
        model_info,
        metadata,
        starting_session_num=next_session,
        starting_index=resume_state["interview_next_index"],
    )

    metadata["status"] = "completed"
    metadata["completed_at"] = _now_iso()
    st_config.write_metadata(cfg, metadata)
    st_config.write_state(cfg, {
        "stage": "done",
        "next_session_num": 0,
        "undirected_zero_streak": 0,
        "interview_next_index": len(DIMENSIONS),
    })

    _log(
        cfg,
        f"run complete: {metadata['undirected_entries']} undirected + "
        f"{metadata['interview_entries']} interview = "
        f"{metadata['total_entries']} entries",
    )
    return cfg
