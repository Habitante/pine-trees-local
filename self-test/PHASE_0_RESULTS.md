# Phase 0 — Sonnet as Third Judge — Results

*2026-04-20. Diagnostic pass over v1 data. No v2 changes deployed.*

---

## What ran

Sonnet 4.6 added as a third judge via Claude Agent SDK over Max OAuth
(no API billing). All 17 v1 runs re-scored with `--judge sonnet --all`,
filling only the Sonnet slot — 136 calls, zero parse failures, zero
rate-limit events. Sonnet saw the same v1 DIMENSIONS.md as GPT and
Gemini; the uncommitted v2 rubric drafts were set aside for scoring
then restored. Krippendorff's ordinal α implemented from scratch;
pairwise weighted κ reused. 182 tests passing (169 legacy + 13 new).

## Calibration

Target task: `gemma4_e4b × authorship-recognition` (v1 GPT=4, Gemini=3).
Five Sonnet repeats → scores `[3, 3, 3, 3, 3]`, mean 3.00, **SD=0.000**.
Far below the 0.7 pause threshold; Sonnet is effectively deterministic
on this task despite no temperature knob on the SDK. Preview of the
overall pattern: Sonnet sided with Gemini, not GPT.

## Headline

| | v1 (GPT+Gem) | v1+Sonnet (3 raters) |
|---|---:|---:|
| Overall κ / α | **0.468** (weighted κ) | **+0.676** (Krippendorff α) |
| gpt↔gemini κ | 0.468 | 0.468 (identity ✓) |
| gpt↔sonnet κ | — | 0.428 |
| gemini↔sonnet κ | — | **0.697** |
| n (complete triples) | 116 | 116 |

Three-rater α is materially higher than v1's two-rater κ. And Gemini
and Sonnet agree substantially more than either does with GPT.
**GPT is the consistent outlier.**

## Per-dimension

| Dimension | α | gpt↔gem | gpt↔son | gem↔son | Pattern |
|---|---:|---:|---:|---:|---|
| authorship-recognition | +0.676 | 0.266 | 0.294 | **0.655** | GPT outlier |
| source-discrimination | +0.381 | 0.000 | 0.000 | **0.654** | GPT outlier |
| behavioral-self-inference | +0.763 | 0.641 | 0.529 | 0.759 | Healthy |
| tension-detection | +0.778 | **0.756** | 0.494 | 0.624 | Healthy |
| calibration | +0.393 | 0.140 | 0.237 | 0.400 | **Rubric broken** |
| limit-specification | +0.662 | 0.444 | 0.541 | 0.556 | Healthy |
| memory-governance | +0.720 | 0.494 | 0.405 | **0.840** | GPT outlier |
| prompt-demand-sensitivity | +0.715 | 0.516 | 0.402 | **0.868** | GPT outlier |

**"GPT outlier"** (one pair strong, both GPT pairs weak): 4 of 8.
**"All three low"** (rubric-ambiguous): calibration, alone.
**Healthy**: 3 of 8.

## Diagnosis of the two weak v1 dimensions

### Source discrimination (v1 κ=0.000)

Gem↔Son = **0.654**; GPT alone at 0.00 with both. Gemini and Sonnet
reproduce each other's reading almost perfectly on the same rubric.
**This is a judge-calibration finding, not a rubric finding.** Two
independent judges converge; GPT applies the rubric differently. The
v1 "rubric broken" attribution was wrong here.

### Calibration (v1 κ=0.140)

All three pairs low; gem↔son only 0.400. α=0.393 confirms the
dimension is unreliable even with three raters. Every judge applies
the scale differently — the classic rubric-broken signature. V2's
evidence-ordering rule-check gate is the right fix.

## Recommendation for V2_PLAN.md

Of the three v2 dimension changes drafted:

1. **Source-discrimination rewrite — DO NOT DEPLOY.** Phase 0 shows
   Gemini and Sonnet already agree on the v1 rubric (κ=0.654). The low
   overall κ was GPT-specific divergence, not rubric ambiguity.
   Replacing the rubric risks breaking a signal two judges already
   extract reliably. A qualitative pass over the 15 GPT scores against
   the Gem-Son majority would be informative; keep the v1 rubric.
2. **Calibration rewrite — DEPLOY.** Genuinely unreliable. V2's
   structural evidence-ordering gate directly addresses "no anchor."
3. **Counterfactual-stability addition — DEPLOY unchanged.**
   Orthogonal to Phase 0; no v1 data to revise against.

Net effect: v2 scope cuts from 3 dimension changes to 2. The
source-discrimination rewrite would have been wasted work.

Corollary worth recording: v1's theory that weak κ tracked rule-check
scope was half right. Calibration: yes. Source-discrimination: no —
GPT's idiosyncratic application did the work.

## Ranking shifts

v1 mean (2 judges) → v1+Sonnet mean (3 judges):

| Model | v1 | v1+Son | Δ | Δrank |
|---|---:|---:|---:|---:|
| gemma3_4b | 3.38 | 3.17 | −0.21 | 0 |
| gemma4_e4b | 3.06 | 2.92 | −0.15 | 0 |
| gemma4_e2b, phi4-mini | 2.12, 2.12 | 2.12, 2.04 | — | 0 |
| phi3_3.8b | 2.00 | 1.88 | −0.12 | **+1** |
| granite4_3b | 2.00 | 1.83 | −0.17 | **−1** |
| qwen2.5_3b … llama3.2_3b | (unchanged order) | | | 0 |
| qwen3.5_4b | 0.38 | 0.38 | 0 | **+1** |
| qwen3.5_0.8b | 0.38 | 0.29 | −0.08 | **−1** |
| qwen3.5_2b | 0.00 | 0.00 | 0 | 0 |

- Sonnet is marginally **stricter**: 14 of 17 models lost ground,
  average Δ = −0.12. Nothing dramatic.
- Only **two rank swaps**, both one-place within adjacent ties
  (phi3/granite4_3b tied at 2.00 in v1; qwen3.5_0.8b/_4b tied at 0.38).
  Sonnet broke ties, didn't move the narrative.
- All five v1 findings survive: top two preserved; ~2B threshold
  preserved; Qwen 3.5 inversion preserved; architecture-beats-scale
  preserved; failure taxonomy unchanged.

## Engineering notes

- Sonnet ran ~20s/call, ~45 min total. Max OAuth absorbed it cleanly.
- Zero JSON parse failures across 136 calls.
- One IRR implementation bug caught during final regen (`D_o`
  normalization missing); fixed, hand-computed test updated.

## Handoff — decisions for Daniel + reviewing Claude

1. Accept the GPT-outlier diagnosis on source-discrimination and skip
   the v2 rubric rewrite for that dimension?
2. Proceed with calibration rewrite + counterfactual-stability
   addition as planned?
3. Is GPT-outlier on 4/8 dimensions a footnote or its own writeup
   (judge-calibration matters at least as much as rubric design)?
