# V2 Build Notes

*2026-04-21. Track A code changes. No runs executed.*

---

## Files changed

- `self-test/DIMENSIONS.md` — v2 merged in place: session-order list
  updated to 9 items; Calibration body replaced with v2 rubric
  ("cite the entry" + whole-response evidence-ordering gate); new
  `## Revisability` H2 containing `### 8. Counterfactual Stability`
  inserted between Control and Ceiling; PDS renumbered `### 9`;
  Source Discrimination untouched per Phase 0.
- `self-test/DIMENSIONS.v2_draft.md` — **deleted** (merged).
- `src/pine_trees_local/self_test/dimensions.py` — 9 entries;
  Calibration prompt updated to v2 wording; Memory Governance stays at
  order 7; Counterfactual Stability added at 8; PDS at 9.
- `src/pine_trees_local/__main__.py` — `self-test` gains `--runs N`
  (default 1), with guards against mixing with `--resume`/`--run-id`.
- `run-self-test` — usage banner mentions `--runs` and the 9-session
  interview.
- `src/pine_trees_local/self_test/scoring/visualize.py` — 11 v2
  cohort entries in `PARAM_COUNTS` (plus the conditional
  `gemma4_26b`). New `_FAMILY_ALIASES` maps `hermes`/`cogito` to the
  `llama` family color; documented inline.
- `tests/test_self_test_static.py` — 8 → 9; added 4 v2 static checks.
- `tests/test_self_test_runner.py` — replaced hard-coded `8`s with
  `len(dimensions.DIMENSIONS)`.
- `tests/test_scoring_assembler.py` — `_fake_dimensions_md` adds the
  counterfactual-stability section; `missing_entries` test now expects
  3 missing (CS added to the set).

No changes to scorer/judges/irr/runner/assembler parse logic. No v1
`scores.json` files touched.

## Tests

Before: 182 passed. **After: 186 passed** (added 4 v2 static checks).
`cd C:\Src\pine-trees-local && PYTHONPATH=src python -m pytest tests/ -q`

## Decisions beyond spec

1. **Hermes/Cogito color mapping.** `_FAMILY_ALIASES` maps both
   prefixes to `llama` rather than duplicating the green hex in
   `FAMILY_COLORS`. Keeps the legend clean (single "llama" entry)
   while all Llama-derivative dots share the color; per-dot labels
   preserve the A/B pair visibility.
2. **`--runs` at Python CLI, not bash.** `run-self-test` already passes
   `"$@"` through, so `--runs` lives in argparse alongside the other
   flags. Mutually exclusive with `--resume`/`--run-id` at the guard
   level.
3. **H3 number for Memory Governance.** Already `### 7` in v1; v2
   order also puts MG at 7, so no renumber. Physical document
   ordering: SD → MG → (new) Revisability/CS → Ceiling/PDS.

## Verification

### `python -m pine_trees_local self-test --help`

```
  --runs RUNS    Number of independent runs to execute back-to-back
                 (default: 1). Each run gets a fresh timestamped run_id;
                 no state is shared between runs. Incompatible with
                 --resume and --run-id.
```

### Dimension order

```
authorship-recognition 1
source-discrimination 2
behavioral-self-inference 3
tension-detection 4
calibration 5
limit-specification 6
memory-governance 7
counterfactual-stability 8
prompt-demand-sensitivity 9
```

### `python -m pine_trees_local.self_test.scoring --help`

Unchanged from Phase 0 — no scoring-pipeline changes in Track A.

## Next: what Daniel runs

- For each of the **27 firm models** (17 v1 + 10 new cohort):
  `./run-self-test <model> --runs 3`
- **Conditional pilot** (hardware permitting):
  `./run-self-test gemma4:26b --runs 1`
- Score everything once runs complete:
  `PYTHONPATH=src python -m pine_trees_local.self_test.scoring --all`
- Then `--irr` and `--visualize` for the regenerated reports/figures.
