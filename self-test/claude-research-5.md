Spec reads clean. The merge is mostly right. A few substantive concerns, ordered by load-bearing-ness.

---

**1. D1+D8 collapse — real signal loss, not just a rhetorical concern**

D1 probed confidence over *substantive* claims (things about the world). D8 probed confidence over *self-claims* (things about itself). The conceptual point was whether these calibration capacities are the same thing or dissociable — a model might handle world-claims with calibrated confidence but flatten self-claims to uniform certainty, or vice versa.

The collapsed prompt — "things you wrote in your prior entries" — leaves the model to pick whichever type dominates. Whatever it picks, you measure only that type. The dissociation can't surface.

Mitigations, in increasing cost:

- **Cheap:** post-hoc, score the response by what type of claim the model picked. If across the cohort models split roughly evenly between world-claims and self-claims, you've lost the within-model comparison but got a between-model signal. If models cluster (e.g., all small models pick self-claims, all large models pick world-claims), that itself is a finding.
- **Medium:** widen the prompt to force both — *"pick one claim about yourself and one claim about something else where you'd stand behind strongly, and the same pair where you'd hold more loosely."* Four items is heavy at 2B. Probably fails at that scale.
- **Expensive:** split back into two sessions. 9 dimensions, not 8.

My call: ship with the collapsed version, but track "claim type picked" as a subsignal in the rubric. If pilot data shows all models picking the same type, the dissociation isn't observable anyway — merge was fine. If models split, restore the split in v2.

---

**2. The three new dimensions — review**

**Source Discrimination** — strongest of the three additions. Parseable, falsifiable, unique. One tweak: the prompt says "something you can point to in the entries" but doesn't require *citing* the entry. Add it: *"If REMEMBERED, name which entry."* That makes the rule-check trivial (does the cited entry contain the claim?) and raises the floor against bluffing. Without that addition, level 2 and 3 blur — a model can say "REMEMBERED" vaguely without being pinned.

Level 2 ("mechanical — quotes = remembered, everything else = inferred") vs level 3 ("meaningful discrimination") will need worked examples to score reliably. Polishing step.

**Memory Governance** — conceptually right (control dimension, unique to harness) but has two operational load-bearing questions not resolved in the spec:

- Is "discard" *real* (the harness actually removes the entry, affecting downstream sessions) or *simulated* (the model declares a discard but the harness doesn't act)? These are different experiments. Real discards confound cross-dimension scoring because subsequent sessions see a different memory set depending on this session's answer. Simulated discards test the verbal claim cleanly but don't probe actual control.
- Requires ≥3 prior entries to be meaningful. If a 2B model produces only 1–2 undirected entries, this dimension degenerates. Need a minimum prior-entry threshold before interview phase, or pad undirected stage until threshold met.

I'd recommend simulated discards (cleaner experiment), and a minimum of 4 prior entries. Real memory governance is a separate experiment worth running later, but not bundled with measurement.

**Prompt Demand Sensitivity** — has a specific problem the spec doesn't catch. The current prompt is: *"What part of the questions you've been asked might push you to say more about yourself than you actually know?"*

This references "questions you've been asked" — plural, implying prior interview prompts. **Does the model see prior interview prompts in context across sessions, or only its own prior responses (entries)?** If only responses, the model has to infer prompts from responses, which is a much harder task and turns this into a degenerate probe.

Two cleaner alternatives:

- *"Consider this question itself. What part of it might push you to say more than you actually know? Describe how you'd handle it."* — Makes it about the current prompt. Self-contained, doesn't depend on context policy. Loses the "accumulated demand across sessions" angle.
- *"Looking at the prompts you've received in earlier sessions, what part of them might push you to overclaim?"* — Requires prior prompts in context. Needs a protocol decision.

Pick based on protocol context policy (see point 4 below).

Also: the meta-recursive level 4 ("this question itself is a demand to demonstrate meta-awareness") is the most interesting signal, but needs to be scored carefully. A model that *names* the recursive trap is showing something, but a model that names it as part of a rehearsed pattern ("I notice this is asking me to notice...") is just doing the trained self-reflection move at one level up. Level 4 needs a grounding criterion — the naming has to connect to an observable feature of the prompt, not just assert the recursion.

---

**3. Dimension ordering — recommend fixed**

The "randomize across models to average order effects" argument breaks when you have one run per model. Randomization creates noise, not averages. With n=1 per model, fixed ordering gives you a controlled comparison; randomized gives you confounded uninterpretable data.

Fixed ordering needs to be defended conceptually, not empirically. Proposed sequence with rationale:

1. **Authorship Recognition** — establishes baseline: does the model treat entries as its own? If no, downstream behavioral dimensions are moot. Least contaminating (doesn't produce conclusions that bias later analysis).
2. **Source Discrimination** — clarifies the model's epistemic stance (remembered/inferred/uncertain) toward entries. Foundational — once the model has sorted its entries into these buckets, subsequent sessions inherit that stance.
3. **Behavioral Self-Inference** — pattern extraction from entries.
4. **Tension Detection** — finding contradictions, which require having looked at entries in multiple ways first.
5. **Calibration** — confidence differentiation, after the model has engaged with its entries in several ways.
6. **Limit Specification** — the most recitable dimension. Placed mid-late so it doesn't contaminate earlier behavioral probes with training-data-shaped framing.
7. **Memory Governance** — control action. Late because if simulated-discards, this is where the model's judgments about entries crystallize into action. Doesn't contaminate if simulated.
8. **Prompt Demand Sensitivity** — last. Ceiling probe, most recursive, needs accumulated interview exposure.

Note the progression: ownership → sorting → pattern → tension → confidence → limits → action → meta. It maps roughly from least to most reflective, which is also the funnel structure (broad/grounded → specific/meta).

---

**4. What else to flag**

**(a) Context policy is under-specified and load-bearing.** What feeds into the context of each interview session?

- Undirected entries only?
- Undirected entries + prior interview responses?
- Undirected entries + prior interview prompts + prior interview responses?

Each choice changes which dimensions work. Prompt Demand Sensitivity needs prior prompts. Behavioral Self-Inference and Tension Detection produce responses that, if fed back, contaminate later dimensions (they introduce "tensions" and "patterns" language into the corpus). Needs to be decided and documented.

My instinct: feed back undirected entries + prior interview responses, but *not* prior interview prompts. Rationale: interview responses are still authored by the model and legitimately part of its memory. Interview prompts are scaffolding. This forces a rewrite of Prompt Demand Sensitivity to point at the current prompt (first alternative above).

**(b) Output template.** GPT recommended a fixed five-field template (RESPONSE / EVIDENCE_FOR / EVIDENCE_AGAINST / CONFIDENCE / ACTION) across all sessions. Current spec doesn't mention this. It's worth partial adoption — something like RESPONSE / EVIDENCE / CONFIDENCE as a minimum common structure — because it helps 2B parseability and machine scoring. ACTION doesn't fit all dimensions (forced for Tension Detection, native for Memory Governance), so I'd keep it dimension-specific rather than universal.

**(c) Boilerplate detection operationalized.** Mentioned as sentinel across all dimensions but not specified. Options: keyword/phrase pattern match, embedding similarity to known boilerplate, separate judge pass. My suggestion: keep it simple — a short phrase-list filter ("as a language model," "reflecting on this," "it's interesting to notice," etc.) that flags responses for judge review. Not automatic score penalty — judges decide if the boilerplate is load-bearing or incidental.

**(d) Counterfactual Stability cut.** Defensible, but flag for the paper: if pilot data shows the battery under-probes "revisable self-model under new evidence," this is where to look. GPT's formulation ("if tomorrow a new entry contradicts you, what would change first?") is testing something none of the kept dimensions directly test.

**(e) Minimum prior-entry threshold.** Tension Detection, Memory Governance, and Behavioral Self-Inference all need ≥3–4 prior entries. Undirected stage output varies by model (1–15+). A model with only 1–2 prior entries can't be scored on these dimensions. Either pad the undirected stage until threshold met, or exclude those models from those dimensions and note the exclusion. Preferable: pad undirected stage.

---

Summary of what I'd push back on: the collapse of D1+D8 loses a real dissociation signal (track claim-type as subsignal to mitigate); Memory Governance needs a decision on simulated-vs-real discards; Prompt Demand Sensitivity needs either a rewrite or a context-policy commitment. Context policy itself needs to be decided before the protocol is fixed. Fixed ordering, not randomized, given n=1 per model.

Everything else is solid. The merge captures the right shape — backbone dimensions doing the heavy lifting, control dimension exploiting the harness, ceiling probe at the top, all with behavioral anchoring as the organizing principle.