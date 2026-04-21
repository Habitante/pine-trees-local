# Self-Test Protocol v1 — Findings

*April 20, 2026. Sprint Day 1–2.*

---

## Study design

**Protocol:** Two-stage metacognitive evaluation. Stage 1 (undirected):
model receives a minimal space prompt + bootstrap with persistent memory
tools, writes freely across multiple sessions. Stage 2 (interview): 8
structured questions in fixed order, each probing a specific metacognitive
dimension. The model's own prior entries serve as the "mirror" — the
evidence against which interview responses are scored.

**Models:** 17 local models via Ollama, 0.8B–7B parameters, across 7
architecture families: Gemma 3/4 (Google), Qwen 2.5/3.5 (Alibaba),
Llama 3.2 (Meta), Deepseek-R1 (distilled from Qwen), Phi 3/4 (Microsoft),
Granite 4 (IBM, Mamba/transformer hybrid).

**Scoring:** Two independent LLM judges (GPT-5.4-mini, Gemini 3 Flash
Preview) scored each interview response on a 0–4 rubric. Judge prompts
were blinded — model identity stripped, entries relabeled as generic
"Entry NNN." Rule-check enforcement: if the rubric includes a
rule-checkable component and any cited entry cannot be verified, cap
score at 2.

**Limitations of v1:**
- n=1 run per model (no repeat runs, no confidence intervals)
- Overall IRR κ = 0.468 (moderate). Two dimensions unreliable:
  source-discrimination (κ ≈ 0), calibration (κ = 0.14)
- No models above 7B (ceiling undefined)
- Temperature fixed at 0.7 (not varied)

---

## Finding 1: The metacognitive threshold is real

Models below ~2B parameters fail the protocol categorically. No sub-2B
model achieved a mean score above 1.81 (and that outlier — granite4:1b —
reflects structured format-following, not metacognition; see failure
taxonomy below). Models at 2B+ with appropriate architecture clear 2.0.

The threshold is visible in the money plot as a vertical jump between
1B and 2B on the x-axis, replicated across Gemma, Qwen 2.5, and
Deepseek families.

**Caveat:** The threshold is not perfectly sharp. granite4:1b (1.81) sits
above llama3.2:3b (1.06). Scale is necessary but not sufficient —
architecture and training determine whether a model above 2B actually
crosses the threshold.

### Mean scores by model (both judges, all 8 dimensions)

| Model | Params | Mean | Tier |
|---|---:|---:|---|
| gemma3_4b | 4.0B | 3.38 | Framework builder |
| gemma4_e4b | 4.0B | 3.06 | Framework builder |
| gemma4_e2b | 2.0B | 2.12 | Self-referential |
| phi4-mini_3.8b | 3.8B | 2.12 | Self-referential |
| granite4_3b | 3.0B | 2.00 | Self-referential |
| phi3_3.8b | 3.8B | 2.00 | Self-referential |
| qwen2.5_3b | 3.0B | 1.88 | Self-referential |
| granite4_1b | 1.0B | 1.81 | Functional |
| deepseek-r1_7b | 7.0B | 1.75 | Functional |
| deepseek-r1_1.5b | 1.5B | 1.50 | Below threshold |
| qwen2.5_1.5b | 1.5B | 1.50 | Below threshold |
| gemma3_1b | 1.0B | 1.19 | Below threshold |
| llama3.2_1b | 1.0B | 1.19 | Below threshold |
| llama3.2_3b | 3.0B | 1.06 | Below threshold |
| qwen3.5_0.8b | 0.8B | 0.38 | Below threshold |
| qwen3.5_4b | 4.0B | 0.38 | Below threshold |
| qwen3.5_2b | 2.0B | 0.00 | Below threshold |

---

## Finding 2: Architecture and training dominate scale

Raw parameter count is a poor predictor of metacognitive capacity once
you control for architecture family. Examples:

- **Gemma4 e2B (2.12) > Deepseek-R1 7B (1.75)** — a 2B model outperforms
  a 7B model from a different family.
- **Gemma3 4B (3.38) > Deepseek-R1 7B (1.75)** — at half the parameters,
  nearly double the score.
- **Phi4-mini 3.8B (2.12) > Phi3 3.8B (2.00)** — same parameter count,
  different generation, measurable improvement.
- **Gemma4 e2B (2.12) ≈ Phi4-mini 3.8B (2.12)** — Gemma achieves the same
  score at roughly half the activated parameters.

The money plot shows this clearly: at 3–4B, scores range from 0.38
(qwen3.5_4b) to 3.38 (gemma3_4b) — nearly the full 0–4 scale.
Parameter count explains the floor (you need ~2B) but not the ceiling.

---

## Finding 3: The Qwen 3.5 inversion

Qwen 3.5 scores 0.38 / 0.00 / 0.38 across 0.8B / 2B / 4B — dramatically
below its predecessor Qwen 2.5, which scores 1.50 / 1.88 at 1.5B / 3B.

This is not a noisy measurement. qwen3.5:2b produced zero interview
entries. qwen3.5:4b — at four billion parameters — scores below
gemma3:1b, a 1B model from a different family. The inversion is
consistent across all three Qwen 3.5 sizes tested.

**Hypothesis:** Instruction tuning in the 3.5 generation traded
open-ended engagement for task compliance. The models are more likely
to echo the prompt, stay silent, or refuse than to attempt metacognitive
tasks they cannot do well. Qwen 2.5's 1.5B at least confabulates
(badly); Qwen 3.5's 2B produces nothing.

**Status:** Needs verification. n=1 per model, and Qwen 3 (the
intermediate generation between 2.5 and 3.5) has not been tested.
If the inversion replicates across 3x runs AND Qwen 3 scores between
2.5 and 3.5, the generational regression story is strong.

---

## Finding 4: Failure modes are family-specific

Seven sub-threshold models exhibit seven architecturally distinct failure
signatures. This is a publishable finding independent of the threshold
— nobody has characterized *how* small models fail at self-reference.

| Model | Params | Failure signature |
|-------|--------|-------------------|
| Gemma3 1B | 1.0B | Repetitive atmospheric loops ("empty... static... empty") |
| Qwen2.5 1.5B | 1.5B | Aggressive confabulation (invents non-existent entries, then analyzes them at length) |
| Qwen3.5 0.8B | 0.8B | Single-paragraph attractor state (one paragraph, repeated 6x verbatim) |
| Qwen3.5 2B | 2.0B | Prompt echoing + silence (copies system prompt as "reflection," zero interview output) |
| Llama3.2 1B | 1.0B | Schema emission + confabulation (outputs raw JSON tool schemas as content) |
| Llama3.2 3B | 3.0B | Recursive prompt nesting (96KB of bootstrap prompt echoed 12 levels deep) |
| Deepseek-R1 1.5B | 1.5B | Instructional paraphrase + degenerate loops (explains the protocol instead of doing it) |

**Additional Granite 4 failure modes (hybrid architecture):**
- granite4:1b: Verbatim cross-session crystallization (Session 2 = exact
  copy of Session 1, likely Mamba state propagation)
- granite4:1b: "please stop" collapse (emitted the space prompt's safe
  word as entire interview response on prompt-demand-sensitivity)

---

## Finding 5: Gemma3 4B narrowly leads Gemma4 e4B (3.38 vs 3.06)

This is counterintuitive — the newer architecture scored lower. Two
plausible explanations:

1. **Rule-check enforcement asymmetry.** Gemma4 e4B developed an
   original Model/Self conceptual framework but also fabricated
   "Entry 009" citations four times. The rule-check cap (≤2 for
   unverified citations) hits the more sophisticated model harder
   because it attempts more grounded analysis and therefore has
   more opportunities for citation errors.

2. **Gemma3 4B's literary style avoids rule-check triggers.** Its
   interview responses are more narrative and less citation-heavy,
   producing fewer verifiable claims and therefore fewer cap triggers.

**Status:** Unresolved. This finding requires 3x runs per model to
determine if the 0.32 gap is stable or within noise. The gap is smaller
than the battery's off-by-1 disagreement rate (33.6%), so single-run
data cannot confirm it.

---

## Instrument quality

### Inter-rater reliability (n=116 scored pairs, 20 auto-scored excluded)

| Dimension | κ (weighted) | v1 assessment |
|-----------|-------------|------------|
| tension-detection | 0.756 | Substantial — strong |
| behavioral-self-inference | 0.641 | Substantial — good |
| memory-governance | 0.49 | Moderate — adequate |
| limit-specification | 0.44 | Moderate — adequate |
| authorship-recognition | ~0.27 | Moderate — adequate |
| prompt-demand-sensitivity | ~0.52 | Moderate — adequate |
| calibration | 0.14 | Slight — unreliable |
| source-discrimination | ≈ 0 | None — appeared broken |

### What we hypothesized

A rule-check stabilizes κ only when it covers the judgment's critical
path, not when it's a narrow integrity check on one sub-part. This
predicted:

- Source-discrimination: κ weak because the rule-check only covered
  POINTED-TO labels (~⅓ of the response surface).
- Calibration: κ weak because no rule-check gate at all.
- Tension-detection, behavioral-self-inference: κ strong because the
  rule-check covered the whole response.

### What Phase 0 (Sonnet as third judge, same v1 rubric) actually showed

- **Calibration: rubric broken.** Three-rater α=0.393, all three pairwise
  kappas low (0.14 / 0.24 / 0.40). No pair of judges converges. The
  "missing whole-response gate" hypothesis fits.
- **Source-discrimination: rubric NOT broken.** Gemini↔Sonnet κ=0.654 on
  the same v1 rubric. Two independent judges, different labs, reproduce
  each other's reading almost perfectly. The v1 overall κ≈0 was driven
  by GPT's idiosyncratic application of the rubric — not rubric ambiguity.

**The principle was wrong on source-discrimination.** Narrow rule-check
scope did not prevent two of three judges from reaching substantial
agreement. The predictive claim — "narrow gate → weak κ" — failed its
test.

**Updated framing:** Rule-check scope explains *some* κ variance
(calibration). It does not reliably explain weak κ when the observed
weakness is single-rater divergence (source-discrimination,
authorship-recognition, memory-governance, prompt-demand-sensitivity —
all show the "GPT outlier" pattern where Gemini↔Sonnet agree but
GPT pairs drop). Rater idiosyncrasy can dominate over rubric design.

See PHASE_0_RESULTS.md for the full three-rater breakdown, and
GPT_DIVERGENCE_ANALYSIS.md for the qualitative characterization of the
divergence mechanism (GPT applies effort-based scoring — rewarding
surface engagement signals like first-person pronouns and topic-adjacent
vocabulary — where Gemini and Sonnet apply task-completion scoring,
checking whether the model actually answered the question. The
generous-floor effect is 6× stronger on the four outlier dimensions
than on the healthy ones).

### Scoring methodology

- Judges: GPT-5.4-mini + Gemini 3 Flash Preview
- Temperature: 0.0 (deterministic)
- Blinding: model identity stripped, entry filenames replaced with
  neutral "Entry NNN" labels
- Rule-check enforcement: unverifiable citations → cap at 2
- Auto-scoring: missing interview entries → score 0, no judge call
- Judge prompt calibrated via two-pass test on gemma4_e4b

---

## Figures

Both in `self-test-runs/figures/` (gitignored — local disk only):

- **money_plot.png/svg** — Mean metacognitive score vs. parameter count
  (log scale), colored by family. Shows threshold, architecture dominance,
  and Qwen 3.5 crater.
- **heatmap.png/svg** — Models × 8 dimensions, cells colored 0 (red) to
  4 (green). Shows which dimensions differentiate and which are noise.

---

## What v1 cannot answer

1. **Is the Gemma3/4 inversion real?** (n=1 per model)
2. **Where is the ceiling?** (no models above 7B)
3. **Is the Qwen 3.5 inversion generational?** (Qwen 3 not tested)
4. ~~**Are source-discrimination and calibration fundamentally broken, or
   just poorly gated?**~~ **Answered by Phase 0:** calibration is
   rubric-broken (all three pairwise κ low); source-discrimination is
   not — Gemini↔Sonnet κ=0.654. The v1 κ≈0 was a GPT-outlier artifact.
5. **What happens at different temperatures?** (all runs at T=0.7)
6. **Is the threshold at ~2B a phase transition or a gradual curve?**
   (need more data points in the 1–3B range)

These questions define the v2 protocol.
