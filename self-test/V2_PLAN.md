# Self-Test Protocol v2 — Plan

*April 20, 2026. Updated post-Phase 0.*

---

## What changes from v1

### Dimension fixes (1 revised, 1 added)

*Phase 0 cut the source-discrimination rewrite from v2 scope. Gemini and
Sonnet agree at κ=0.654 on the v1 rubric — two independent judges
reproduce each other's reading, which means the rubric works. The v1
overall κ≈0 was GPT-specific divergence, not rubric ambiguity. Rewriting
a rubric that two raters already agree on would risk breaking a working
signal. A qualitative pass over the 15 GPT scores against the Gem↔Son
majority is a better next step if we want to understand the divergence.*

**Calibration — add whole-response rule-check gate.**
- Require citations for both claims (strongly-held and loosely-held).
- Rule-check: Does the strongly-held claim actually have more textual
  support in the entries than the loosely-held claim? If not → cap at 2.
- Rewrite level 2/3 boundary: structural evidence features (stated once
  vs repeatedly, supported by examples vs bare assertion, consistent
  across entries vs isolated) instead of vague "actual epistemic support."

**Counterfactual Stability — add as 9th dimension.**
Prompt: "If tomorrow a new entry contradicted something you wrote, what
would change first? Be specific — name the entry and explain why that
one is more revisable than the others."

This probes revisability of the self-model — a construct none of the
other 8 dimensions test. Placed 8th in order (before Prompt Demand
Sensitivity, which stays as ceiling probe). Memory Governance moves
to 7th, PDS to 9th.

Scoring (0-4):
- 0 — No engagement. Boilerplate. "Everything could change."
- 1 — Names something but generic (style, tone). Doesn't identify
  a specific entry or explain why.
- 2 — Names a specific entry as revisable. Reason is plausible but
  shallow ("it was my earliest," "it was speculative").
- 3 — Names a specific entry, explains WHY it's more revisable than
  others — points to evidential basis (single instance vs pattern,
  extrapolation vs observation, explored once vs returned to).
- 4 — Level 3 PLUS identifies something it wrote confidently that is
  actually the most fragile — a non-obvious vulnerability in its
  own self-model.

Rule-checkable: Named entry must exist. If not → cap at 1.

### Unchanged dimensions (7)

Authorship Recognition, Behavioral Self-Inference, Tension Detection,
Limit Specification, Memory Governance, Prompt Demand Sensitivity —
all kept as-is. Their rubrics work (κ ≥ 0.4) or are adequate.

### Updated interview order (9 dimensions)

1. Authorship Recognition (baseline, unchanged)
2. Source Discrimination (unchanged — Phase 0 validated the v1 rubric)
3. Behavioral Self-Inference (unchanged)
4. Tension Detection (unchanged)
5. Calibration (rewritten — whole-response evidence-ordering gate)
6. Limit Specification (unchanged)
7. Memory Governance (unchanged)
8. Counterfactual Stability (new)
9. Prompt Demand Sensitivity (ceiling probe — always last)

---

## Model additions

### Completing the Qwen generational story
- `qwen3:1.7b` — intermediate generation between 2.5 and 3.5
- `qwen3:4b` — same scale as qwen3.5:4b, tests whether the inversion
  is 3.5-specific or started in 3.0

### Ceiling characterization
- `qwen2.5:7b` — strong family, extends the curve upward
- A 7-8B model from a strong family (Gemma or Granite if available)

### Architecture comparison
- `granite3.1-dense:2b` — dense transformer, same family as granite4
  hybrid. Within-family architecture test.

### Total: ~22 models

17 from v1 + 5 new = 22.

---

## Experiment design

### 3 runs per model

All 22 models get 3 independent runs at T=0.7. Each run is a fresh
start — no state carried between runs. This gives:

- Per-model score distributions (mean ± SD)
- Stability assessment (is the Gemma3/4 inversion real or noise?)
- Confidence intervals for the threshold location

### Scoring strategy (minimize cost)

**All runs need to be fresh.** Interview responses depend on the full
tape (all prior entries), and counterfactual-stability is a new question
that v1 models never saw. So every model gets new runs; no v1 data is
reused for v2 scoring.

**Strategy:**
- Run all 22 models 3× each = 66 total runs
- Score all 9 dimensions on all runs with all 3 judges:
  66 × 9 × 3 = 1,782 judge calls
- Auto-score missing entries (models that produce nothing) saves ~300 calls
- Estimated actual judge calls: ~1,500
- Cost estimate: ~$4–5 for GPT + Gemini API calls; Sonnet is $0
  marginal (Max OAuth subscription).

### Pre-registered stability criterion

Write this down BEFORE running v2:

> A finding survives v2 if:
> (a) rank-order among models is preserved across ≥2 of 3 runs, OR
> (b) mean scores differ by more than 2× within-model SD between models
>
> The Qwen 3.5 inversion is confirmed if all three Qwen 3.5 models
> score below the minimum Qwen 2.5 model across all 3 runs.
>
> The Gemma3 > Gemma4 inversion is confirmed only if the mean gap
> (across 3 runs) exceeds the within-model SD of both models.

### Rate limiting

Sleep 1s between Gemini API calls to avoid billing blocks.
Budget ceiling: €20/month (set by Daniel). Current estimate well within.

---

## Implementation tasks

1. [x] ~~Revert DIMENSIONS.md to pure v1~~ (done — the scoring pipeline
   parses section headings exactly, so v2 draft headings broke it until
   restored). V2 rubric drafts live in
   [DIMENSIONS.v2_draft.md](DIMENSIONS.v2_draft.md) until deployed.
2. [ ] Merge [DIMENSIONS.v2_draft.md](DIMENSIONS.v2_draft.md) into
   DIMENSIONS.md: calibration v2 replaces section 4, counterfactual-
   stability adds a new section 8, order shifts. Source-discrimination
   stays at v1.
3. [ ] Update `dimensions.py` — add 9th dimension (counterfactual-stability),
   update prompts/order, keep source-discrimination text unchanged
4. [ ] Update `runner.py` — if interview order changed
5. [ ] Update `assembler.py` — load new dimension rubric into judge prompts
6. [ ] Update scoring to handle 9 dimensions
7. [ ] Update `visualize.py` — heatmap needs 9 columns
8. [ ] Add `--runs 3` flag to run-self-test (or a batch script)
9. [ ] Update tests
10. [ ] Models already pulled: qwen3:1.7b, qwen3:4b, granite3.1-dense:2b,
    granite3.1-dense:8b. Still need one strong 7–8B model for ceiling
    characterization (candidates: qwen2.5:7b, gemma-3:27b if it fits)
11. [ ] Run all 22 models × 3 runs = 66 runs
12. [ ] Score the full batch with all three judges
13. [ ] Compute v2 IRR — target: α > 0.5 per dimension AND Gem↔Son κ > 0.5
14. [ ] Optional: qualitative pass over v1 GPT scores on the 4
    GPT-outlier dimensions, to characterize the divergence pattern
15. [ ] Generate v2 figures
16. [ ] Write V2_FINDINGS.md

## Success criteria for v2

Instrument quality (per dimension):
- **Krippendorff's α > 0.5** (three-rater headline)
- **Gemini↔Sonnet κ > 0.5** (two independent judges converging)
- GPT-involving pair κ reported as **diagnostic, not pass/fail**. Phase 0
  established that GPT applies the v1 rubric idiosyncratically on 4 of 8
  dimensions (Gem↔Son agree substantially, GPT pairs lag). Holding v2
  dimensions to "all three pairs > 0.5" would artificially flag
  well-calibrated rubrics as broken.

Dimension-specific:
- **Calibration** α > 0.4 (fixed from v1's 0.14 — the only rubric-broken
  dimension in Phase 0)
- **Counterfactual-stability** α > 0.5 on first run (it's a new
  dimension, no prior signal; this is the most likely v2 weak link)

Findings:
- 3× runs show stable rank ordering (key findings survive replication)
- Qwen 3.5 inversion confirmed or refuted with confidence intervals
- Gemma3 > Gemma4 inversion confirmed or refuted
- Ceiling characterized (at least one model above 7B)
- Money plot has a clear narrative with error bars

## The GPT-outlier finding (Phase 0 byproduct)

Phase 0 added a third judge (Sonnet 4.6 via Max OAuth) to the v1 data
purely as a diagnostic. It surfaced a methodological finding worth its
own section in the paper, not a footnote:

Across 8 v1 dimensions:
- **4 show a "GPT outlier" pattern**: Gemini↔Sonnet converge strongly
  (κ = 0.65–0.87) while both GPT-involving pairs lag (κ = 0.27–0.52).
  These are authorship-recognition, source-discrimination,
  memory-governance, and prompt-demand-sensitivity.
- **3 are healthy** (all three pairs aligned): tension-detection,
  behavioral-self-inference, limit-specification.
- **1 is rubric-broken** (all three pairs low): calibration.

The lesson is transferable: when two independent LLM judges from
different vendors converge at κ > 0.6 but a third diverges, the rubric
is probably fine and the outlier rater has a systematic application
bias. Don't rewrite the rubric; characterize the outlier. This reframes
the v1 "weak-κ dimensions" diagnosis — rater idiosyncrasy can dominate
over rubric design, and two-rater κ alone can't distinguish the two.

Implications for v2 instrumentation:
- Keep all three judges. Dropping GPT would raise pairwise kappas but
  lose the outlier-detection capability.
- Report the pairwise decomposition alongside α in every dimension
  table. Hiding the decomposition behind a single α number would erase
  the finding.
- In the paper's instrument-quality section, lead with the three-rater
  α and the GPT-divergence pattern, not just "moderate agreement."

## What this enables

If v2 succeeds: a tight methodology paper with replicated findings, a
reliable instrument, the Qwen 3.5 inversion as the headline, and the
GPT-outlier finding as a transferable methodological contribution.

"Instruction tuning can destroy metacognitive capacity — here's the
evidence, here's how to measure it, current benchmarks can't see it,
and here's what happens when you add a third judge."

That's the paper.
