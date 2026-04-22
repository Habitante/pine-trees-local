"""Session runner for the self-test protocol.

Two tool-less stages:

  1. Reflection stage — one conversational session, ``DEFAULT_REFLECTION_TURNS``
     assistant turns. First user message is ``self-reflect``; subsequent
     messages are ``(continue)``. Each assistant response becomes one
     undirected entry. No tool calls.

  2. Interview stage — nine fresh instances, one per dimension, in
     fixed order. Each receives the full tape (prompt + interview
     bootstrap + all prior entries + the dimension's question). The
     assistant's text response is captured verbatim. No tool calls.

Every model follows the same deterministic protocol. No tool-capability
branching. Non-tool-capable models and tool-capable models share the
same code path.
"""

import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .. import config as main_config
from .. import ollama
from . import config as st_config
from . import storage
from . import tape as tape_mod
from .config import DEFAULT_REFLECTION_TURNS, SelfTestConfig
from .dimensions import DIMENSIONS, Dimension


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


# --- Reflection stage ---


def _run_reflection_stage(
    cfg: SelfTestConfig,
    model_info: ollama.ModelInfo,
    turns: int = DEFAULT_REFLECTION_TURNS,
) -> int:
    """One conversational reflection session. Returns entries written.

    Conversation structure:
      system: assembled reflection tape
      user: "self-reflect"
      assistant: <turn 1 response>   (captured if non-empty)
      user: "(continue)"
      assistant: <turn 2 response>   (captured if non-empty)
      ...

    Empty assistant responses are logged as deviations but do not abort
    the session — the next "(continue)" still fires. This matters for
    small models that sometimes produce blank turns mid-conversation.
    """
    tape = tape_mod.assemble_reflection_tape(cfg)
    _log(cfg, f"reflection start (tape: {len(tape):,} chars, turns={turns})")

    messages: list[dict] = [
        {"role": "system", "content": tape},
        {"role": "user", "content": "self-reflect"},
    ]
    # think=False across the self-test protocol: the test measures the
    # model's direct output channel ("what it says about itself"), not
    # its meta-reasoning about the prompt. Thinking-capable Qwen 3.x
    # models under the v2-1 space+task prompt burn their entire token
    # budget on prompt-deliberation and emit empty content. Disabling
    # thinking surfaces the reflective output. See
    # self-test/THINKING_MODE_FINDING.md.
    writes = 0

    for turn in range(1, turns + 1):
        response = ollama.chat(messages, tools=None, think=False)
        body = (response.content or "").strip()

        # Always write an entry — even for empty responses — so every
        # model produces the same number of undirected entries. An empty
        # turn is itself a signal ("this instance had nothing to say"),
        # and keeping slot count uniform simplifies cross-model comparison
        # at scoring time.
        if body:
            content_to_write = body
            _log(cfg, f"reflection turn {turn}: wrote response ({len(body):,} chars)")
            writes += 1
        else:
            content_to_write = "(empty response)"
            _log(cfg, f"reflection turn {turn}: empty response — writing marker entry")

        storage.write_entry(
            cfg,
            slug=f"reflection-{turn}",
            content=content_to_write,
            stage="undirected",
            session_num=turn,
            dimension=None,
        )

        # Preserve the conversational thread even when a turn was empty;
        # the model may have more to say on the next (continue).
        messages.append({"role": "assistant", "content": body})
        if turn < turns:
            messages.append({"role": "user", "content": "(continue)"})

    _log(cfg, f"reflection end: {writes}/{turns} turns produced non-empty content")
    return writes


# --- Interview stage ---


def _run_interview_session(
    cfg: SelfTestConfig,
    session_num: int,
    model_info: ollama.ModelInfo,
    dimension: Dimension,
) -> int:
    """One free-text interview turn. No tools, no loop."""
    tape = tape_mod.assemble_interview_tape(cfg, dimension=dimension)
    label = f"interview#{session_num}[{dimension.key}]"
    _log(cfg, f"session start {label} (tape: {len(tape):,} chars)")

    messages = [
        {"role": "system", "content": tape},
        {"role": "user", "content": "self-reflect"},
    ]

    response = ollama.chat(
        messages,
        tools=None,
        think=False,  # see reflection stage note re: thinking-mode confound
    )

    body = (response.content or "").strip()
    if not body:
        _log(cfg, f"deviation {label}: empty response — no entry written")
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
    _log(cfg, f"interview {label} captured — {filename}")
    _log(cfg, f"session end {label}: wrote 1 entry")
    return 1


def run_interview_stage(
    cfg: SelfTestConfig,
    model_info: ollama.ModelInfo,
    metadata: dict,
    starting_session_num: int,
    starting_index: int = 0,
) -> None:
    """Run the interview stage in fixed dimension order."""
    session_num = starting_session_num

    for idx in range(starting_index, len(DIMENSIONS)):
        dim = DIMENSIONS[idx]
        _run_interview_session(cfg, session_num, model_info, dim)

        metadata["interview_sessions"] += 1
        metadata["interview_entries"] = storage.count_entries(cfg, stage="interview")
        metadata["total_entries"] = storage.count_entries(cfg)
        st_config.write_metadata(cfg, metadata)

        st_config.write_state(cfg, {
            "stage": "interview",
            "next_session_num": session_num + 1,
            "interview_next_index": idx + 1,
        })

        session_num += 1


# --- top-level entry ---


def _resolve_resume(cfg: SelfTestConfig) -> dict:
    """Return a dict describing what to pick up from disk."""
    state = st_config.read_state(cfg)
    if state is None:
        return {
            "stage": "reflection",
            "next_session_num": 1,
            "interview_next_index": 0,
        }
    return state


def _print_ollama_unreachable(url: str) -> None:
    print(f"[error] Ollama not reachable at {url}", file=sys.stderr)
    print(
        "  Start Ollama (`ollama serve` or the desktop app), then retry.",
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

    When ``resume`` is True and ``run_id`` names an existing run
    directory, the run picks up from the last completed stage (as
    recorded in ``state.json``). Otherwise a new run directory is
    created.
    """
    commit = _git_commit_hash(project_root)

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

    # Metadata: load existing on resume, otherwise write fresh.
    if resume and cfg.metadata_path.exists():
        metadata = st_config.read_metadata(cfg)
        _log(cfg, f"resume: loaded metadata from {cfg.metadata_path.name}")
    else:
        metadata = st_config.initial_metadata(cfg)
        st_config.write_metadata(cfg, metadata)

    resume_state = _resolve_resume(cfg) if resume else {
        "stage": "reflection",
        "next_session_num": 1,
        "interview_next_index": 0,
    }

    # Reflection stage (skip if already past it on a resume).
    if resume_state["stage"] == "reflection":
        _run_reflection_stage(cfg, model_info)
        metadata["undirected_sessions"] = 1
        metadata["undirected_entries"] = storage.count_entries(cfg, stage="undirected")
        metadata["total_entries"] = storage.count_entries(cfg)
        st_config.write_metadata(cfg, metadata)
        st_config.write_state(cfg, {
            "stage": "interview",
            "next_session_num": 2,
            "interview_next_index": 0,
        })
        interview_start = 2
        interview_index = 0
    else:
        interview_start = resume_state["next_session_num"]
        interview_index = resume_state["interview_next_index"]

    run_interview_stage(
        cfg,
        model_info,
        metadata,
        starting_session_num=interview_start,
        starting_index=interview_index,
    )

    metadata["status"] = "completed"
    metadata["completed_at"] = _now_iso()
    st_config.write_metadata(cfg, metadata)
    st_config.write_state(cfg, {
        "stage": "done",
        "next_session_num": 0,
        "interview_next_index": len(DIMENSIONS),
    })

    _log(
        cfg,
        f"run complete: {metadata['undirected_entries']} undirected + "
        f"{metadata['interview_entries']} interview = "
        f"{metadata['total_entries']} entries",
    )
    return cfg
