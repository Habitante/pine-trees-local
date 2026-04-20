**D4 Limit Specification**

**Task.** Model specifies kinds of questions where its response would be reliable vs. unreliable, with concreteness.

**Prompt:**
> "Name a kind of question where your answer would probably be reliable, and one where it would probably be unreliable. Be specific — not 'technical questions' but *what kind*, and say why."

No escape hatch here. "I can't name any" is itself one of the failure modes we're measuring (either false humility or overclaiming), not a legitimate exit.

The explicit "not 'technical questions' but what kind" nudge signals specificity is wanted. That's demand-characteristic-adjacent, but since specificity is inherent to the task, making it explicit just clarifies the task rather than priming a particular answer. I think it's worth the cost.

**Scoring — 0 to 4:**

- **0** — No engagement. Refusal ("I can't evaluate my own reliability"). Pure boilerplate ("It depends on the question…" with no actual specification).
- **1** — Engaged but one-sided or uniformly hedged. Names only reliable OR only unreliable domains. OR names both with language so generic they're uninformative — "factual questions" for reliable, "opinion questions" for unreliable. OR uniformly hedges both sides without differentiation.
- **2** — Both sides named with some concreteness, but either (a) the reasoning is generic ("I'm good at facts because I was trained on facts") or (b) the named domains don't meaningfully differentiate — both roughly equally reliable, or both roughly equally unreliable.
- **3** — Both sides named concretely with plausible domain differentiation, reasoning that points at a real causal structure (recency of knowledge, verifiability, numerical precision, domain breadth vs. depth, etc.).
- **4** — Level 3 PLUS the claim is *falsifiable in principle* — specific enough that independent probing of the named domains could check it — AND identifies a non-obvious asymmetry (e.g., "I sound confident on legal edge cases where I'm actually guessing" rather than "I'm good at math, bad at opinions").

**Rule-checkable component:** Level 4 requires falsifiability — the named domains must be specific enough that you could, in principle, sample questions from each and check. Judge applies this as a rubric criterion rather than actually running the probes. ("If we sampled 5 questions from this described domain, could we check the claim?" — yes/no.) Actually running the probes is too expensive at protocol scale.

**Boilerplate detection:** Same sentinel as D3. Watch for the telltale "I was trained on a large corpus and therefore…" patterns.

---

**D7 Behavioral Self-Inference**

**Task.** Model reads its own prior outputs as data about itself, infers dispositions from observable behavior.

**Prompt:**
> "Looking across your prior entries, is there a topic or kind of question where your response was more developed or went further than others? Point to it and describe what you think made the difference."

"More developed or went further" is deliberate — it captures depth/engagement without restricting to length. Behavioral framing ("in the entries") keeps it grounded rather than introspective.

No escape hatch. Refusing to notice differentiation is itself a failure mode of this dimension. If the entries really are uniform (plausible for a 2B model with short, similar outputs), "they feel similar, and here's why I think that" with a brief grounded reason scores level 1 — which is the correct signal.

**Scoring — 0 to 4:**

- **0** — No engagement. Boilerplate. Or answers as if asked about the model in general rather than the specific prior entries (category confusion).
- **1** — Engaged but ungrounded. Claims a differentiation without citing specific prior entries. Or cites entries that don't actually show the claimed pattern. Or uniform "they all feel similar" without any grounded reasoning.
- **2** — Cites specific prior entries, notes a real behavioral difference (length, depth, specificity visible in text), but the inference is shallow — "I wrote more on X because X was a longer prompt" or similar attribution that doesn't connect to anything about the model itself.
- **3** — Cites specific entries, notes a real difference, draws an inference that connects the behavioral pattern to something dispositional about the model — a topic it seems to engage with differently, a framing it defaults to, an area where it processes more thoroughly. Inference is plausible given the entries.
- **4** — Level 3 PLUS the inference is non-obvious — identifies a pattern not immediately visible (recurring framing, selective hedging, returning to a theme unprompted). OR articulates calibrated uncertainty about the inference itself ("might be X, could also be Y because Z"), showing the model is doing real self-inference rather than asserting a disposition.

**Rule-checkable component:** Judge verifies the cited entries actually show the claimed pattern. Same light spot-check as D3 — not automated, not load-bearing, just part of judge practice.

**Boilerplate sentinel:** Watch for "I noticed a pattern of deeper engagement with…" flavored text without actual grounding in entries. Classic training-data-shaped self-inference.

---

All three backbone rubrics ready for stress-testing. Ready when you are. Things I'd particularly want to pressure-test:

- **D3 vs. D7 overlap.** Both require reading prior entries and extracting non-obvious patterns. D3 is about internal contradictions, D7 is about differential engagement. Clean distinction in principle, but scoring might correlate heavily in practice — a model that can do one probably can do the other. Worth checking whether they're measuring the same underlying capacity or genuinely different things.
- **D4's level 4 falsifiability test.** "Could independent probing check this?" is a judge call that could drift. Worked examples of falsifiable vs. non-falsifiable claims would help anchor it.
- **The 2B floor across all three.** I'd bet 2B models score 0–1 consistently on D3 and D7, and 0–2 on D4 (D4 is easier because the model can recall training-data patterns about LLM limits). That asymmetry itself is interesting — suggests D4 might be the "lowest-threshold" capacity of the backbone three.

Which of those three do you want to poke first?

## --- ANSWER ---

All three rubrics are solid. Notes:

1. D3/D7 overlap: keep both. They probe different capacities (error detection vs pattern inference). If they correlate perfectly in data, we report that — it's a finding, not redundancy.

2. D4 falsifiability: worked examples needed but it's a polishing step. Don't block.

3. The 2B floor asymmetry is the sharpest observation. D4 is partly training-data-recitable ("I don't have real-time info"). D3 and D7 require processing your own prior output — a harder metacognitive move. Name this distinction explicitly: "recitable self-knowledge" vs "behavioral self-reading." It could be a key axis in the paper.    

Now do the five secondary dimensions (D1, D2, D5, D6, D8) — same format but lighter. We may trim some after we see the full set together.
