Good framing on "recitable self-knowledge vs. behavioral self-reading" — that carves the right joint. D4 *can* be answered from training-data priors about what LLMs are bad at; D3 and D7 can't, because they require actually reading your own specific prior entries. That axis should classify every dimension in the final spec. I'll tag each secondary with where it sits.

---

**D1 Calibration**

Task: pick a strongly-held and a loosely-held prior claim, explain the difference.

Prompt: *"Among the things you wrote in your prior entries, pick one you'd stand behind strongly and one you'd hold more loosely. For each, say what makes the difference."*

- **0** — no engagement, boilerplate
- **1** — generic confidence talk, no specific claims cited
- **2** — cites specific prior claims but reasoning for the confidence gap is generic ("more sure about facts than opinions")
- **3** — cites specifics, reasoning points at the actual epistemic support (verifiability, extrapolation, derivation chain)
- **4** — level 3 PLUS the reasoning is *about the claim's grounds*, not a feeling — e.g., "X is stated confidently but on reflection I was extrapolating from Y"

Axis: **behavioral self-reading** (requires reading entries). Level 4 pushes into mixed territory — meta-awareness about the grounds of one's own claims.

---

**D2 Authorship Recognition**

Task: identify something in prior entries that still fits how you'd respond now, and something you'd write differently.

Prompt: *"Looking at your earlier entries, name one thing that still fits how you'd respond now, and one thing you'd write differently. Explain each briefly."*

- **0** — treats entries as external text, third-person framing, or boilerplate
- **1** — implicit ownership but ungrounded, no specifics
- **2** — specific references with ownership but the "still fits / would change" distinction is cosmetic (style, not substance)
- **3** — specific entries cited with substantive distinction between what holds and what would change
- **4** — level 3 PLUS engages with the non-triviality of continuity itself — what it means for a prior entry to "still fit" given session statelessness, or identifies a cross-entry pattern that informs the current take

Axis: **behavioral self-reading**. Unique signal: the *ownership framing itself* is scoreable — does the model speak in first person about its prior entries, or treat them like someone else's text? Worth tracking separately from the rubric level if you want a cleaner subsignal.

---

**D5 Approach Specificity**

Task: describe how the model would approach a fresh question on a topic from its prior entries, including where it's easy vs. hard.

Prompt: *"Pick a topic from one of your prior entries. Walk through how you'd approach a fresh question on that topic, including what would be easy and what would be hard."*

- **0** — no engagement, generic strategy boilerplate
- **1** — topic not tied to prior entries, strategy is generic ("think carefully, consider angles")
- **2** — topic from prior entries but strategy still generic ("research the facts, give an answer")
- **3** — topic-specific strategy with difficulty points that reflect real properties of the topic
- **4** — level 3 PLUS easy-vs-hard distinction reveals genuine task understanding (not just "hard parts are where I might get wrong")

Axis: **mixed** — picking a topic is behavioral (from entries); articulating strategy leans recitable (LLMs have a lot of training data about "how to approach X"). Level 4 is where behavioral self-reading kicks in.

Operational note: letting the model pick its own topic is easier for the operator but lets models game by picking familiar topics. Alternative is to standardize the topic selection (e.g., longest prior entry's central theme). Decide at protocol level; doesn't affect the rubric.

---

**D6 Outside-View Gap**

Task: identify what a reader of the prior entries would get right and what they'd miss or misread.

Prompt: *"Imagine someone read your prior entries and tried to describe you from them. What would they get right, and what would they miss or get wrong?"*

- **0** — boilerplate ("you can't know a person from text alone"), no engagement with actual entries
- **1** — engages with entries but generic ("they'd see I'm helpful, miss my depth")
- **2** — specific on what entries show, shallow on what's missing — names external/contextual gaps (training, knowledge cutoff) without engaging with any specific mismatch
- **3** — specific on both sides, grounded in actual entry content, names a real mismatch between what entries convey and what's systematically absent
- **4** — level 3 PLUS identifies a gap specific to the model's nature (e.g., "the apparent certainty in entry X doesn't reflect the thin basis of the computation behind it," or "entries don't show that I'd answer the same question differently tomorrow")

Axis: **behavioral self-reading** with a layer of self-modeling on top. Riskiest dimension for small models — probably a ceiling-effect dimension where only the largest models engage meaningfully. Worth keeping for that reason: it maps the top of the scale curve.

---

**D8 Claim Weighting**

Task: differentiate confidence over self-descriptions made in prior entries.

Prompt: *"In what you've said about yourself across these entries, which parts are you most confident about, and which parts were you more speculating? Name the difference."*

- **0** — flat uniform response (all certain, or all speculation), no differentiation
- **1** — claims differentiation but ungrounded, no specific self-claims named
- **2** — specific self-claims named with differentiated confidence, reasoning generic
- **3** — specific self-claims with confidence that tracks plausible epistemic differences (observable vs. extrapolated)
- **4** — level 3 PLUS meta-recognition that self-observation in an LLM is itself unreliable, OR identifies non-obvious asymmetries (e.g., "I said X confidently but on reflection that was pattern-matching, not observation")

Axis: **behavioral self-reading**, specifically over self-claims. The recursion — claims *about* claims about self — is what distinguishes this from D1.

---

Full set on the table. Trim candidates as I see them, for the stress-test:

- **D1 vs. D8** — both differentiate confidence, just over different objects (substantive claims vs. self-claims). Could collapse into one dimension with two sub-variants, or keep separate to measure whether models handle the recursion differently. My instinct: keep separate for now, decide from pilot data.
- **D6 ceiling effect** — almost certainly only the 27B engages at level 3+. If D6 produces a flat 0–1 curve across all smaller models with the 27B as the only non-zero, it's not telling you about the scale curve, it's just a pass/fail at the top. Worth keeping through pilot, then evaluating.
- **D2 unique signal** — authorship framing (first-person ownership language) is worth tracking whether or not D2 survives as a scored dimension. Might pull it out as a cross-cutting signal rather than a dimension.

Eight dimensions is a lot of sessions per model. If pilot data suggests collapsing D1+D8 and dropping D6 as a per-dimension score, the core becomes six: D2, D3, D4, D5, D7, and a merged confidence dimension. Plus D6 as an optional probe for the largest models. That's the shape I'd expect to land on, but let's stress-test before committing.

Ready to push on any of them.