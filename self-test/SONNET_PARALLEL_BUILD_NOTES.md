# Sonnet Parallel Build Notes

*2026-04-21. Implementation complete. Committed N=2.*

---

## Files changed

- **`judges.py`** — extracted `_collect_sonnet` (async single call) +
  `_score_one_sonnet_async` (async retry using `asyncio.sleep`);
  added `_batch_async` + `score_batch_with_sonnet(tasks, concurrency,
  model)` using `asyncio.gather(return_exceptions=True)` +
  `Semaphore(concurrency)`. Rewrote `score_with_sonnet` as a 1-item
  wrapper over the batch. Dropped obsolete `SONNET_THROTTLE_SECS`.
- **`scorer.py`** — added `ScoreRunConfig.concurrency`; added
  `_score_runs_sonnet_batch`; `score_runs` routes to it when
  `judges == ("sonnet",)` and `concurrency > 1`. Other paths
  unchanged. `skip_existing` still applied before the batch.
- **`scoring/__main__.py`** — `--concurrency N` (default 2), with
  warning when combined with non-Sonnet judge sets.
- **`tests/test_scoring_sonnet_batch.py`** — 7 new tests (order,
  semaphore bound, N=1 sequential, single-call wrapper parity,
  failure isolation, empty batch, parse failure).

## Test count

Was 186. **Now 193 passing** (+7; no removals).

## Smoke test — measured

Target: `gemma4_26b × authorship-recognition`. ~31s/call.

| Mode | Scores | SD | Wall | Speedup |
|---|---|---:|---:|---:|
| Sequential (N=1) | `[3,3,3,3,3]` | 0.000 | 153.9s | 1.00× |
| **N=2** | `[3,3,3,3,3]` | **0.000** | 88.9s | **1.73×** |
| N=4 | `[3,3,3,3,4]` | 0.400 | 62.8s | 2.45× |

**N=4 failed both gates** (SD 0.400 > 0.2, speedup 2.45× < 2.5×).
**N=2 cleared the SD gate** (0.000) with real 1.73× speedup. Per the
decision rule (commit to the N that passes both gates; else fall back
to N=2), **committed N=2**. Projected v2 impact: ~3h → ~1h45m on a
500-call batch — smaller than the proposal's 52-min projection but
still meaningful.

## Committed N: 2

Defaults match in three places: `score_batch_with_sonnet(..., 2)`,
`ScoreRunConfig.concurrency = 2`, `--concurrency 2`. N=4 remains
available via `--concurrency 4` if Daniel wants to re-measure with a
larger sample.

## Deviations from the proposal

- **Default N is 2, not 4.** Gate worked as designed.
- **SD gate cause uncertain.** N=4's 0.000→0.400 jump at n=5 could be
  load-induced or natural variance earlier n=5 Phase 0 missed. n=20
  could disambiguate; not on this sprint.
- **No adaptive degradation, no stdout buffering** — proposal said
  "only if measurement demands it," and v2 runs `print_results=False`.

## What Daniel does next

- v2 runs continue on local hardware.
- After all v2 runs complete, score three judges sequentially:
  `python -m pine_trees_local.self_test.scoring --all`.
- Sonnet-only rescoring (if needed) routes through the parallel path
  at N=2 automatically:
  `--judge sonnet --all` (override N via `--concurrency N`).
