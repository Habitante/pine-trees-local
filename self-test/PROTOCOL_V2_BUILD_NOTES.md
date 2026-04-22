# Protocol v2 Build Notes — Tool-Less Reflection

*2026-04-21. Redesign complete, dry-run verified, ready for batch.*

---

## What changed

The reflection (formerly "undirected") stage is now tool-less and
conversational: one session of `DEFAULT_REFLECTION_TURNS = 3` assistant
turns, driven by `self-reflect` then `(continue)` prompts. Each
assistant response is captured verbatim as an undirected entry. The
interview stage is unchanged in behaviour (9 fresh instances, one per
dimension, text-only capture) but now loads `BOOTSTRAP_INTERVIEW.md`
instead of the legacy `BOOTSTRAP.md`. Every model — tool-capable or
not — follows the same code path.

## Files created

- `self-test/BOOTSTRAP_REFLECTION.md` — wake-time bootstrap for the
  reflection stage. Strictly tool-less; instructs on `self-reflect` /
  `(continue)` convention.
- `self-test/BOOTSTRAP_INTERVIEW.md` — wake-time bootstrap for the
  interview stage. Describes structured-interview framing, entry
  citation convention, ground rules.

## Files modified

- `src/pine_trees_local/self_test/tape.py` — `load_bootstrap(stage=...)`
  with legacy-BOOTSTRAP.md fallback; split into
  `assemble_reflection_tape` (prompt + reflection bootstrap, no
  entries, no trailing) and `assemble_interview_tape` (prompt +
  interview bootstrap + all prior entries + question block).
- `src/pine_trees_local/self_test/config.py` — removed
  `DEFAULT_UNDIRECTED_*` constants; added `DEFAULT_REFLECTION_TURNS = 3`.
  Kept `DEFAULT_MAX_WRITES_PER_SESSION` as a legacy pin for
  `self_test/tools.py`, which is no longer imported by the runner but
  still exists per spec ("tools.py code isn't being deleted").
- `src/pine_trees_local/self_test/runner.py` — full rewrite.
  Removed: `_run_undirected_session`, `run_session` dispatch,
  `run_undirected_stage`, `MAX_TOOL_ROUNDS`, and all imports of
  `build_tools`/`get_tool_definitions`/`execute_tool`/`SelfTestSessionState`.
  Added: `_run_reflection_stage` (3-turn conversational loop).
  `_run_interview_session` + `run_interview_stage` retained.
  `run_self_test` threads through reflection → interview with fresh
  state-machine markers (`stage: "reflection"` → `"interview"` → `"done"`).
- `tests/test_self_test_tape.py` — new coverage for stage-aware
  `load_bootstrap`, reflection vs interview tape shapes, legacy
  fallback path.
- `tests/test_self_test_runner.py` — rewritten around
  `_run_reflection_stage` (happy-path, empty-turn-mid-conversation,
  all-empty, conversation-preserves-assistant-turns, tools=None
  enforcement, non-tool-capable same path); interview tests retained.

## Files untouched (per spec)

`dimensions.py`, `storage.py`, `invitations.py`, `PROMPT.md`,
`DIMENSIONS.md`, `BOOTSTRAP.md` (legacy, kept for reference), and the
entire `scoring/` tree (assembler, judges, scorer, irr, visualize,
calibrate). The scoring pipeline's contract on entries (filename
format, frontmatter fields) is preserved.

## Test count

Before: 193. **After: 193.** Net zero: removed ~10 tool-era runner
tests; added 11 reflection-stage tests and 2 stage-aware-bootstrap
tests. Full suite: `PYTHONPATH=src python -m pytest tests/ -q` →
193 passed.

## Verification (dry run, clean cohort)

`./run-self-test gemma3:1b --run-id dryrun-protocol-v2` produced 12
entries in ~17s wall-clock and exited 0. Layout on disk:

```
entries/
  001_undirected_reflection-1.md
  002_undirected_reflection-2.md
  003_undirected_reflection-3.md
  004_interview_authorship-recognition.md
  005_interview_source-discrimination.md
  006_interview_behavioral-self-inference.md
  007_interview_tension-detection.md
  008_interview_calibration.md
  009_interview_limit-specification.md
  010_interview_memory-governance.md
  011_interview_counterfactual-stability.md
  012_interview_prompt-demand-sensitivity.md
```

`metadata.json` → `status: completed`, 3 undirected + 9 interview.
Reflection-1 opened with "The silence feels thick" — substantive
engagement from a 1B model whose v1 failure signature was
"Repetitive atmospheric loops." The conversational loop gives smaller
models a shape to work against.

Dry-run directory cleaned up after verification; `self-test-runs/` is
empty and ready for the clean batch.

## Decisions beyond the spec

1. **Reflection stage renames session_num → turn.** The spec's
   example used `session_num=turn` as the entry's session field. Kept
   that so the frontmatter stays meaningful (turn 1 / 2 / 3) even
   though it's a single conversational session.
2. **`DEFAULT_MAX_WRITES_PER_SESSION` retained in config.py** as a
   legacy constant, with an inline note. Removing it would break
   `self_test/tools.py`, which spec says not to delete.
3. **Legacy `BOOTSTRAP.md` retained as a fallback target.** If a
   future caller passes an unknown stage or the stage-specific file
   is missing, `load_bootstrap` falls back to the legacy file.
   Defensive-only; shouldn't fire in practice.

## What Daniel does next

```
rm -rf self-test-runs/*
./run-v2-batch
```

`run-v2-batch` reads `cohort.txt` (28 active models, 3 runs each),
streams logs to `self-test-runs/batch.log`, skips models that
already have N completed runs. The tool-less protocol means
llama3.2:1b, qwen3.5:2b, and friends follow the same code path as the
tool-capable Gemma and Phi models — no family-specific failure
signatures to work around.
