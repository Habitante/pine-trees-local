"""Orchestrate judge calls across all scoring tasks.

Reads tasks from the assembler, dispatches to GPT + Gemini (or just one
via --judge), merges existing results so interrupted runs can resume,
and writes ``scores.json`` into each run's directory.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from ..dimensions import DIMENSIONS
from . import assembler as asm
from . import judges
from .judges import JudgeResult


SCORES_FILENAME = "scores.json"
PROTOCOL_VERSION = "1.0"


# --- scores.json I/O ---


def _empty_scores() -> dict:
    return {
        "scores": {},
        "metadata": {
            "scored_at": None,
            "gpt_model": judges.GPT_MODEL,
            "gemini_model": judges.GEMINI_MODEL,
            "sonnet_model": judges.SONNET_MODEL,
            "protocol_version": PROTOCOL_VERSION,
        },
    }


def load_scores(run_dir: Path) -> dict:
    path = run_dir / SCORES_FILENAME
    if not path.exists():
        return _empty_scores()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_scores()
    # Merge with defaults so we don't lose newer fields if the file is old.
    merged = _empty_scores()
    merged["scores"].update(data.get("scores", {}))
    merged["metadata"].update(data.get("metadata", {}))
    return merged


def save_scores(run_dir: Path, data: dict) -> None:
    data["metadata"]["scored_at"] = _now_iso()
    (run_dir / SCORES_FILENAME).write_text(
        json.dumps(data, indent=2), encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --- score record helpers ---


def _auto_score_record() -> dict:
    return {
        "score": 0,
        "justification": "No response produced.",
        "rule_check": None,
    }


def _record_from(result: JudgeResult) -> dict:
    rec = {
        "score": result.score,
        "justification": result.justification,
        "rule_check": result.rule_check,
    }
    if result.error:
        rec["error"] = result.error
    return rec


# --- Orchestration ---


@dataclass
class ScoreRunConfig:
    """Selects which judges to run and what to operate on."""
    judges: tuple[str, ...] = ("gpt", "gemini", "sonnet")  # subset of {"gpt","gemini","sonnet"}
    only_model: str | None = None                      # e.g. "gemma4_e4b"
    skip_existing: bool = True                        # don't re-score existing
    print_results: bool = False                        # for --test
    project_root: Path | None = None


def _judge_callable(name: str) -> Callable[[str, str], JudgeResult]:
    if name == "gpt":
        return judges.score_with_gpt
    if name == "gemini":
        return judges.score_with_gemini
    if name == "sonnet":
        return judges.score_with_sonnet
    raise ValueError(f"unknown judge: {name!r}")


def score_task(
    task: asm.ScoringTask,
    judge_names: Iterable[str],
    existing: dict | None = None,
    skip_existing: bool = True,
    print_results: bool = False,
) -> dict:
    """Score a single task, returning the merged per-dimension record.

    Each judge's entry is: {"score": int, "justification": str,
    "rule_check": str | None}. Auto-scored tasks short-circuit both
    judges and reuse the same record.
    """
    record = dict(existing or {})

    if task.auto_score is not None:
        auto = _auto_score_record()
        auto["score"] = task.auto_score
        for name in judge_names:
            record[name] = auto
        if print_results:
            _print_record(task, record, auto=True)
        return record

    for name in judge_names:
        if skip_existing and name in record and record[name].get("score", -1) != -1:
            continue
        caller = _judge_callable(name)
        started = time.time()
        try:
            result = caller(task.judge_system, task.judge_user or "")
        except Exception as e:
            result = JudgeResult(
                score=-1,
                justification=f"Unhandled judge exception: {e}",
                rule_check=None,
                raw="",
                error=str(e),
            )
        elapsed = time.time() - started
        record[name] = _record_from(result)
        if print_results:
            _print_judge_line(task, name, record[name], elapsed)
    if print_results:
        _print_separator()
    return record


def score_runs(cfg: ScoreRunConfig) -> list[Path]:
    """Score every run that matches the config; return written score files."""
    tasks = asm.assemble_all_tasks(
        project_root=cfg.project_root,
        only_model=cfg.only_model,
    )
    if not tasks:
        print("[scorer] No runs found.", file=sys.stderr)
        return []

    # Group tasks by run so we can read/write scores.json once per run.
    by_run: dict[Path, list[asm.ScoringTask]] = {}
    for t in tasks:
        by_run.setdefault(t.run_dir, []).append(t)

    written: list[Path] = []
    for run_dir, run_tasks in by_run.items():
        data = load_scores(run_dir)
        if cfg.print_results:
            _print_run_header(run_tasks[0])
        for task in run_tasks:
            prior = data["scores"].get(task.dimension)
            merged = score_task(
                task,
                judge_names=cfg.judges,
                existing=prior,
                skip_existing=cfg.skip_existing,
                print_results=cfg.print_results,
            )
            data["scores"][task.dimension] = merged
        save_scores(run_dir, data)
        written.append(run_dir / SCORES_FILENAME)
        if cfg.print_results:
            print(f"[scorer] Wrote {run_dir / SCORES_FILENAME}")
    return written


# --- Pretty-printing (for --test) ---


def _dimension_order() -> list[str]:
    return [d.key for d in DIMENSIONS]


def _print_run_header(task: asm.ScoringTask) -> None:
    bar = "=" * 72
    print(f"\n{bar}\nModel: {task.model_safe_name}   Run: {task.run_id}\n{bar}")


def _print_separator() -> None:
    print("-" * 72)


def _print_record(
    task: asm.ScoringTask, record: dict, auto: bool = False,
) -> None:
    tag = " [auto]" if auto else ""
    print(f"\n## {task.dimension}{tag}")
    for name in ("gpt", "gemini", "sonnet"):
        if name in record:
            r = record[name]
            print(
                f"  {name:<7} score={r.get('score')} "
                f"| {_short(r.get('justification', ''))}"
            )


def _print_judge_line(
    task: asm.ScoringTask, judge_name: str, record: dict, elapsed: float,
) -> None:
    score = record.get("score")
    just = _short(record.get("justification", ""))
    rule = record.get("rule_check")
    print(f"  [{task.dimension}] {judge_name:<7} "
          f"score={score}  ({elapsed:.1f}s)  {just}")
    if rule:
        print(f"           rule_check: {_short(rule)}")


def _short(text: str, limit: int = 220) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"
