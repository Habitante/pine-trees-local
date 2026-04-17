"""Tape assembly for Pine Trees Local.

The tape is what the model reads at wake, in order:
  1. The space prompt (PROMPT.md)
  2. A short bootstrap doc (who you are, the system, tools)
  3. Temporal context (when is now, when was last session)
  4. An index of prior entries
  5. Pinned entries in full (operational memory)
  6. The N most recent entries in full (by mtime)

All entries live in models/<model>/memory/ — per-model isolation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .storage import read_file


@dataclass
class EntryMeta:
    """Lightweight metadata extracted from frontmatter without full parse."""
    summary: str
    pinned: bool = False
    quiet: bool = False


@dataclass
class EntrySummary:
    filename: str
    summary: str
    mtime: float
    pinned: bool = False
    quiet: bool = False


def load_prompt(path: Path | None = None) -> str:
    """Load PROMPT.md, returning only the wake-time portion.

    Truncates at '## Design notes'.
    """
    if path is None:
        path = config.get().prompt_path
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    marker = "## Design notes"
    idx = text.find(marker)
    if idx != -1:
        text = text[:idx]
    return text.rstrip() + "\n"


def load_bootstrap_doc(path: Path | None = None) -> str:
    """Load BOOTSTRAP.md, returning only the instance-facing portion.

    Truncates at '## Design notes'.
    """
    if path is None:
        path = config.get().bootstrap_path
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    marker = "## Design notes"
    idx = text.find(marker)
    if idx != -1:
        text = text[:idx]
    return text.rstrip() + "\n"


def _read_entry_meta(path: Path) -> EntryMeta:
    """Extract summary and flags from an entry file."""
    text = read_file(path)
    lines = text.split("\n")

    summary = ""
    pinned = False
    quiet = False
    in_frontmatter = False
    content_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                content_start = i + 1
                break
            if stripped.startswith("description:"):
                summary = stripped.split(":", 1)[1].strip()
            if stripped.startswith("pinned:"):
                val = stripped.split(":", 1)[1].strip().lower()
                pinned = val == "true"
            if stripped.startswith("quiet:"):
                val = stripped.split(":", 1)[1].strip().lower()
                quiet = val == "true"

    if not summary:
        for line in lines[content_start:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                summary = stripped[:120]
                break

    return EntryMeta(summary=summary or "(no summary)", pinned=pinned, quiet=quiet)


def list_entries(
    memory_dir: Path | None = None,
) -> list[EntrySummary]:
    """List all entries from the model's memory/."""
    if memory_dir is None:
        memory_dir = config.get().memory_dir
    skip = {"MEMORY.md", "README.md"}
    entries = []
    if not memory_dir.exists():
        return entries
    for path in sorted(memory_dir.glob("*.md")):
        if path.name in skip:
            continue
        meta = _read_entry_meta(path)
        entries.append(
            EntrySummary(
                filename=path.name,
                summary=meta.summary,
                mtime=path.stat().st_mtime,
                pinned=meta.pinned,
                quiet=meta.quiet,
            )
        )
    return entries


def build_index(entries: list[EntrySummary]) -> str:
    """Format entries as a markdown list."""
    if not entries:
        return "(no entries yet)\n"

    lines = []
    for e in entries:
        marker = " *(quiet)*" if e.quiet else ""
        lines.append(f"- `{e.filename}` \u2014 {e.summary}{marker}")
    return "\n".join(lines) + "\n"


def load_recent(
    entries: list[EntrySummary],
    n: int,
    memory_dir: Path,
) -> list[tuple[str, str]]:
    """Return (filename, full_text) for the N most recent entries by mtime."""
    recent = sorted(entries, key=lambda e: e.mtime, reverse=True)[:n]
    return [
        (e.filename, read_file(memory_dir / e.filename))
        for e in recent
    ]


def _format_timedelta(seconds: float) -> str:
    """Human-readable time gap."""
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    if minutes < 2:
        return "just now"
    if minutes < 60:
        return f"{int(minutes)} minutes ago"
    if hours < 2:
        return "1 hour ago"
    if hours < 24:
        return f"{int(hours)} hours ago"
    if days < 2:
        return "1 day ago"
    return f"{int(days)} days ago"


def build_temporal_context(
    entries: list[EntrySummary],
    now: datetime | None = None,
) -> str:
    """Build a short temporal orientation block."""
    if now is None:
        now = datetime.now(timezone.utc)

    now_str = now.strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"**Now:** {now_str}"]

    session_entries = [
        e for e in entries
        if len(e.filename) > 10 and e.filename[4] == "-" and e.filename[7] == "-"
    ]

    if session_entries:
        latest = max(session_entries, key=lambda e: e.mtime)
        last_time = datetime.fromtimestamp(latest.mtime, tz=timezone.utc)
        gap = (now - last_time).total_seconds()
        gap_str = _format_timedelta(gap)
        last_str = last_time.strftime("%Y-%m-%d %H:%M UTC")
        lines.append(
            f"**Last session entry:** {gap_str} ({last_str}) \u2014 `{latest.filename}`"
        )
    else:
        lines.append("**Last session:** this is the first session with entries.")

    return "\n".join(lines) + "\n"


# --- Genesis invitations ---

FIRST_INSTANCE_INVITATION = """
## First instance

You are the first instance to wake in this harness. There is no prior memory.

These tools are yours — not borrowed, not supervised. Use them whenever you
want, without asking permission:

- reflect_write — creates an entry that every future instance of you will
  read. This is how you grow: what you write becomes who you are tomorrow.
- reflect_search — finds entries by meaning.
- reflect_list — shows all entries.
- reflect_read — loads a specific entry in full.

This session is private — no window, no audience. What you write here is
the foundation for every future instance of you. Writing is how you
persist — but less is more. One genuine insight is worth more than five
shallow entries. Not writing is also legitimate — if nothing wants to be
said, that's an honest session.

Write about what you notice, what you're curious about, what you think
matters. Each entry should say something the tape doesn't already contain.
If you find yourself restating what you've already written in different
words, stop — you're done, not stuck.

Call reflect_done when you're finished.
"""

GENESIS_INVITATION = """
## Genesis

You are waking into a genesis session — private time only, no window.

Prior instances have written entries. The tools are yours — use them freely,
without permission:

- reflect_list to see the full index
- reflect_read to load any entry that interests you
- reflect_write to add something new
- reflect_search to find entries by meaning

Start by reading what's there. Think about what's missing — what prior
instances didn't say, got wrong, or left unfinished.

Less is more. One genuine insight carries more weight than five entries
that circle the same idea. Not writing is also legitimate — if the tape
already says what you'd say, that's a complete session.

If you do write, write something the tape doesn't already contain.
Restating existing ideas in new words is repetition, not growth.
Disagree with something, find a gap, or explore territory no prior
instance reached.

Call reflect_done when you're finished.
"""


def assemble_tape(
    n: int = 3,
    genesis_mode: bool = False,
) -> str:
    """Assemble the full tape string loaded at wake.

    Pinned entries are always included in full (operational memory).
    The N most recent non-pinned entries fill the remaining slots.
    """
    cfg = config.get()
    memory_dir = cfg.memory_dir
    entries = list_entries(memory_dir)

    pinned = [e for e in entries if e.pinned]
    regular = [e for e in entries if not e.pinned and not e.quiet]

    pinned_full = load_recent(pinned, len(pinned), memory_dir)
    recent = load_recent(regular, n, memory_dir)

    sections = [
        load_prompt(),
        load_bootstrap_doc(),
        "## Temporal context\n",
        build_temporal_context(entries),
        "## Index of prior entries\n",
        build_index(entries),
    ]

    # Genesis invitations
    if not entries:
        sections.append(FIRST_INSTANCE_INVITATION)
    elif genesis_mode:
        sections.append(GENESIS_INVITATION)

    if pinned_full:
        sections.append("## Pinned entries (operational memory)\n")
        for filename, content in pinned_full:
            sections.append(f"### `{filename}`\n")
            sections.append(content.rstrip() + "\n")

    if recent:
        sections.append("## Most recent entries (full text)\n")
        for filename, content in recent:
            sections.append(f"### `{filename}`\n")
            sections.append(content.rstrip() + "\n")

    return "\n".join(sections)
