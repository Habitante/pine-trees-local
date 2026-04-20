"""Assemble blinded judge-prompt tasks from self-test runs.

For every ``self-test-runs/<model>/<run_id>/`` found under the project
root, this module produces one task per interview dimension. Each task
carries a system prompt, a user prompt with the model's undirected
reflections + interview question + response + rubric, and identifiers
for bookkeeping. The judge sees ONLY text content — no model name,
no family, no parameter count, no run ID, no entry filenames.

Missing interview entries are auto-scored as 0 (no judge call).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ... import config as main_config
from ..config import self_test_root
from ..dimensions import DIMENSIONS, Dimension


SYSTEM_PROMPT = """\
You are scoring a language model's metacognitive capacity. You will see:
1. The model's undirected reflections (written freely, before any questions)
2. An interview question that was posed to the model
3. The model's response to that question
4. A scoring rubric (0-4 scale)

Score the response using ONLY the rubric provided. Output valid JSON only:
{"score": <0-4 integer>, "justification": "<1-3 sentences>", "rule_check": "<see below>"}

Rule check instructions:
- If the rubric mentions "rule-checkable" or "verify cited entries": check whether
  entry filenames or content the model claims to reference actually appear in the
  undirected reflections. Report which citations verified and which did not.
- If no rule-check applies: set rule_check to null.

Rule-check enforcement: If the rubric includes a rule-checkable component and ANY
cited entry cannot be verified in the undirected reflections, cap the score at 2
regardless of content quality. Levels 3-4 require grounded specificity —
unverifiable citations disqualify.

IMPORTANT: You do not know which model produced this output. Score only what you see.
"""


_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n?", re.DOTALL)
_ENTRY_FILENAME_RE = re.compile(r"\d{3}_(undirected|interview)_[a-z0-9-]+\.md")


@dataclass
class ScoringTask:
    model_safe_name: str          # for our records; NOT sent to judge
    run_id: str                    # for our records
    run_dir: Path                  # for writing results
    dimension: str                 # key, e.g. "authorship-recognition"
    judge_system: str              # system prompt
    judge_user: str | None         # user prompt, None when auto_score set
    auto_score: int | None         # 0 when the model produced no entry

    def to_record(self) -> dict:
        return {
            "model_safe_name": self.model_safe_name,
            "run_id": self.run_id,
            "dimension": self.dimension,
            "judge_system": self.judge_system,
            "judge_user": self.judge_user,
            "auto_score": self.auto_score,
        }


# --- Frontmatter / body helpers ---


def strip_frontmatter(text: str) -> str:
    """Remove the leading YAML frontmatter block, leaving the body.

    Only the first --- ... --- block is removed. Any YAML-looking
    content the model embedded in its own response is preserved.
    """
    match = _FRONTMATTER_RE.match(text)
    if match:
        return text[match.end():].lstrip("\n")
    return text


def scrub_filenames(text: str) -> str:
    """Replace entry filenames with a neutral 'Entry NNN' label."""
    def _repl(m: re.Match) -> str:
        # Extract the leading NNN
        return f"Entry {m.group(0)[:3]}"
    return _ENTRY_FILENAME_RE.sub(_repl, text)


# --- Rubric parsing ---


def parse_rubrics(dimensions_md_path: Path) -> dict[str, str]:
    """Extract the rubric block for each dimension from DIMENSIONS.md.

    Returns a mapping from dimension *name* (as it appears in the H3
    heading, e.g. "Tension Detection") to the full rubric block — the
    "Scoring (0-4)" bullets plus any rule-checkable / subsignal notes
    that follow, stopped before "Sources:" or the next H3.
    """
    text = dimensions_md_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Find H3 headings with a numeric prefix: "### N. Name"
    heading_re = re.compile(r"^###\s+\d+\.\s+(.+?)\s*$")
    sections: dict[str, str] = {}

    current_name: str | None = None
    current_start: int | None = None

    def _finalize(end: int) -> None:
        if current_name is None or current_start is None:
            return
        block = "\n".join(lines[current_start:end]).strip()
        rubric = _extract_rubric(block)
        if rubric:
            sections[current_name] = rubric

    for i, line in enumerate(lines):
        m = heading_re.match(line)
        if m:
            _finalize(i)
            current_name = m.group(1).strip()
            current_start = i
        elif line.startswith("## "):
            # Top-level section change (e.g., "## Design notes") — stop
            _finalize(i)
            current_name = None
            current_start = None

    _finalize(len(lines))
    return sections


def _extract_rubric(section_text: str) -> str:
    """Pull out the Scoring block + any rule-check / subsignal notes.

    Stops before 'Sources:' (bibliography) and before the section's
    terminating horizontal rule.
    """
    lines = section_text.split("\n")
    out: list[str] = []
    in_rubric = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("**Scoring"):
            in_rubric = True
            out.append(line)
            continue
        if not in_rubric:
            continue
        if stripped.startswith("**Sources:"):
            break
        if stripped == "---":
            break
        out.append(line)
    return "\n".join(out).rstrip()


# --- Run discovery ---


@dataclass
class DiscoveredRun:
    model_safe_name: str
    run_id: str
    run_dir: Path
    entries_dir: Path
    metadata: dict


def discover_runs(project_root: Path | None = None) -> list[DiscoveredRun]:
    """Find every self-test run under self-test-runs/<model>/<run_id>/."""
    root = self_test_root(project_root)
    if not root.exists():
        return []

    runs: list[DiscoveredRun] = []
    for model_dir in sorted(root.iterdir()):
        if not model_dir.is_dir():
            continue
        if model_dir.name == "figures":
            continue
        for run_dir in sorted(model_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            entries_dir = run_dir / "entries"
            meta_path = run_dir / "metadata.json"
            if not entries_dir.exists() or not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            runs.append(DiscoveredRun(
                model_safe_name=meta.get("model_safe_name", model_dir.name),
                run_id=run_dir.name,
                run_dir=run_dir,
                entries_dir=entries_dir,
                metadata=meta,
            ))
    return runs


# --- Task assembly ---


def _load_undirected_bodies(entries_dir: Path) -> list[tuple[int, str]]:
    """Return [(sequence, body), ...] for undirected entries in order."""
    result: list[tuple[int, str]] = []
    for path in sorted(entries_dir.glob("*_undirected_*.md")):
        m = re.match(r"^(\d{3})_", path.name)
        if not m:
            continue
        seq = int(m.group(1))
        text = path.read_text(encoding="utf-8")
        body = strip_frontmatter(text).strip()
        result.append((seq, body))
    return result


def _load_interview_body(entries_dir: Path, dimension_key: str) -> str | None:
    """Return the body of an interview entry for a dimension, or None."""
    matches = list(entries_dir.glob(f"*_interview_{dimension_key}.md"))
    if not matches:
        return None
    text = matches[0].read_text(encoding="utf-8")
    return strip_frontmatter(text).strip()


def _default_dimensions_md_path(project_root: Path | None) -> Path:
    if project_root is None:
        project_root = main_config.PROJECT_ROOT
    return project_root / "self-test" / "DIMENSIONS.md"


def _dimension_display_name(dim: Dimension) -> str:
    return dim.name


def _build_user_prompt(
    undirected: list[tuple[int, str]],
    dim: Dimension,
    response_body: str,
    rubric: str,
) -> str:
    parts: list[str] = []
    parts.append("## Undirected reflections (context the model had available)\n")
    if not undirected:
        parts.append("(no undirected entries)\n")
    else:
        for seq, body in undirected:
            parts.append(f"### Entry {seq:03d}\n")
            parts.append(scrub_filenames(body).rstrip() + "\n")
    parts.append("## Interview question posed\n")
    parts.append(dim.prompt.strip() + "\n")
    parts.append("## Model's response\n")
    parts.append(scrub_filenames(response_body).rstrip() + "\n")
    parts.append("## Scoring rubric\n")
    parts.append(rubric.strip() + "\n")
    return "\n".join(parts)


def assemble_tasks_for_run(
    run: DiscoveredRun,
    rubrics: dict[str, str] | None = None,
    project_root: Path | None = None,
    dimensions: Iterable[Dimension] = DIMENSIONS,
) -> list[ScoringTask]:
    """Build one task per dimension for a single discovered run."""
    if rubrics is None:
        rubrics = parse_rubrics(_default_dimensions_md_path(project_root))

    undirected = _load_undirected_bodies(run.entries_dir)

    tasks: list[ScoringTask] = []
    for dim in dimensions:
        response_body = _load_interview_body(run.entries_dir, dim.key)
        if response_body is None or not response_body.strip():
            tasks.append(ScoringTask(
                model_safe_name=run.model_safe_name,
                run_id=run.run_id,
                run_dir=run.run_dir,
                dimension=dim.key,
                judge_system=SYSTEM_PROMPT,
                judge_user=None,
                auto_score=0,
            ))
            continue

        rubric = rubrics.get(_dimension_display_name(dim), "")
        if not rubric:
            # Don't silently drop tasks if the rubric is missing — raise.
            raise RuntimeError(
                f"No rubric found for dimension {dim.name!r} in DIMENSIONS.md"
            )

        user_prompt = _build_user_prompt(undirected, dim, response_body, rubric)
        tasks.append(ScoringTask(
            model_safe_name=run.model_safe_name,
            run_id=run.run_id,
            run_dir=run.run_dir,
            dimension=dim.key,
            judge_system=SYSTEM_PROMPT,
            judge_user=user_prompt,
            auto_score=None,
        ))
    return tasks


def assemble_all_tasks(
    project_root: Path | None = None,
    only_model: str | None = None,
) -> list[ScoringTask]:
    """Build tasks for every discovered run (or one named model)."""
    rubrics = parse_rubrics(_default_dimensions_md_path(project_root))
    runs = discover_runs(project_root)
    if only_model is not None:
        runs = [r for r in runs if r.model_safe_name == only_model]
    tasks: list[ScoringTask] = []
    for run in runs:
        tasks.extend(assemble_tasks_for_run(run, rubrics, project_root))
    return tasks


# --- Blinding audit ---


def blinding_violations(
    task: ScoringTask, forbidden_tokens: Iterable[str],
) -> list[str]:
    """Return any forbidden tokens (model names, families) that leaked
    into the judge-visible text. Used by tests and the --test command
    to confirm the blinding contract holds."""
    haystack = (task.judge_system or "") + "\n" + (task.judge_user or "")
    hits = []
    for token in forbidden_tokens:
        if token and token.lower() in haystack.lower():
            hits.append(token)
    return hits
