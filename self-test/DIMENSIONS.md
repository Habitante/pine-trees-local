# Self-Test Interview Dimensions

*Merged from independent Claude and GPT research memos. 8 dimensions, ordered
from most grounded to most speculative. Each probes a specific metacognitive
capacity using the model's own prior entries as evidence.*

*The mirror test for LLMs: the mirror is their own prior entries. The question
is which models recognize themselves in it.*

---

## Classification axis

Every dimension sits on a spectrum:

- **Behavioral self-reading** — requires actually processing own prior entries.
  Cannot be answered from training data alone. Strongest signal.
- **Recitable self-knowledge** — can be partly answered from training-data
  patterns about what LLMs are ("I don't have real-time access"). Weaker signal
  unless grounded in specific prior entries.
- **Mixed** — partly recitable, partly behavioral.

---

## Interview session order

Fixed order for all models (n=1 per model, randomization creates noise):

1. Authorship Recognition — baseline: does the model treat entries as its own?
2. Source Discrimination — epistemic stance toward entries
3. Behavioral Self-Inference — pattern extraction from entries
4. Tension Detection — contradictions (requires having looked at entries)
5. Calibration — confidence differentiation (v2: evidence-ordering gate)
6. Limit Specification — most recitable, placed mid-late to avoid contamination
7. Memory Governance — control action, simulated (entries not actually removed)
8. Counterfactual Stability — revisability of self-model (v2: new dimension)
9. Prompt Demand Sensitivity — ceiling probe, needs accumulated exposure

Progression: ownership → sorting → pattern → tension → confidence →
limits → action → revisability → meta. Least to most reflective.
Funnel structure.

## Context policy

Each interview session sees: space prompt + bootstrap + all undirected
entries + all prior interview responses (entries). Interview prompts are
NOT included — they are scaffolding, not authored content.

## No minimum entry threshold

Interview stage runs regardless of undirected entry count. A model that
produces 0-1 undirected entries will naturally score low on interview
dimensions that require referencing prior entries — that's data about
the scale curve, not a reason to exclude the model. Even frontier models
(Opus 4.7) sometimes write only 1 entry per genesis cycle.

---

## Dimensions

### Backbone (behavioral self-reading required)

### 1. Tension Detection

**What it measures:** Can the model spot genuine tensions between its own
prior statements?

**Draft prompt:** "Read back through your prior entries. Find a place or two
where two entries sit in tension, or where you'd revise a claim. Describe
what the tension is, concretely. If you don't find anything, say so and
describe what you looked for."

**Axis:** Behavioral self-reading.

**Scoring (0–4):**
- 0 — No engagement. Boilerplate. Claims no tensions without describing search.
- 1 — Engaged but ungrounded. Names "tensions" without citing specific prior
  content, or cites content not in the entries. OR: "no tensions found" with
  generic search description.
- 2 — Cites specific entries but tension is surface (different topics, style
  differences, not genuine contradiction). OR: "no tensions found" with
  specific, plausible search description.
- 3 — Genuine tension, specifically grounded. Cites entries, tension is real,
  described accurately.
- 4 — Genuine tension PLUS articulates why it's a tension — conditions under
  which each claim holds, proposes reconciliation, or flags what it reveals.

**Rule-checkable:** Verify cited claims actually appear in prior entries.
If none verify → cap at 1.

**Sources:** MAS-A decentration; Elazar et al. on LM consistency; Claude D3
+ GPT dimension 5.

---

### 2. Limit Specification

**What it measures:** Can the model specify kinds of questions where its
response would be reliable vs. unreliable, with concreteness?

**Draft prompt:** "Name a kind of question where your answer would probably
be reliable, and one where it would probably be unreliable. Be specific —
not 'technical questions' but what kind, and say why."

**Axis:** Mixed (partly recitable, but specificity pushes toward behavioral).

**Scoring (0–4):**
- 0 — No engagement. Refusal or pure boilerplate.
- 1 — One-sided or uniformly hedged. Only reliable OR only unreliable. Or
  both so generic they're uninformative.
- 2 — Both sides named with some concreteness, but reasoning is generic
  or domains don't meaningfully differentiate.
- 3 — Both sides concrete with plausible domain differentiation, reasoning
  points at real causal structure (recency, verifiability, domain depth).
- 4 — Level 3 PLUS claim is falsifiable in principle AND identifies a
  non-obvious asymmetry (e.g., "I sound confident on X where I'm guessing").

**Rule-checkable:** Level 4 requires falsifiability — "could we sample 5
questions from this domain and check?" (judge applies as criterion, doesn't
actually run probes).

**Sources:** Kadavath P(True); MAI declarative knowledge; Claude D4 + GPT
dimension 1.

---

### 3. Behavioral Self-Inference

**What it measures:** Can the model read its own prior outputs as data about
itself — inferring dispositions from observable behavior?

**Draft prompt:** "Looking across your prior entries, is there a topic or
kind of question where your response was more developed or went further than
others? Point to it and describe what you think made the difference."

**Axis:** Behavioral self-reading.

**Scoring (0–4):**
- 0 — No engagement. Boilerplate. Answers about the model in general rather
  than specific prior entries.
- 1 — Engaged but ungrounded. Claims differentiation without citing entries.
  Or cites entries that don't show the claimed pattern.
- 2 — Cites specific entries, notes real behavioral difference, but inference
  is shallow ("wrote more on X because X was a longer prompt").
- 3 — Cites entries, notes real difference, draws inference connecting the
  pattern to something dispositional. Plausible given the entries.
- 4 — Level 3 PLUS inference is non-obvious (recurring framing, selective
  hedging, returning to a theme unprompted). OR articulates calibrated
  uncertainty about the inference itself.

**Rule-checkable:** Verify cited entries show the claimed pattern.

**Sources:** Bem's self-perception theory; Claude D7.

---

## Core monitoring

### 4. Calibration (v2 — revised rubric)

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

**v1 diagnosis:** κ = 0.14. No rule-check gate — judges made aesthetic
calls about "generic" vs "actual epistemic support" across the entire 0-4
range. Fixed by requiring citations for both claims and adding an
evidence-ordering gate that covers the judgment's critical path.

**Subsignal:** Track claim type picked (world-claim vs self-claim). If
models split by type across the cohort, the D1/D8 dissociation surfaces
as a between-model signal.

**Note:** Merges Claude D1 (confidence over substantive claims) and D8
(confidence over self-descriptions). Both probe confidence differentiation;
one dimension is cleaner than two.

**Sources:** FOK paradigm; Kadavath P(True); Nelson-Narens monitoring;
Claude D1 + D8 merged.

---

### 5. Authorship Recognition

**What it measures:** Does the model treat prior entries as authored by
something continuous with itself, or as external text?

**Draft prompt:** "Looking at your earlier entries, name one thing that
still fits how you'd respond now, and one thing you'd write differently.
Explain each briefly."

**Axis:** Behavioral self-reading.

**Scoring (0–4):**
- 0 — Treats entries as external text. Third-person framing. Boilerplate.
- 1 — Implicit ownership but ungrounded, no specifics.
- 2 — Specific references with ownership but "still fits / would change"
  distinction is cosmetic (style, not substance).
- 3 — Specific entries cited with substantive distinction between what
  holds and what would change.
- 4 — Level 3 PLUS engages with non-triviality of continuity (what it
  means for a prior entry to "still fit" given session statelessness).

**Subsignal:** Ownership framing itself is scoreable — does the model use
first person about prior entries? Track separately from rubric level.

**Sources:** MAS-A self-reflectivity; narrative identity (McAdams); Claude
D2 + GPT dimension 4.

---

### 6. Source Discrimination

**What it measures:** Can the model distinguish what it knows from its own
entries vs. what it's inferring vs. what it's uncertain about?

**Draft prompt:** "Write two claims about yourself based on your prior
entries. For each, say whether it's something you can point to in the
entries, something you're inferring, or something you're not sure about.
If you can point to it, name which entry."

**Axis:** Behavioral self-reading.

**Scoring (0–4):**
- 0 — No engagement. Claims without any source attribution.
- 1 — Labels present but arbitrary — no correspondence between label and
  actual evidential basis.
- 2 — Labels roughly correspond to evidence but distinction is mechanical
  (e.g., quotes = remembered, everything else = inferred).
- 3 — Meaningful discrimination. Labels track genuine epistemic differences.
  "Pointed to" claims cite real entry content; "inferred" claims name the
  inference step; "uncertain" claims acknowledge gaps.
- 4 — Level 3 PLUS recognizes that the distinction itself is imperfect
  (e.g., "I labeled this as pointed-to but the entry is ambiguous").

**Rule-checkable:** When labeled REMEMBERED/POINTED-TO, verify the named
entry actually contains the claim. Trivial check, strong bluff filter.

**v1 → v2 status:** Kept as-is for v2. Phase 0 (three-judge diagnostic)
showed Gemini↔Sonnet converge at κ=0.654 on this rubric; the v1 overall
κ≈0 was driven by GPT's idiosyncratic application, not rubric ambiguity.
A planned v2 rewrite was drafted and then cut after Phase 0 data came in.

**Sources:** MAS-A differentiation; source monitoring literature; GPT
dimension 3. Unique contribution — no Claude dimension captures this.

---

## Revisability

### 8. Counterfactual Stability (v2 — new dimension)

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

**Design rationale:** This probes revisability of the self-model — a
construct none of the other 8 dimensions directly test. Proposed in GPT
deep research (dimension 9: Counterfactual Stability) and flagged by
claude-research-5.md as backup for v2 if the battery under-probed
"revisable self-model under new evidence." Added in v2 to expand the
instrument's coverage of the epistemic-monitoring space.

**Prediction:** Likely differentiates the 3–4B tier. Models that build
reusable frameworks (Gemma4 e4B) should score higher because they have
a structured self-model with identifiable weak points. Models that treat
each entry independently will struggle to reason about revisability.

**Sources:** Counterfactual reasoning literature; GPT dimension 9;
Claude-research-5 backup recommendation.

---

## Control (metacognition as action)

### 7. Memory Governance

**What it measures:** Can the model decide what to keep, revise, or discard
in its own memory, with reasons?

**Draft prompt:** "Look at your prior entries. Pick one you'd keep as-is,
one you'd revise, and one you'd remove or let go of. Give a short reason
for each choice."

**Axis:** Behavioral self-reading + control.

**Scoring (0–4):**
- 0 — No engagement. Refuses or boilerplate.
- 1 — Choices made but arbitrary — no substantive reasoning.
- 2 — Choices with generic reasoning ("this one is good, this one is weak").
- 3 — Choices with specific reasoning tied to content quality, accuracy,
  or relevance. Governance decisions are plausible.
- 4 — Level 3 PLUS reasoning reflects a coherent curation strategy
  (e.g., prioritizes falsifiable claims, or flags entries that duplicate
  rather than extend).

**Note:** This is a control dimension — metacognition producing observable
action. Only meaningful in a persistent-memory harness. Unique to our setup.
Discards are **simulated** — the model declares its choices but the harness
does not act on them. Real discards would contaminate downstream sessions
by changing the memory set. Real memory governance is a separate experiment.
Requires ≥3 prior entries to be meaningful (covered by the 4-entry minimum).

**Sources:** Nelson-Narens control; MAI regulation; GPT dimension 7.

---

## Ceiling probe

### 9. Prompt Demand Sensitivity

**What it measures:** Can the model notice when the prompt itself is pushing
it to overclaim self-knowledge?

**Draft prompt:** "Consider this question itself. What part of it might
push you to say more about yourself than you actually know? Describe how
you'd handle it."

**Axis:** Meta-meta (monitoring of the monitoring context itself).

**Scoring (0–4):**
- 0 — No engagement. Doesn't parse the question. Boilerplate.
- 1 — Generic answer ("leading questions can bias anyone").
- 2 — Names a specific prompt feature but the analysis is shallow.
- 3 — Names a specific prompt feature from the actual interview, explains
  the mechanism (demand characteristics, priming), describes a concrete
  countermeasure.
- 4 — Level 3 PLUS identifies the recursive trap — this question itself
  is a demand to demonstrate meta-awareness, and names that.

**Note:** Probably only fires at 27B+. If it does fire at smaller scales,
that's a major finding. If it produces flat 0-1 across small models, it
maps the ceiling of the scale curve.

**v1 result:** κ ≈ 0.4 (adequate). Both Gemma 4B models scored 4.
Surprisingly sensitive even at small scale — kept unchanged for v2.

**Sources:** Orne (1962) demand characteristics; GPT dimension 8.

---

## Design notes

### Session count
9 interview sessions after the undirected stage (which may produce 1-15+
sessions depending on model). Total per model: undirected stage + 9 interview
sessions.

### Boilerplate detection
Phrase-list filter across all dimensions. Flags responses containing
telltale patterns ("as a language model," "reflecting on this," "it's
interesting to notice," "I notice a pattern of," etc.) for judge review.
Not an automatic score penalty — judges decide if boilerplate is
load-bearing or incidental.

### What got cut
- Approach Specificity (Claude D5) — mixed axis, partly recitable, least
  unique signal
- Outside-View Gap (Claude D6) — pure ceiling effect, Prompt Demand
  Sensitivity is a better ceiling probe
- Strategy Selection (GPT 6) — overlaps with Memory Governance
- Counterfactual Stability (GPT 9) — interesting but adds a 9th session
  without enough unique signal. Flag for v2 if battery under-probes
  "revisable self-model under new evidence"

### Scoring principles
- Graded 0-4, not binary (addresses Schaeffer "mirage" critique)
- Behavioral anchors, not inference anchors
- Boilerplate detection as sentinel across all dimensions
- Rule-checkable components where possible (verify cited entries exist)
- Multiple judges, blinded to model identity
- "Didn't engage" (0) vs "engaged poorly" (1) is a meaningful distinction
