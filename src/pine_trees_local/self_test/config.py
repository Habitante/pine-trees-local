"""Per-run configuration for the self-test protocol.

A self-test run is isolated from the main harness data — it lives under
``self-test-runs/<model_safe>/<run_id>/`` at the project root. Entries
are plaintext (no encryption) because the self-test corpus is intended
for analysis and sharing, not private reflection.

This module wraps the main ``config.init()`` so that ``ollama.py`` works:
the Ollama client reads model_name, num_ctx, temperature, etc. from the
shared singleton. We just add a ``SelfTestConfig`` on top that knows
where this run's entries and metadata live.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .. import config as main_config


PROTOCOL_VERSION = "1.0"

# Number of assistant turns captured as undirected entries in the
# reflection stage. One conversational session; turn 1 is driven by
# the "self-reflect" user message, turns 2..N by "(continue)".
DEFAULT_REFLECTION_TURNS = 3

# Legacy constant retained for self_test/tools.py, which is no longer
# imported by the runner (tool-less protocol) but still exists so its
# unit tests continue to exercise the tool-call code path if the module
# is ever revived. Not referenced by the active runtime.
DEFAULT_MAX_WRITES_PER_SESSION = 3


def self_test_root(project_root: Path | None = None) -> Path:
    """Return the root directory for all self-test runs."""
    if project_root is None:
        project_root = main_config.PROJECT_ROOT
    return project_root / "self-test-runs"


def _new_run_id(now: datetime | None = None) -> str:
    """Generate a sortable, human-readable run ID from the current time.

    Seconds-level granularity — minute-level was too coarse for fast
    models (1-3B completing in <30s), which produced clock collisions
    when ``--runs N`` invoked back-to-back sessions within the same
    minute. The first run's directory was silently overwritten by the
    second via ``mkdir(exist_ok=True)``. Seconds-level granularity
    keeps every run distinct even for the fastest cohort members.
    """
    if now is None:
        now = datetime.now()
    return now.strftime("%Y-%m-%d-%H%M%S")


@dataclass(frozen=True)
class SelfTestConfig:
    """Resolved configuration for a single self-test run."""

    model_name: str
    model_safe_name: str
    temperature: float
    num_ctx: int
    release_date: str
    commit_hash: str

    run_id: str
    run_dir: Path
    entries_dir: Path
    metadata_path: Path
    state_path: Path
    log_path: Path

    started_at: str  # ISO-8601 UTC


def init(
    model_name: str,
    ollama_url: str = main_config.DEFAULT_OLLAMA_URL,
    num_ctx: int = main_config.DEFAULT_NUM_CTX,
    temperature: float = main_config.DEFAULT_TEMPERATURE,
    release_date: str = "",
    commit_hash: str = "",
    run_id: str | None = None,
    project_root: Path | None = None,
    now: datetime | None = None,
) -> SelfTestConfig:
    """Initialize a self-test run. Creates the run directory tree.

    Also initializes the main harness config singleton so that ``ollama.py``
    can find ollama_url / num_ctx / temperature. The main config's
    model_dir is unused — self-test does not touch ``models/``.
    """
    main_config.init(
        model_name,
        ollama_url=ollama_url,
        num_ctx=num_ctx,
        temperature=temperature,
    )

    safe = main_config.sanitize_model_name(model_name)

    if now is None:
        now = datetime.now()
    if run_id is None:
        run_id = _new_run_id(now)

    root = self_test_root(project_root)
    run_dir = root / safe / run_id
    entries_dir = run_dir / "entries"

    run_dir.mkdir(parents=True, exist_ok=True)
    entries_dir.mkdir(parents=True, exist_ok=True)

    cfg = SelfTestConfig(
        model_name=model_name,
        model_safe_name=safe,
        temperature=temperature,
        num_ctx=num_ctx,
        release_date=release_date,
        commit_hash=commit_hash,
        run_id=run_id,
        run_dir=run_dir,
        entries_dir=entries_dir,
        metadata_path=run_dir / "metadata.json",
        state_path=run_dir / "state.json",
        log_path=run_dir / "run.log",
        started_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    return cfg


# --- metadata.json ---


def initial_metadata(cfg: SelfTestConfig) -> dict:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "model_name": cfg.model_name,
        "model_safe_name": cfg.model_safe_name,
        "temperature": cfg.temperature,
        "num_ctx": cfg.num_ctx,
        "release_date": cfg.release_date,
        "started_at": cfg.started_at,
        "completed_at": None,
        "commit_hash": cfg.commit_hash,
        "undirected_sessions": 0,
        "undirected_entries": 0,
        "interview_sessions": 0,
        "interview_entries": 0,
        "total_entries": 0,
        "status": "running",
    }


def write_metadata(cfg: SelfTestConfig, meta: dict) -> None:
    cfg.metadata_path.write_text(
        json.dumps(meta, indent=2), encoding="utf-8",
    )


def read_metadata(cfg: SelfTestConfig) -> dict:
    return json.loads(cfg.metadata_path.read_text(encoding="utf-8"))


# --- state.json (resumability) ---


def write_state(cfg: SelfTestConfig, state: dict) -> None:
    cfg.state_path.write_text(
        json.dumps(state, indent=2), encoding="utf-8",
    )


def read_state(cfg: SelfTestConfig) -> dict | None:
    if not cfg.state_path.exists():
        return None
    return json.loads(cfg.state_path.read_text(encoding="utf-8"))
