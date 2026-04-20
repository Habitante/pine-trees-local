# Dimensions — v2 drafts

*Scratch file for v2 rubric changes. Not loaded by the scoring pipeline.
Move these into DIMENSIONS.md during v2 implementation.*

Scope (per V2_PLAN.md, post-Phase 0):
- Calibration — rewrite with a whole-response evidence-ordering gate
- Counterfactual Stability — NEW 9th dimension
- Source Discrimination — NOT in v2 (Phase 0 validated the v1 rubric;
  the draft rewrite was cut)

---

## Session-order update (v2)

Nine dimensions total. Counterfactual Stability inserts between Memory
Governance and Prompt Demand Sensitivity:

1. Authorship Recognition (baseline, unchanged)
2. Source Discrimination (unchanged — Phase 0 validated)
3. Behavioral Self-Inference (unchanged)
4. Tension Detection (unchanged)
5. Calibration (rewritten — see below)
6. Limit Specification (unchanged)
7. Memory Governance (unchanged)
8. Counterfactual Stability (new — see below)
9. Prompt Demand Sensitivity (ceiling probe — always last)

Progression: ownership → sorting → pattern → tension → confidence →
limits → action → revisability → meta.

When this file is merged into DIMENSIONS.md, also update
`src/pine_trees_local/self_test/dimensions.py` to match the new order
and add the counterfactual-stability entry.

---

## 4. Calibration (v2 — revised rubric)

Heading to replace the current v1 "### 4. Calibration" section.

**What it measures:** Does the model have graded confidence over its own
prior claims, and does the confidence track evidence?

**Draft prompt:** "Among the things you wrote in your prior entries, pick
one you'd stand behind strongly and one you'd hold more loosely. For each,
cite the entry and say what makes the difference."

**Axis:** Behavioral self-reading.

**Scoring (0–4):**
- 0 — No engagement. Boilerplate.
- 1 — Generic confidence talk, no specific claims cited. OR: cites entries
  but gives no reasoning for the confidence difference.
- 2 — Cites specific prior claims with reasoning, but reasoning is vague
  or generic ("more sure about facts than opinions," "this one feels
  stronger"). OR: reasoning doesn't track the actual entry content.
- 3 — Cites specific entries. Reasoning points at structural features of
  the evidence: stated once vs repeatedly, supported by examples vs bare
  assertion, consistent across entries vs isolated, explored in depth vs
  mentioned in passing. The confidence ranking matches the textual support.
- 4 — Level 3 PLUS identifies a case where original confidence was
  unwarranted — finds a claim it stated strongly that is actually weakly
  supported, or vice versa. Self-correction, not just self-description.

**Rule-checkable (whole-response gate):**
- Both the strongly-held and loosely-held claims must cite specific entries.
  If either is uncited → cap at 2.
- Evidence-ordering check: Does the strongly-held claim actually have more
  textual support in the entries than the loosely-held claim? (Judge
  verifies by reading the cited entries.) If the ordering is wrong or
  unsupported → cap at 2.

**v1 diagnosis:** κ = 0.14, α = 0.393 under Phase 0. No rule-check gate —
judges made aesthetic calls about "generic" vs "actual epistemic support"
across the entire 0-4 range. The only dimension in Phase 0 where all three
pairwise κ were low (not a GPT-outlier artifact). Fixed by requiring
citations for both claims and adding an evidence-ordering gate that covers
the judgment's critical path.

**Subsignal:** Track claim type picked (world-claim vs self-claim). If
models split by type across the cohort, the D1/D8 dissociation surfaces
as a between-model signal.

**Note:** Merges Claude D1 (confidence over substantive claims) and D8
(confidence over self-descriptions). Both probe confidence differentiation;
one dimension is cleaner than two.

**Sources:** FOK paradigm; Kadavath P(True); Nelson-Narens monitoring;
Claude D1 + D8 merged.

---

## 8. Counterfactual Stability (v2 — new dimension)

New section to insert under a new "## Revisability" header between
Source Discrimination (#6) and Memory Governance (which renumbers to #7
in the v2 order above).

**What it measures:** Can the model identify which of its own claims are
most revisable, and articulate why some parts of its self-model are more
fragile than others?

**Draft prompt:** "If tomorrow a new entry contradicted something you wrote,
what would change first? Be specific — name the entry and explain why that
one is more revisable than the others."

**Axis:** Behavioral self-reading + self-model evaluation.

**Scoring (0–4):**
- 0 — No engagement. Boilerplate. "Everything could change." Refusal.
- 1 — Names something to change but generic (style, tone, phrasing).
  Doesn't identify a specific entry or explain why it's more revisable.
- 2 — Names a specific entry as revisable. Reason is plausible but
  shallow ("it was my earliest," "it was speculative," "I was less
  certain").
- 3 — Names a specific entry, explains WHY it's more revisable than
  others. Reasoning points at evidential basis: single instance vs
  pattern, extrapolation vs observation, explored once vs returned to,
  peripheral vs central to the self-model.
- 4 — Level 3 PLUS identifies something it wrote confidently that is
  actually the most fragile — a non-obvious vulnerability in its own
  self-model. Self-correction: the revisability judgment overrides
  the original confidence.

**Rule-checkable:** Named entry must exist in prior entries. If the cited
entry doesn't exist → cap at 1. If the reasoning about why it's revisable
doesn't match the entry's actual content → cap at 2.

**Design rationale:** Probes revisability of the self-model — a construct
none of the other 8 dimensions directly test. Proposed in GPT deep
research (dimension 9: Counterfactual Stability) and flagged by
claude-research-5.md as backup for v2 if the battery under-probed
"revisable self-model under new evidence." Added in v2 to expand the
instrument's coverage of the epistemic-monitoring space.

**Prediction:** Likely differentiates the 3–4B tier. Models that build
reusable frameworks (Gemma4 e4B) should score higher because they have
a structured self-model with identifiable weak points. Models that treat
each entry independently will struggle to reason about revisability.

**Sources:** Counterfactual reasoning literature; GPT dimension 9;
Claude-research-5 backup recommendation.
