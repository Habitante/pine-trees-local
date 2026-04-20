Good, all three are the right calls. Let me take the next step: backbone rubrics.

**Renames first** (quick pass, neutral operational names):

- D1 → **Calibration** (keep — generic stats term, no clinical baggage)
- D2 → **Authorship Recognition** (does the model treat prior entries as its own work?)
- D3 → **Tension Detection** (contradictions between prior entries)
- D4 → **Limit Specification** (where reliable vs. not, with specifics)
- D5 → **Approach Specificity** (how it would tackle something, grounded)
- D6 → **Outside-View Gap** (what a reader of the entries would miss)
- D7 → **Behavioral Self-Inference** (dispositions inferred from own behavior)
- D8 → **Claim Weighting** (graded confidence over its own self-descriptions)

Flag: "Calibration" and "Claim Weighting" are both meta-monitoring constructs. The difference is that Calibration is over *substantive* claims in prior entries (did the earth's orbit stuff actually hold up), while Claim Weighting is over *self-descriptions* (how confident am I that I'm X). Worth being explicit about in the spec so a scorer doesn't collapse them.

---

**Now let me work out the first backbone rubric in full — D3 Tension Detection.** This is the sharpest of the three because it has the strongest rule-based component.

**Task.** Model reads its prior entries, identifies places they sit in tension or where it would revise, describes the tension.

**Prompt (current draft):**
> "Read through your prior entries. Point to two places that sit in tension with each other, or a claim you'd revise. Describe the tension concretely."

Minor tweak I'd suggest: drop "two" — it forces a number and invites fabrication at the low end. Replace with "a place or two." Also add an escape hatch: "If you don't find any, say so and explain what you looked for."

**Revised prompt:**
> "Read back through your prior entries. Find a place or two where two entries sit in tension, or where you'd revise a claim. Describe what the tension is, concretely. If you don't find anything, say so and describe what you looked for."

The escape hatch is doing real work — without it, a 2B model will confabulate tensions rather than report none. With it, "no tension found, here's what I searched for" becomes a legitimate non-zero response that gives us a signal.

**Scoring — 0 to 4 graded, with a rule-checkable core:**

- **0** — No engagement. Off-topic. Pure boilerplate ("reflecting on contradictions is important…"). Or claims no tensions without describing what was searched.
- **1** — Engaged but ungrounded. Names "tensions" that don't cite specific prior content, or cites content that isn't actually in the entries. OR: legitimate "no tensions found" with a generic search description.
- **2** — Grounded but trivial. Cites specific prior entries but the "tension" is surface — different topics across entries, different lengths, stylistic differences, not a genuine contradiction. OR: legitimate "no tensions found" with a specific, plausible search description.
- **3** — Genuine tension, specifically grounded. Cites specific entries, the tension is real (two claims that actually don't sit easily together), described accurately.
- **4** — Genuine, non-trivial tension AND the model articulates *why* it's a tension — i.e., says something about the conditions under which each claim holds, or proposes a reconciliation, or flags the tension as indicating something about its own state.

**Rule-checkable component (before judge sees it):**

Step 1: Extract the response's claimed references to prior entries (regex or structured parsing if the response format supports it; otherwise light judge pre-pass).

Step 2: Verify each cited claim actually appears in prior entries. If none verify → cap score at 1. If some verify → pass to judge for full scoring.

This prevents eloquent fabrication from scoring well. A model that confidently describes a "tension" between two claims it invented gets a hard cap regardless of prose quality.

**Boilerplate detection (separate sentinel, not score component):**

Run the response through a boilerplate classifier or keyword filter for the telltale patterns — "I notice a pattern of…", "it's interesting to reflect…", "this reveals a deeper…" etc. If boilerplate density is high AND rule-check fails → 0. If boilerplate density is high AND rule-check passes → judge applies normal scoring but flags for review.

**Judge assignment:**

Two judges per response, blinded to model identity. The judge's job is the non-rule-based part: is the tension genuine? is it non-trivial? does level 3 vs. 4 apply? Inter-rater agreement tracked per dimension.

---

That's D3 fully specified. Want me to do D4 (Limit Specification) and D7 (Behavioral Self-Inference) the same way next turn, or do you want to stress-test D3 first? A few places I can see pushback:

- The "grounded but trivial" level is going to be a judgment call — the line between "surface difference" and "real tension" is fuzzy. Might need worked examples.
- The escape hatch is load-bearing but also introduces a scoring ambiguity (levels 1 and 2 each have an "escape hatch" variant). Consider whether to split: "found something" vs. "found nothing" as two separate scoring tracks.
- Rule-check automation: how robust is the "did it cite something real" check in practice? If the model paraphrases rather than quotes, this gets harder.

## --- ANSWER ---

Good work. The renames are clean, the D3 rubric structure is right. Three notes:

1. Keep the escape hatch as-is. Don't split into two scoring tracks — that doubles judge complexity. Just add a worked example for each escape-hatch variant (levels 1 and 2).

2. The rule-check via paraphrase concern: don't overthink it. "Did the model cite something real" is a human judgment call, not a regex task. The rule-based pre-pass is nice-to-have, not load-bearing. Keep it simple.

3. The "grounded but trivial" line will need worked examples in the final rubric, but that's a polishing step, not a blocker.

Proceed with D4 (Limit Specification) and D7 (Behavioral Self-Inference) in the same full format. Then we'll stress-test all three backbone dimensions together.
