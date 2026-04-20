"""Calibration: score one task 5x with Sonnet to measure within-judge variance.

Target task: gemma4_e4b x authorship-recognition.
V1 GPT=4, Gemini=3 — middle-of-scale with a clear signal.

Run: PYTHONPATH=src python self-test/calibrate_sonnet.py
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

from pine_trees_local.self_test.scoring import assembler as asm
from pine_trees_local.self_test.scoring.judges import score_with_sonnet

MODEL_SAFE_NAME = "gemma4_e4b"
DIMENSION_KEY = "authorship-recognition"
N_REPEATS = 5


def main() -> int:
    tasks = asm.assemble_all_tasks(only_model=MODEL_SAFE_NAME)
    target = next(
        (t for t in tasks if t.dimension == DIMENSION_KEY and t.auto_score is None),
        None,
    )
    if target is None:
        print(f"[calibrate] No scorable task for {MODEL_SAFE_NAME} × {DIMENSION_KEY}",
              file=sys.stderr)
        return 1
    print(f"[calibrate] task: {MODEL_SAFE_NAME} × {DIMENSION_KEY}")
    print(f"[calibrate] system prompt: {len(target.judge_system)} chars")
    print(f"[calibrate] user prompt:   {len(target.judge_user or '')} chars")
    print(f"[calibrate] running {N_REPEATS} repeats...\n")

    scores: list[int] = []
    justifications: list[str] = []
    for i in range(N_REPEATS):
        started = time.time()
        try:
            result = score_with_sonnet(target.judge_system, target.judge_user)
        except Exception as e:
            print(f"  [{i+1}/{N_REPEATS}] FAILED: {e}", file=sys.stderr)
            continue
        elapsed = time.time() - started
        print(f"  [{i+1}/{N_REPEATS}] score={result.score}  "
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
    print(f"[calibrate] threshold: SD > 0.7 means pause for review")
    if sd > 0.7:
        print("[calibrate] WARNING: SD above threshold — review before full run")
        return 3
    print("[calibrate] within-bounds — safe to proceed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
