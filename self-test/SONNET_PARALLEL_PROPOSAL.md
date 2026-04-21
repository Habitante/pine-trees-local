# Sonnet Judge Parallelization — Proposal

*2026-04-21. Design only. No implementation.*

---

## TL;DR

Sonnet-only batch parallelism via `asyncio.gather` + semaphore; N=4
default; preserve `score_with_sonnet` unchanged. Land between v2 runs
and v2 scoring. Estimated: **~3h → ~50min** on the v2 batch.

## What the SDK actually does

`claude_agent_sdk.query()` routes through `SubprocessCLITransport`,
which spawns **one fresh `claude` CLI process per call** via
`anyio.open_process`. Each reads OAuth from
`~/.claude/.credentials.json`. N concurrent calls → N independent
Node subprocesses under one OAuth token.

Neither `think-tank` nor `claude` uses `asyncio.gather` across
`query()` calls. Think-tank's "concurrent workers" are independent OS
processes. **No empirical data on in-process parallel `query()`.**
Everything below is engineering gated on measurement.

## Concurrency model

Three options, picked **C**:

| | Where | Verdict |
|---|---|---|
| A. Judge-level in one task | fan out gpt+gem+son in `score_task` | ~3× per task; GPT/Gem already fast; wasted complexity |
| B. Task-level for all judges | parallelize outer loop | Drags GPT+Gem into the change; Gemini rate-limit risk; out of scope |
| **C. Sonnet-only batch** | new batch helper, used when `judges == ("sonnet",)` | Matches v2 use case 1:1, minimum surface area |

## Integration point (KISS)

Three additions, no removals:

1. **`judges.py`** — extract the async body of
   `score_with_sonnet` into `_collect_sonnet(system, user)`; add
   `score_batch_with_sonnet(tasks, concurrency=4) -> list[JudgeResult]`
   using `asyncio.gather(*coros, return_exceptions=True)` inside a
   `Semaphore(concurrency)`. `score_with_sonnet` stays for single-call
   callers (tests, `calibrate.py`) — delegates to a 1-item batch.
2. **`scorer.py`** — one new branch in `score_runs`: if
   `cfg.judges == ("sonnet",)` and ≥2 tasks remain after
   `skip_existing` filtering, route through the batch helper;
   otherwise stay on the existing per-task loop. No changes to
   `_judge_callable` or `score_task`.
3. **CLI** — add `--concurrency N` to `__main__.py`, default 4,
   effective only with `--judge sonnet`.

`JudgeResult` contract preserved: batch returns a list in input
order, each item shaped identically to sequential output. Exceptions
from gather are wrapped as `JudgeResult(score=-1, error=...)`, mirroring
`_with_retries` on retry exhaustion. `skip_existing` keeps working
because filtering happens before the batch call. Existing 186 tests
stay green; new tests mock the inner call to verify concurrency,
ordering, and failure isolation.

## Recommended N

**Start N=2 for a one-model smoke test (9 Sonnet calls); move to N=4
for the v2 batch if smoke passes.** N=4 math: 500 calls × 25s ÷ 4 ≈
52 min vs ~3h sequential. Marked **needs measurement before
committing** — specific unknowns: per-process RSS on Windows, Node
startup contention, and whether Anthropic's account-level rate limit
trips at ~4 requests/min sustained.

## Failure handling

`asyncio.gather(return_exceptions=True)` returns a list where each
slot is either a `JudgeResult` or an `Exception`. Each exception →
`JudgeResult(score=-1, error=str(e))`. **No other results are lost;
the batch returns partial success.** `_with_retries` already applies
per-slot inside gather, so transient errors retry independently.

## Backpressure

Fixed N + existing retry handles rate limits per-slot. If rejections
become common, add adaptive degradation (halve N on rejection, double
after a clean batch, floor at 1) — only if measurement demands.

## Sequencing

**Land after v2 runs, before v2 scoring.** V2 runs are ~40h on local
hardware; scoring is separate after. That window gives us time to
smoke-test one model (9 calls), roll back to sequential if problems
surface, and reap the ~3h speedup on the full v2 batch. Landing
earlier: no benefit (v2 runs don't call Sonnet). Landing later: we
eat the 3h cost once unnecessarily.

## Open questions / risks

1. **Windows + 4 concurrent Node processes.** Node startup is heavy
   on Windows. Measure combined RSS during smoke; if >2GB, drop to N=3.
2. **Account-level rate limits under sustained parallelism.** Phase 0
   saw zero `RateLimitEvent`s sequentially. Unknown at 4×.
3. **OAuth credential file concurrent reads.** Read-only, should be
   fine; surface any auth error from any subprocess in logs.
4. **Stdout interleaving** when `print_results=True`. Batch path
   should buffer per-task logs and flush in order.
5. **Temperature drift under load.** Re-run the 5× calibration at N=4;
   verify within-judge SD stays ≤ 0.7.

## Decision points

- [ ] Approve option C vs A/B?
- [ ] N=4 default with N=2 smoke gate?
- [ ] Land between v2 runs and v2 scoring?
- [ ] `asyncio.gather` vs `anyio.create_task_group`? (SDK uses anyio
      internally but `asyncio.gather` is more idiomatic and keeps the
      rest of the codebase sync.)
