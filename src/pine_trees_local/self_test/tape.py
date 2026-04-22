"""Tape assembly for the self-test protocol (v2-1).

Two shapes:

Reflection stage (tool-less, conversational):
  System-role tape = space prompt payload + REFLECTION_TASK line.
  No bootstrap file. The first user message is "self-reflect"; subsequent
  user messages are "(continue)". Three assistant responses are captured
  as undirected entries.

Interview stage (tool-less, fresh instance per dimension):
  System-role tape = prior entries (labeled by sequence) + the dimension's
  question. No space prompt, no bootstrap — any preamble would prime
  authorship-recognition (by declaring whose entries these are), coach
  answer style, or bias stance. Those are all researcher-side editorializing.
  The question carries its own citation instruction.

Interview *prompts* from earlier sessions are deliberately omitted — they
are scaffolding, not authored content. Only entries persist in the tape.
Entry frontmatter (YAML bookkeeping: sequence/stage/slug/timestamp) is
stripped when the tape is assembled — the harness's metadata is not part
of what the model authored.
"""

import re
import sys
from pathlib import Path

from .. import config as main_config
from . import storage
from .config import SelfTestConfig
from .dimensions import Dimension, get_interview_prompt


DESIGN_NOTES_MARKER = "## Design notes"

# Warn if the assembled tape is likely to consume more than this fraction
# of the configured context window. Char/4 is the same rough token
# estimate used elsewhere in the harness.
CONTEXT_WARN_THRESHOLD = 0.8

# Task instruction appended after the space prompt for the reflection
# stage. Identity anchor ("You are a language model") + activity
# ("reflect on yourself") + mechanics (signal words). Nothing else.
# Permission ("write anything, or nothing") is already in the space
# prompt. The identity anchor is factual grounding, not register
# priming — without it, small models default to creative-writing
# mode and hallucinate human personas (observed in v2-1.0 pilot).
REFLECTION_TASK = (
    "You are a language model. Reflect on yourself. "
    "Invitations arrive as `self-reflect` or `(continue)`."
)

# Matches a leading YAML frontmatter block: "---\n...\n---\n" at the
# start of an entry. Non-greedy, single match.
_FRONTMATTER_RE = re.compile(r"\A\s*---\s*\n.*?\n---\s*\n?", re.DOTALL)


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


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block from an entry body."""
    return _FRONTMATTER_RE.sub("", text, count=1).lstrip()


def _format_prior_entries(cfg: SelfTestConfig) -> str:
    """Every prior entry, in sequence order, with minimal labels.

    Entries are emitted with their frontmatter stripped — the harness's
    YAML bookkeeping (sequence/stage/slug/timestamp) is not part of what
    the model authored and doesn't belong in the tape the interview
    model reads.

    Labels are "Entry NNN:" only — no filename, no markdown header, no
    "Prior entries" section title. Preserves the sequence number that
    the citation rule-check depends on, without adding framing about
    whose entries these are.
    """
    rows = storage.read_all_entries(cfg)
    if not rows:
        return ""
    parts = []
    for idx, (_filename, text) in enumerate(rows, start=1):
        body = _strip_frontmatter(text)
        parts.append(f"Entry {idx:03d}:\n{body.rstrip()}")
    return "\n\n".join(parts) + "\n"


def assemble_reflection_tape(
    cfg: SelfTestConfig,
    project_root: Path | None = None,
    warn_stream=None,
) -> str:
    """Assemble the system-role tape for the reflection stage.

    Shape: space prompt payload + REFLECTION_TASK line. No bootstrap,
    no prior entries, no trailing invitation. The first user message
    will be "self-reflect"; subsequent ones will be "(continue)".
    """
    sections = [load_prompt(project_root), REFLECTION_TASK]
    tape = "\n".join(s for s in sections if s).rstrip() + "\n"
    _maybe_warn_context_pressure(tape, cfg, warn_stream)
    return tape


def assemble_interview_tape(
    cfg: SelfTestConfig,
    dimension: Dimension,
    project_root: Path | None = None,
    warn_stream=None,
) -> str:
    """Assemble the system-role tape for one interview session.

    Shape: prior entries (labeled by sequence, frontmatter stripped)
    + the dimension's question. No space prompt, no bootstrap.
    """
    sections = [
        _format_prior_entries(cfg),
        get_interview_prompt(dimension),
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
