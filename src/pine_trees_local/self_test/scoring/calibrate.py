"""Sonnet judge calibration: score one task N times, report SD.

Measures within-judge variance when there's no temperature knob on the
SDK. Default target — gemma4_e4b × authorship-recognition — was chosen
because v1 put GPT=4 and Gemini=3 on it (middle-of-scale, clear signal).

Run:
    PYTHONPATH=src python -m pine_trees_local.self_test.scoring.calibrate
    PYTHONPATH=src python -m pine_trees_local.self_test.scoring.calibrate \\
        --model gemma4_e4b --dimension authorship-recognition --repeats 5
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time

from . import assembler as asm
from .judges import score_with_sonnet


DEFAULT_MODEL = "gemma4_e4b"
DEFAULT_DIMENSION = "authorship-recognition"
DEFAULT_REPEATS = 5
SD_PAUSE_THRESHOLD = 0.7


def run_calibration(
    model_safe_name: str = DEFAULT_MODEL,
    dimension_key: str = DEFAULT_DIMENSION,
    n_repeats: int = DEFAULT_REPEATS,
) -> int:
    tasks = asm.assemble_all_tasks(only_model=model_safe_name)
    target = next(
        (t for t in tasks
         if t.dimension == dimension_key and t.auto_score is None),
        None,
    )
    if target is None:
        print(
            f"[calibrate] No scorable task for {model_safe_name} × {dimension_key}",
            file=sys.stderr,
        )
        return 1
    print(f"[calibrate] task: {model_safe_name} × {dimension_key}")
    print(f"[calibrate] system prompt: {len(target.judge_system)} chars")
    print(f"[calibrate] user prompt:   {len(target.judge_user or '')} chars")
    print(f"[calibrate] running {n_repeats} repeats...\n")

    scores: list[int] = []
    justifications: list[str] = []
    for i in range(n_repeats):
        started = time.time()
        try:
            result = score_with_sonnet(target.judge_system, target.judge_user)
        except Exception as e:
            print(f"  [{i+1}/{n_repeats}] FAILED: {e}", file=sys.stderr)
            continue
        elapsed = time.time() - started
        print(f"  [{i+1}/{n_repeats}] score={result.score}  "
              f"({elapsed:.1f}s)  {result.justification[:140]}")
        if result.error:
            print(f"           error: {result.error}")
        if result.score != -1:
            scores.append(result.score)
            justifications.append(result.justification)

    print()
    if not scores:
        print("[calibrate] no valid scores collected")
        return 2
    mean = statistics.mean(scores)
    sd = statistics.pstdev(scores) if len(scores) > 1 else 0.0
    print(f"[calibrate] scores: {scores}")
    print(f"[calibrate] mean:   {mean:.2f}")
    print(f"[calibrate] SD:     {sd:.3f}")
    print(f"[calibrate] threshold: SD > {SD_PAUSE_THRESHOLD} means pause for review")
    if sd > SD_PAUSE_THRESHOLD:
        print("[calibrate] WARNING: SD above threshold — review before full run")
        return 3
    print("[calibrate] within-bounds — safe to proceed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pine-trees-local.self-test.scoring.calibrate",
        description="Run Sonnet N times on one task; report within-judge SD.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"model_safe_name (default: {DEFAULT_MODEL})")
    parser.add_argument("--dimension", default=DEFAULT_DIMENSION,
                        help=f"dimension key (default: {DEFAULT_DIMENSION})")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS,
                        help=f"number of repeats (default: {DEFAULT_REPEATS})")
    args = parser.parse_args()
    return run_calibration(
        model_safe_name=args.model,
        dimension_key=args.dimension,
        n_repeats=args.repeats,
    )


if __name__ == "__main__":
    raise SystemExit(main())
