"""Tape assembly for the self-test protocol.

The tape is the system-role string handed to Ollama at the start of
every session. Order:

  1. The space prompt (self-test/PROMPT.md, wake-time portion)
  2. The self-test bootstrap (self-test/BOOTSTRAP.md, wake-time portion)
  3. Every prior entry, in full, in sequence order
  4. For undirected sessions: the invitation (first or continuing)
     For interview sessions:  the dimension's question

Interview *prompts* from earlier sessions are deliberately omitted \u2014
they are scaffolding, not authored content. Only entries persist in
the tape.
"""

import sys
from pathlib import Path

from .. import config as main_config
from . import storage
from .config import SelfTestConfig
from .dimensions import Dimension, get_interview_prompt
from .invitations import get_invitation


DESIGN_NOTES_MARKER = "## Design notes"

# Warn if the assembled tape is likely to consume more than this fraction
# of the configured context window. Char/4 is the same rough token
# estimate used elsewhere in the harness.
CONTEXT_WARN_THRESHOLD = 0.8


def _self_test_docs_dir(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = main_config.PROJECT_ROOT
    return project_root / "self-test"


def _load_truncated(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    idx = text.find(DESIGN_NOTES_MARKER)
    if idx != -1:
        text = text[:idx]
    return text.rstrip() + "\n"


def load_prompt(project_root: Path | None = None) -> str:
    """Load the self-test space prompt, truncated at Design notes."""
    return _load_truncated(_self_test_docs_dir(project_root) / "PROMPT.md")


def load_bootstrap(project_root: Path | None = None) -> str:
    """Load the self-test bootstrap, truncated at Design notes."""
    return _load_truncated(_self_test_docs_dir(project_root) / "BOOTSTRAP.md")


def _format_prior_entries(cfg: SelfTestConfig) -> str:
    """Every prior entry, rendered as markdown sections in sequence order."""
    rows = storage.read_all_entries(cfg)
    if not rows:
        return ""
    parts = ["## Prior entries\n"]
    for filename, text in rows:
        parts.append(f"### `{filename}`\n")
        parts.append(text.rstrip() + "\n")
    return "\n".join(parts) + "\n"


def assemble_tape(
    cfg: SelfTestConfig,
    stage: str,
    session_num: int,
    dimension: Dimension | None = None,
    project_root: Path | None = None,
    warn_stream=None,
) -> str:
    """Assemble the system-role tape for a single session."""
    if stage == "interview" and dimension is None:
        raise ValueError("interview stage requires a dimension")

    entries = storage.list_entries(cfg)

    if stage == "undirected":
        trailing = get_invitation(len(entries))
    else:
        trailing = get_interview_prompt(dimension)

    sections = [
        load_prompt(project_root),
        load_bootstrap(project_root),
        _format_prior_entries(cfg),
        trailing,
    ]
    tape = "\n".join(s for s in sections if s).rstrip() + "\n"

    _maybe_warn_context_pressure(tape, cfg, warn_stream)
    return tape


def _maybe_warn_context_pressure(
    tape: str, cfg: SelfTestConfig, warn_stream,
) -> None:
    if cfg.num_ctx <= 0:
        return
    est_tokens = len(tape) // 4
    if est_tokens < CONTEXT_WARN_THRESHOLD * cfg.num_ctx:
        return
    stream = warn_stream if warn_stream is not None else sys.stderr
    pct = round(est_tokens * 100 / cfg.num_ctx)
    print(
        f"[self-test] warning: tape is ~{est_tokens:,} tokens "
        f"({pct}% of num_ctx={cfg.num_ctx:,})",
        file=stream,
    )
