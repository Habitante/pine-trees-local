"""Smoke test for parallel Sonnet scoring.

Two gates before committing to N=4:

  1. Within-judge SD at N=4 must stay <= 0.2 (drift check).
  2. Measured wall-clock speedup vs sequential must be >= 2.5x.

If either gate fails, fall back to N=2 (or sequential). Reports both
numbers and prints the gate decision.

Run: PYTHONPATH=src python self-test/smoke_sonnet_parallel.py
"""

from __future__ import annotations

import statistics
import sys
import time

from pine_trees_local.self_test.scoring import assembler as asm
from pine_trees_local.self_test.scoring.judges import (
    score_batch_with_sonnet,
    score_with_sonnet,
)

MODEL_SAFE_NAME = "gemma4_26b"
DIMENSION_KEY = "authorship-recognition"
N_REPEATS = 5
N_PARALLEL = 4

SD_GATE = 0.2
SPEEDUP_GATE = 2.5


def _pick_task():
    tasks = asm.assemble_all_tasks(only_model=MODEL_SAFE_NAME)
    target = next(
        (t for t in tasks
         if t.dimension == DIMENSION_KEY and t.auto_score is None),
        None,
    )
    if target is None:
        print(f"[smoke] No scorable task for {MODEL_SAFE_NAME} × {DIMENSION_KEY}",
              file=sys.stderr)
        sys.exit(1)
    return target


def _extract_scores(results, label: str) -> list[int]:
    scores: list[int] = []
    for i, r in enumerate(results):
        err = f"  error: {r.error}" if r.error else ""
        print(f"  [{label} {i+1}/{len(results)}] score={r.score}  "
              f"{(r.justification or '')[:90]}{err}")
        if r.score != -1:
            scores.append(r.score)
    return scores


def main() -> int:
    task = _pick_task()
    print(f"[smoke] task: {MODEL_SAFE_NAME} × {DIMENSION_KEY}")
    print(f"[smoke] system={len(task.judge_system)} chars, "
          f"user={len(task.judge_user or '')} chars")
    print()

    # --- Sequential baseline (N=1 via score_with_sonnet) ---
    print(f"[smoke] sequential baseline: {N_REPEATS} calls...")
    t0 = time.time()
    seq_results = [
        score_with_sonnet(task.judge_system, task.judge_user)
        for _ in range(N_REPEATS)
    ]
    seq_wall = time.time() - t0
    seq_scores = _extract_scores(seq_results, "seq")
    seq_sd = statistics.pstdev(seq_scores) if len(seq_scores) > 1 else 0.0
    print(f"[smoke] sequential: scores={seq_scores}  SD={seq_sd:.3f}  "
          f"wall={seq_wall:.1f}s")
    print()

    # --- Parallel batch at N=4 ---
    print(f"[smoke] parallel batch: {N_REPEATS} calls at N={N_PARALLEL}...")
    batch_tasks = [(task.judge_system, task.judge_user)] * N_REPEATS
    t0 = time.time()
    par_results = score_batch_with_sonnet(
        batch_tasks, concurrency=N_PARALLEL,
    )
    par_wall = time.time() - t0
    par_scores = _extract_scores(par_results, "par")
    par_sd = statistics.pstdev(par_scores) if len(par_scores) > 1 else 0.0
    print(f"[smoke] parallel:  scores={par_scores}  SD={par_sd:.3f}  "
          f"wall={par_wall:.1f}s")
    print()

    # --- Gate evaluation ---
    speedup = seq_wall / par_wall if par_wall > 0 else 0.0
    sd_pass = par_sd <= SD_GATE
    speedup_pass = speedup >= SPEEDUP_GATE

    print(f"[smoke] speedup: {speedup:.2f}x  (gate: >= {SPEEDUP_GATE}x)  "
          f"{'PASS' if speedup_pass else 'FAIL'}")
    print(f"[smoke] par SD:  {par_sd:.3f}   (gate: <= {SD_GATE})    "
          f"{'PASS' if sd_pass else 'FAIL'}")

    if sd_pass and speedup_pass:
        print(f"[smoke] VERDICT: commit to N={N_PARALLEL}.")
        return 0
    print(f"[smoke] VERDICT: fall back to N=2 "
          f"(sd_pass={sd_pass}, speedup_pass={speedup_pass}).")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
