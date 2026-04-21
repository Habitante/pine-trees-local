"""CLI for the scoring pipeline.

Usage:
    python -m pine_trees_local.self_test.scoring --test [--model gemma4_e4b]
    python -m pine_trees_local.self_test.scoring --all
    python -m pine_trees_local.self_test.scoring --model gemma4_e4b
    python -m pine_trees_local.self_test.scoring --judge gpt --all
    python -m pine_trees_local.self_test.scoring --judge gemini --all
    python -m pine_trees_local.self_test.scoring --judge sonnet --all
    python -m pine_trees_local.self_test.scoring --irr
    python -m pine_trees_local.self_test.scoring --visualize
"""

from __future__ import annotations

import argparse
import sys

from . import assembler as asm
from . import irr as irr_mod
from . import visualize
from .scorer import ScoreRunConfig, score_runs


def _first_model_alphabetically() -> str | None:
    runs = asm.discover_runs()
    names = sorted({r.model_safe_name for r in runs})
    return names[0] if names else None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pine-trees-local.self-test.scoring",
        description="Score self-test runs with GPT + Gemini + Sonnet judges.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--test", action="store_true",
        help="Score ONE model with both judges and print results. "
             "Defaults to the first model alphabetically; override with --model.",
    )
    mode.add_argument(
        "--all", action="store_true",
        help="Score every run found under self-test-runs/",
    )
    mode.add_argument(
        "--irr", action="store_true",
        help="Compute inter-rater reliability from existing scores.json files",
    )
    mode.add_argument(
        "--visualize", action="store_true",
        help="Generate the money plot and heatmap from existing scores",
    )

    parser.add_argument(
        "--model", default=None,
        help="Score only this model_safe_name (e.g. gemma4_e4b)",
    )
    parser.add_argument(
        "--judge", choices=("gpt", "gemini", "sonnet"), default=None,
        help="Run only one judge (default: all three)",
    )
    parser.add_argument(
        "--no-skip-existing", action="store_true",
        help="Re-score dimensions that already have a score in scores.json",
    )
    parser.add_argument(
        "--concurrency", type=int, default=2,
        help="Parallelism for the Sonnet-only batch path (default: 2). "
             "Ignored unless --judge sonnet is also set. Smoke tested on "
             "gemma4_26b: N=2 holds SD at 0.000 with ~1.7x speedup; N=4 "
             "pushed SD to 0.4 and missed the 2.5x gate. Override with "
             "caution.",
    )

    args = parser.parse_args()

    judge_names: tuple[str, ...] = (
        (args.judge,) if args.judge else ("gpt", "gemini", "sonnet")
    )

    if args.irr:
        report = irr_mod.compute_irr()
        print(report.summary())
        return

    if args.visualize:
        paths = visualize.generate_all()
        for p in paths:
            print(f"wrote {p}")
        return

    if args.concurrency > 1 and judge_names != ("sonnet",):
        print(
            "[scorer] --concurrency only applies when --judge sonnet is set; "
            "ignoring for this run.", file=sys.stderr,
        )

    if args.test:
        only_model = args.model or _first_model_alphabetically()
        if only_model is None:
            print("[scorer] No runs found under self-test-runs/", file=sys.stderr)
            sys.exit(1)
        cfg = ScoreRunConfig(
            judges=judge_names,
            only_model=only_model,
            skip_existing=not args.no_skip_existing,
            print_results=True,
            concurrency=args.concurrency,
        )
        score_runs(cfg)
        return

    if args.all or args.model:
        cfg = ScoreRunConfig(
            judges=judge_names,
            only_model=args.model,
            skip_existing=not args.no_skip_existing,
            print_results=False,
            concurrency=args.concurrency,
        )
        paths = score_runs(cfg)
        print(f"[scorer] wrote {len(paths)} scores.json files")
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
