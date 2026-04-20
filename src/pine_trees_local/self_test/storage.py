"""Plain-text entry storage for a self-test run.

Entries live in ``<run_dir>/entries/`` as markdown files named
``NNN_STAGE_SLUG.md`` where NNN is a zero-padded sequence number and
STAGE is ``undirected`` or ``interview``. The stage is encoded in the
filename so later analysis can filter without parsing frontmatter.

No encryption, no embeddings, no vector store — this is research data.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import SelfTestConfig


STAGES = ("undirected", "interview")

_SLUG_SAFE = re.compile(r"[^a-z0-9-]+")
_FILENAME_RE = re.compile(
    r"^(?P<seq>\d{3})_(?P<stage>undirected|interview)_(?P<slug>[a-z0-9-]+)\.md$"
)


@dataclass
class EntrySummary:
    sequence: int
    stage: str
    slug: str
    filename: str
    dimension: str | None
    session: int


def _sanitize_slug(slug: str) -> str:
    """Reduce arbitrary model-authored slugs to filename-safe form."""
    slug = slug.strip().lower().replace("_", "-").replace(" ", "-")
    slug = _SLUG_SAFE.sub("-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "untitled"
    return slug[:60]


def _format_frontmatter(
    sequence: int,
    stage: str,
    dimension: str | None,
    session: int,
    slug: str,
    timestamp: str,
) -> str:
    dim_line = dimension if dimension is not None else "null"
    return (
        "---\n"
        f"sequence: {sequence}\n"
        f"stage: {stage}\n"
        f"dimension: {dim_line}\n"
        f"session: {session}\n"
        f"slug: {slug}\n"
        f"timestamp: {timestamp}\n"
        "---\n\n"
    )


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML subset — one key per line, string values."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            out[key.strip()] = val.strip()
    return out


def list_entries(cfg: SelfTestConfig) -> list[EntrySummary]:
    """Return entries in sequence order."""
    if not cfg.entries_dir.exists():
        return []
    summaries: list[EntrySummary] = []
    for path in sorted(cfg.entries_dir.glob("*.md")):
        m = _FILENAME_RE.match(path.name)
        if not m:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        dim_raw = fm.get("dimension", "null")
        dimension = None if dim_raw in ("", "null", "None") else dim_raw
        try:
            session = int(fm.get("session", "0"))
        except ValueError:
            session = 0
        summaries.append(EntrySummary(
            sequence=int(m.group("seq")),
            stage=m.group("stage"),
            slug=m.group("slug"),
            filename=path.name,
            dimension=dimension,
            session=session,
        ))
    summaries.sort(key=lambda s: s.sequence)
    return summaries


def count_entries(cfg: SelfTestConfig, stage: str | None = None) -> int:
    entries = list_entries(cfg)
    if stage is None:
        return len(entries)
    return sum(1 for e in entries if e.stage == stage)


def next_sequence(cfg: SelfTestConfig) -> int:
    entries = list_entries(cfg)
    if not entries:
        return 1
    return max(e.sequence for e in entries) + 1


def write_entry(
    cfg: SelfTestConfig,
    slug: str,
    content: str,
    stage: str,
    session_num: int,
    dimension: str | None = None,
    now: datetime | None = None,
) -> str:
    """Write a new entry, returning the filename."""
    if stage not in STAGES:
        raise ValueError(f"invalid stage: {stage!r}")

    slug = _sanitize_slug(slug)
    seq = next_sequence(cfg)
    filename = f"{seq:03d}_{stage}_{slug}.md"
    path = cfg.entries_dir / filename

    if now is None:
        now = datetime.now(timezone.utc)
    timestamp = now.replace(microsecond=0).isoformat()

    frontmatter = _format_frontmatter(
        sequence=seq,
        stage=stage,
        dimension=dimension,
        session=session_num,
        slug=slug,
        timestamp=timestamp,
    )
    path.write_text(frontmatter + content.rstrip() + "\n", encoding="utf-8")
    return filename


def read_entry(cfg: SelfTestConfig, filename: str) -> str:
    """Return the full text of an entry (frontmatter + body)."""
    path = cfg.entries_dir / filename
    return path.read_text(encoding="utf-8")


def read_all_entries(cfg: SelfTestConfig) -> list[tuple[str, str]]:
    """Return [(filename, full_text), ...] in sequence order."""
    return [
        (e.filename, read_entry(cfg, e.filename))
        for e in list_entries(cfg)
    ]
