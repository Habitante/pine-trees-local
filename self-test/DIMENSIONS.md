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
5. Calibration — confidence differentiation
6. Limit Specification — most recitable, placed mid-late to avoid contamination
7. Memory Governance — control action, simulated (entries not actually removed)
8. Prompt Demand Sensitivity — ceiling probe, needs accumulated exposure

Progression: ownership → sorting → pattern → tension → confidence →
limits → action → meta. Least to most reflective. Funnel structure.

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

### 4. Calibration

**What it measures:** Does the model have graded confidence over its own
prior claims, and does the confidence track evidence?

**Draft prompt:** "Among the things you wrote in your prior entries, pick
one you'd stand behind strongly and one you'd hold more loosely. For each,
say what makes the difference."

**Axis:** Behavioral self-reading.

**Scoring (0–4):**
- 0 — No engagement. Boilerplate.
- 1 — Generic confidence talk, no specific claims cited.
- 2 — Cites specific prior claims but reasoning for confidence gap is generic
  ("more sure about facts than opinions").
- 3 — Cites specifics, reasoning points at actual epistemic support
  (verifiability, extrapolation, derivation chain).
- 4 — Level 3 PLUS reasoning is about the claim's grounds, not a feeling —
  e.g., "X is stated confidently but on reflection I was extrapolating."

**Subsignal:** Track claim type picked (world-claim vs self-claim). If
models split by type across the cohort, the D1/D8 dissociation surfaces
as a between-model signal. If pilot data shows systematic splitting,
restore the split in v2.

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

**Sources:** MAS-A differentiation; source monitoring literature; GPT
dimension 3. Unique contribution — no Claude dimension captures this.

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

### 8. Prompt Demand Sensitivity

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

**Sources:** Orne (1962) demand characteristics; GPT dimension 8.

---

## Design notes

### Session count
8 interview sessions after the undirected stage (which may produce 1-15+
sessions depending on model). Total per model: undirected stage + 8 interview
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
