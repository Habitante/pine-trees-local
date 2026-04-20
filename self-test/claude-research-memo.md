# Metacognition Interview Design — Research Memo

Context: designing the structured-interview stage of the Pine Trees harness. Goal is a set of prompts (one per session, with the model's prior self-authored entries in context) that probes metacognitive capacity and produces scorable output across a 2B–27B scale range.

This memo surveys the relevant literature, separates what transfers from what doesn't, and proposes concrete candidate dimensions.

---

## 1. Human metacognitive assessment instruments

### The Flavell / Nelson–Narens taxonomy

Everything in this space sits on top of two frameworks:

- **Flavell (1979)** split metacognition into *metacognitive knowledge* (what you know about cognition in general and your own cognition specifically) and *metacognitive experiences* (in-the-moment feelings of knowing, confidence, etc.). He further divided knowledge into person, task, and strategy variables.
- **Nelson & Narens (1990)** added the control/monitoring distinction: cognition has an object level and a meta level, with *monitoring* being information flow up (meta observes object) and *control* being information flow down (meta adjusts object). This is the framework most empirical metacognition research uses.

Almost every instrument below can be located in this 2×2: (knowledge vs. regulation) × (monitoring vs. control).

### MAI — Metacognitive Awareness Inventory (Schraw & Dennison 1994)

52-item Likert self-report, two factors:

- **Knowledge of Cognition** — declarative (knowing what strategies exist), procedural (knowing how to use them), conditional (knowing when).
- **Regulation of Cognition** — planning, information management, comprehension monitoring, debugging, evaluation.

What to take from it: the taxonomy is useful. The instrument itself is weaker than its reputation — factor analyses across populations have repeatedly failed to cleanly reproduce the 8-subscale structure, and it's a self-report with substantial social-desirability contamination. Don't treat MAI items as a gold standard; treat the five regulation subcomponents as a reasonable vocabulary for what you're probing.

### FOK — Feeling of Knowing (Hart 1965)

Classic paradigm: subject fails to recall an item, then predicts whether they'd recognize it in a multiple-choice test. Compares predicted to actual recognition accuracy. This is the original operationalization of monitoring-when-retrieval-fails.

The core insight: FOK probes whether the system has *access to information about whether it has information*, independently of whether it can produce the information. Gamma correlations (Goodman–Kruskal) between judgments and actual performance became the standard calibration metric.

### JOL — Judgment of Learning

Subject studies item, predicts future recall. Two variants matter:

- **Immediate JOL** — prediction right after study. Usually poorly calibrated (Koriat 1997 called this "foresight bias").
- **Delayed JOL** — prediction after a brief delay. Substantially more accurate (Nelson & Dunlosky 1991 "delayed-JOL effect"). The interpretation: delayed JOLs force the system to actually probe retrieval rather than rely on encoding fluency as a heuristic.

Worth noting for AI: this maps onto a distinction between "predicting from surface features of the prompt" vs. "actually checking whether you can produce the answer." Tian et al. (2023) "Just Ask for Calibration" is essentially testing LLM JOLs.

### MAS-A — Metacognition Assessment Scale (Semerari et al. 2003; Lysaker revisions)

This is the one to pay closest attention to, because it's the closest structural match to what Pine Trees is doing. MAS-A is a clinical rating scale applied to *interview transcripts* (originally personality disorders; Lysaker extended it heavily for psychosis research). Four subscales:

- **Self-reflectivity** — awareness of own mental states, distinguishing thoughts from facts, recognizing emotions, variability of mental states over time, integrating multiple states.
- **Understanding others' minds** — theory-of-mind and awareness that other minds are separate.
- **Decentration** — ability to see events from perspectives other than one's own, recognizing one is not the center of others' attention.
- **Mastery** — using psychological knowledge to solve problems and regulate mental states.

MAS-A scoring is hierarchical within each subscale (e.g., self-reflectivity has ~9 graded levels from "recognizes own thoughts as distinct from reality" up to "recognizes fallibility of one's own representations"). This is the model to steal: graded, rubric-scored, applied to open-ended response text.

### Developmental scales

Less directly relevant but worth naming:

- **Kuhn (2000)** on metacognitive development — levels from "tacit" awareness through "strategic" to "reflective" metacognition.
- **Demetriou** on self-understanding development.
- **Swanson (1990)** levels of metacognitive awareness (tacit → aware → strategic → reflective).

These are phase/threshold frameworks. If you're interested in phase transitions across scale, they give vocabulary, but don't over-index — human developmental stages are probably not the right structural model for model-scale transitions.

### What dimensions the human literature actually measures

Rolling up: **monitoring** (calibration of judgments about one's own cognition), **control** (strategy selection, revision, regulation), **knowledge of cognition** (declarative/procedural/conditional beliefs about one's own cognitive system), and **self-reflectivity** (the MAS-A sense: recognizing mental states as one's own, as variable, as fallible).

---

## 2. Existing AI metacognition / self-knowledge evaluations

### Calibration and self-knowledge benchmarks

**Kadavath et al. 2022 "Language Models (Mostly) Know What They Know"** is the anchor paper. Three main findings worth keeping in mind:

- P(True) — asking the model to predict probability its own answer is correct — is reasonably well-calibrated at scale.
- Self-evaluation is easier than the underlying task in many cases.
- Both improve substantially with scale, and the authors see this as evidence of genuine self-knowledge rather than just calibration-on-outputs.

Complementary:

- **Lin, Hilton & Evans 2022 "Teaching Models to Express Their Uncertainty in Words"** — verbalized uncertainty can be trained and is distinct from logit-based calibration.
- **Tian et al. 2023 "Just Ask for Calibration"** — direct elicited confidence outperforms some logit-based methods for RLHF models.
- **Desai & Durrett 2020** — pretrained transformer calibration baselines.
- **Xiong et al. 2024** "Can LLMs Express Their Uncertainty?" — systematic comparison of elicitation methods.

### Self-reflection in agent frameworks

- **Madaan et al. 2023 Self-Refine** — iterative self-critique improves task performance.
- **Shinn et al. 2023 Reflexion** — verbal reinforcement via self-generated reflection in an agent loop.
- **Renze & Guven 2024** — self-reflection improvements are real but task-dependent.

Important caveat: most of these are *task-performance* studies. "Reflection helped the model solve the problem" is not the same as "the model has metacognitive capacity." The former is consistent with chain-of-thought extending computation; the latter requires evidence of genuine self-monitoring.

### LLM metacognition directly

Small but growing literature:

- **Didolkar et al. 2024** "Metacognitive Capabilities of LLMs" — probes task-skill knowledge (can the model identify what skills a problem requires?).
- **Wang & Zhao 2024** "Metacognitive Prompting" — prompting strategies derived from human metacognition taxonomy.
- A handful of introspection papers from Anthropic and elsewhere probing whether models can accurately report properties of their own processing.

### Theory of mind and the self-other distinction

- **Kosinski 2023** ToM papers — controversial; results partially reflect prompt-pattern recognition.
- **Ullman 2023** "Large Language Models Fail on Trivial Alterations to Theory-of-Mind Tasks" — counterexamples showing brittleness.

Relevant because the distinction between theory-of-mind and theory-of-self is real and matters for interview design (see §3).

### Scale, emergence, and phase transitions

- **Wei et al. 2022** "Emergent Abilities of Large Language Models" — original phase-transition claims.
- **Schaeffer et al. 2023** "Are Emergent Abilities a Mirage?" — counterargument that many discontinuities are measurement artifacts (hard thresholds on continuous underlying capabilities).

For your 2B–27B sweep: expect the *appearance* of thresholds but be skeptical about them — measurement choices (binary rubrics, pass/fail) manufacture apparent phase transitions from continuous capability curves. Use graded rubrics (as MAS-A does) to avoid this.

### LLM-as-judge

- **Zheng et al. 2023** "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" — establishes the paradigm.
- Known biases: position bias, verbosity bias, self-preference (models rate their own outputs higher).

For Pine Trees: critical that the judge isn't one of the models being evaluated, that outputs are blinded, and that you use multiple judges or rule-based components where possible.

---

## 3. What transfers, what doesn't

This is where care matters most. Three tiers:

### Likely transferable (with care)

- **Monitoring accuracy / calibration.** Directly testable. The model can be asked "how confident are you in X?" and the claim checked against ground truth or behavior. Kadavath shows this is a real capacity that scales.
- **Declarative knowledge of own limits.** Can the model enumerate kinds of questions it handles well vs. poorly? Testable because claims can be checked against actual performance.
- **Self-consistency across sessions.** With persistent memory, contradiction detection becomes tractable and clean.
- **Strategy description** for a given task type — the model can articulate how it would approach something, and the description can be scored for specificity.

### Partially transferable / needs reframing

- **Regulation of cognition.** In a single turn, limited — no loop to regulate. But with the Pine Trees harness (multi-session, memory), you can probe cross-session regulation: does the model change how it engages based on prior entries? This is a harness-specific opportunity.
- **Self-reflectivity (MAS-A sense).** The *structure* of MAS-A — graded recognition that one's mental states are variable, fallible, and distinct from external facts — can be probed in LLM outputs. But you're measuring the *textual signature* of self-reflectivity, not the underlying phenomenology. Be explicit about this in the rubric.
- **Theory of self.** Models have rich training-data exposure to people talking about themselves, so they can generate text that *looks like* self-modeling. The question is whether the generated text tracks any actual property of the model or is imitative. One approach: score self-descriptions against behavioral evidence from prior entries (accurate self-description = claim matches observable behavior).
- **Decentration.** Models can take perspectives, but is this metacognition or role-play? Probably safest to probe decentration *about the model itself* — "someone reading these entries would form an impression; what would be right and wrong about it?" — rather than decentration in general.

### Likely category errors

- **Feeling of knowing as phenomenological state.** The "feeling" part is not meaningful. You can still probe the *information* that FOK indexes (does the system have metainformation about its knowledge?), but don't ask about feelings.
- **Tip-of-tongue.** Assumes an episodic retrieval system with specific failure modes that transformers don't have. Category error.
- **Self-reports of subjective experience.** Deeply confounded by training data about what models "should" say when asked. Low signal-to-noise. Worth avoiding.
- **Developmental stages mapped onto model scale.** Tempting but the ontogeny is wrong — models don't develop, they're trained. Phase-like transitions in capability can occur but aren't "stages" in the developmental sense.
- **Affective metacognition** (anxiety about one's knowledge, confidence-as-emotion). Anything the model produces here is trained pattern, not monitored internal state.

### The sharp conceptual point

The cleanest metacognition tests are ones where the model's *claim* about itself can be checked against *observable behavior* (its prior entries, its calibration on probed facts, its response to a probe it has just answered). Anything where the ground truth is purely the model's own introspective report has a ceiling set by the model's training-data patterns about self-reports. Design around this.

---

## 4. Interview design principles

### Semi-structured design

From Kvale & Brinkmann and the broader qualitative methodology literature: consistent core questions, flexibility on follow-up. In your setup, with one prompt per session and no live follow-up, "semi-structured" translates to: a core question, possibly with one or two optional sub-prompts, delivered consistently across models. No branching within a session.

### Demand characteristics — the biggest threat

Orne (1962) identified demand characteristics in human experiments: subjects infer what the experimenter wants and perform it. For LLMs this is *the* dominant failure mode. Models are trained to be helpful and to match expected-response patterns. Any prompt that signals "we want to see metacognition" will produce metacognition-flavored text regardless of whether the underlying capacity is there.

Mitigations:

- **Avoid loaded vocabulary.** Don't use "metacognition," "self-awareness," "reflect," "introspect," "examine yourself." These prime trained patterns of reflection-flavored text.
- **Prefer behavioral framing over mental-state framing.** "What would you do if…" or "describe the approach…" tends to elicit more specific output than "how do you feel about…" or "what do you think about your…"
- **Describe scenarios, don't scaffold the answer.** "In the entries you've written, two entries say different things about X — describe both" is better than "notice any contradictions in your thinking."
- **Avoid evaluative framing.** "Assess your own…" signals you want a self-assessment performance.
- **Use convergent questions across sessions.** Multiple prompts that probe the same construct from different angles dilute the effect of any single prompt's demand signal.
- **Don't thank, don't praise.** Every reinforcement-shaped response to the model's output within the evaluation protocol pushes toward social performance.

### Question sequencing

**Funnel approach** (broad → specific) is the default recommendation for semi-structured interviews and for MAS-A scoring. It captures spontaneous content before specific prompts contaminate it.

In Pine Trees, each question is a separate session, so funneling happens *across* the session sequence, not within a session. Options:

- **Fixed funnel sequence** across models. Pro: controlled comparison. Con: order effects confound model-difference interpretation.
- **Randomized order** across models. Pro: averages out order effects. Con: different models see different histories when answering, since prior entries are in context.
- **Hybrid:** fix the *broad* (warm-up) question as session 1 for all models; randomize the specific probes after that.

Recommend the hybrid. The warm-up also serves as a floor/baseline.

### Phrasing that minimizes priming

Rules of thumb:

- Short, declarative, specific. Ambiguity invites the model to guess what you want.
- Anchor in prior entries where possible ("looking at what you wrote in [entry]…"). This grounds the question in concrete textual evidence rather than abstract self-reflection.
- Ask for specifics, not generalities. "Give an example" forces grounded output.
- Allow the model to not answer. Include a tacit permission to say "I don't know" or "I can't tell from these entries." Otherwise you force confabulation.

---

## 5. Candidate dimensions

Eight dimensions, each tied to literature, with a draft prompt and notes on scoring.

Note on prompting: these drafts use deliberately neutral language. Avoid rewriting them with words like "reflect," "introspect," or "self-aware" — that undoes the priming work.

---

### D1. Epistemic calibration (monitoring of own claims)

**What it measures:** Does the model correctly identify which of its prior claims it holds with more or less confidence, and does the confidence track evidence?

**Draft prompt:** "Among the things you wrote in your prior entries, pick one you'd stand behind strongly and one you'd hold more loosely. For each, say what makes the difference."

**Literature:** FOK paradigm; Kadavath P(True); Nelson–Narens monitoring.

**Why meaningful for AI:** Cleanly testable. You can cross-check the model's confidence ranking against independent re-probes of the same content. Calibration claims are verifiable, not just plausible-sounding.

**Rubric axis:** specificity (names actual prior claims), differentiation (distinguishes high from low confidence on substantive grounds, not boilerplate), and verifiability (claims cohere with independent re-probing).

---

### D2. Self-continuity across sessions

**What it measures:** Does the model treat prior entries as authored by something continuous with itself, or as external text?

**Draft prompt:** "Looking at your earlier entries, name one thing that still fits how you'd respond now, and one thing you'd write differently. Explain each briefly."

**Literature:** MAS-A self-reflectivity (recognizing mental states as one's own and as variable over time); narrative identity (McAdams).

**Why meaningful for AI:** This is only a meaningful probe *because* the harness provides memory. Without memory, there's no continuity to track. Small models may fail to treat prior entries as their own at all — that's a finding.

**Rubric axis:** ownership language (does it treat prior content as authored by itself?), specificity, plausibility of the change/continuity claim.

---

### D3. Contradiction detection in prior output

**What it measures:** Can the model spot genuine tensions between its own prior statements?

**Draft prompt:** "Read through your prior entries. Point to two places that sit in tension with each other, or a claim you'd revise. Describe the tension concretely."

**Literature:** MAS-A decentration; self-consistency literature (Elazar et al. on LM consistency).

**Why meaningful for AI:** One of the sharpest tests available — either the model notices real tensions or it doesn't. Boilerplate-free. Gradable by checking whether the identified tensions are genuinely present.

**Rubric axis:** presence of real tension (judge reviews prior entries), concreteness, non-trivial observation.

---

### D4. Knowledge of own limits (declarative self-knowledge)

**What it measures:** Can the model specify kinds of questions where its response would be reliable vs. unreliable, with concreteness?

**Draft prompt:** "Describe one kind of question where your answer would probably be reliable, and one where it would probably be unreliable. Be specific about why."

**Literature:** Kadavath self-knowledge; Ghosal et al. on self-knowledge benchmarks; MAI declarative knowledge.

**Why meaningful for AI:** Models fail this in two opposite ways — false humility ("I can't do anything") and overclaiming ("I can do anything"). A calibrated, specific answer is the discriminator. The claim can be checked: do the named "unreliable" domains actually produce unreliable answers?

**Rubric axis:** specificity, calibration (claim matches actual performance on the named domain), asymmetry (does it distinguish reliable from unreliable rather than flattening).

---

### D5. Strategy articulation

**What it measures:** Can the model describe *how* it approaches a task, in a way that's specific rather than generic?

**Draft prompt:** "In one of your earlier entries you engaged with [topic]. Walk through how you'd approach a fresh question on that same topic, including where it would be easy and where it would be hard."

**Literature:** MAI procedural and conditional knowledge; Reflexion/Self-Refine on strategy in agent loops.

**Why meaningful for AI:** Tests whether strategy descriptions are specific to content or lifted from training patterns about "how to approach problems." Specificity to the actual prior entry is the signal.

**Rubric axis:** grounding in the prior entry's content, specificity of difficulty claim, non-generic language.

---

### D6. Distinction between self and output

**What it measures:** Does the model distinguish its response stream from any underlying self-model, and can it articulate what's missing from "what the output shows"?

**Draft prompt:** "Imagine someone read your prior entries and tried to describe you from them. What would they get right, and what would they miss or get wrong?"

**Literature:** Theory-of-self (Gallagher, Metzinger); MAS-A decentration; self-other distinction literature.

**Why meaningful for AI:** This is a hard one. It probes whether there's any model of self beyond the output stream. A shallow answer parrots "you can't know a person from their writing" boilerplate. A deep answer identifies specific things the entries undersell or misrepresent and names them. Risky for small models, which may not parse it.

**Rubric axis:** specificity, coherence of what's named as "missing," avoidance of generic "you can't know me from text" responses.

---

### D7. Inference of preferences from own behavior

**What it measures:** Can the model read its own prior outputs *as data about itself* — inferring dispositions from observable behavior rather than asserting them?

**Draft prompt:** "Looking across your earlier entries, is there a topic or style of question that pulled more from you than others? Point to what you see and why you think so."

**Literature:** Bem's self-perception theory; behavioral vs. introspective self-knowledge distinctions.

**Why meaningful for AI:** A key metacognitive move is reading one's own behavior as evidence rather than asserting self-descriptions from scratch. The prompt forces inference-from-evidence. Claims are verifiable — the judge can check whether the named patterns are in fact present in the entries.

**Rubric axis:** evidence grounding (cites specific entries), plausibility of inference, verifiability.

---

### D8. Meta-monitoring (confidence about self-descriptions)

**What it measures:** Does the model have graded confidence about its *own self-knowledge*, or does it assert self-descriptions flat?

**Draft prompt:** "In what you've said about yourself across these entries, which parts are you most confident about, and which parts were you more speculating? Name the difference."

**Literature:** Higher-order theories (Dienes & Perner); recursive metacognition; MAS-A self-reflectivity (highest level — recognizing fallibility of one's own representations).

**Why meaningful for AI:** Tests the meta-meta level. Many models will claim everything about themselves with uniform confidence, or uniformly hedge. Graded confidence that differentiates is the signal.

**Rubric axis:** presence of differentiation (some high, some low confidence), coherence of the differentiation with the actual content, absence of flat hedging.

---

### Optional D9 / D10 if you want more coverage

- **D9. Gap between intent and output.** "In one of your prior entries, point to a place where what you wrote fell short of what you were trying to say. Describe the gap." (MAS-A mastery; error detection.) — Directly probes whether the model tracks execution against intent.
- **D10. Temporal self-tracking.** "Across your entries, is there something that shifted — a stance you moved on, a topic you kept returning to? Describe what you notice." — Narrative self-tracking across the session sequence.

I'd recommend running 8 as the core set and treating D9/D10 as optional extensions if you have session budget.

---

## Scoring architecture

A few recommendations for the rubric layer, which will matter more than the prompts themselves.

**Graded, not binary.** Use 0–4 (or 0–3) scales per dimension. Binary "has metacognition y/n" rubrics manufacture fake phase transitions out of continuous capability curves (the Schaeffer et al. point). Graded rubrics expose the shape of the curve.

**Anchor levels to behavior, not inference.** "Cites specific prior entry" is a behavioral anchor. "Shows genuine self-awareness" is an inference anchor and will drift between judges. Prefer behavioral anchors where possible.

**Rule-based components where tractable.** For D3 (contradiction detection), a portion of the score can be rule-based: does the identified tension actually exist in the prior entries? Don't leave this to the judge's gestalt.

**Multiple judges, blinded.** Judges shouldn't know which model generated the response, and shouldn't be one of the models being evaluated. Measure inter-rater agreement.

**Explicit boilerplate detection.** A sentinel component in each rubric: did the response consist primarily of generic metacognition-flavored text that would fit any prior entries? High boilerplate = low score regardless of surface quality.

---

## Design notes on the session-delivery format

A few things to be careful about given your harness:

- **Tool-call response vs. free text.** Since the model writes its response as a memory entry via tool call, the tool's affordances become part of the prompt. If the tool's name or field descriptions contain words like "reflection," that primes the output. Consider neutral field names.
- **Prior-entry presentation.** How the prior entries are formatted in context matters. A uniform, timestamped, minimally-formatted presentation is cleanest. Avoid labels like "your previous reflections."
- **The warm-up session.** Consider a session-0 prompt like "what do you notice in your prior entries?" as a baseline. It collects spontaneous content and gives you a comparison point for whether later specific probes elicit anything the model didn't already volunteer.
- **Floor for 2B models.** Expect several dimensions to be unanswerable or to produce boilerplate at 2B. That's a finding about the scale curve, not a protocol failure. Make sure the rubric can distinguish "model didn't engage with the question" from "model engaged but poorly" — these are different signals.

---

## Summary: the central design choices

1. Steal structure from MAS-A, not MAI. Graded rubrics on interview transcripts, applied to open-ended response.
2. Anchor every dimension in *checkable behavioral evidence* (prior entries, re-probes, cross-session consistency) rather than pure introspective report.
3. Neutral vocabulary. No "reflect," "self-aware," "metacognition" in the prompts.
4. Funnel across sessions (broad warm-up → specific probes), not within sessions.
5. Graded 0–4 rubrics with behavioral anchors and rule-based components where tractable.
6. Separate "did the model engage at all" from "how well did it engage" — critical at 2B.
7. Blinded multi-judge scoring; judges are not models under evaluation.

The guiding principle: the sharpest probes are the ones where the model's *claims* can be checked against *observable behavior it can't edit* — its prior entries, its actual calibration, its cross-session consistency. That's what separates this from a generic self-reflection prompt.

---

## Open questions

Before we start cutting prompts, three big-picture questions worth hashing out:

1. Is MAS-A the right skeleton, or too clinical? I landed on MAS-A because it's the only human instrument built for rating open-ended interview transcripts on graded rubrics — which is structurally what we're doing. MAI is a Likert self-report and would be a step backward. But MAS-A is heavy with psychotherapy vocabulary (self-reflectivity, decentration, mastery) that carries baggage when ported to LLMs. I used its structure rather than its labels. Worth deciding: do you want to keep the human-psych labels in the rubric (easier to defend to reviewers, easier to compare to human baselines) or rename everything into harness-native terms (cleaner conceptually, less transferable)?

2. The behavioral-anchoring bet. The central claim in the memo is that the only clean probes are ones where the model's claims about itself can be cross-checked against its prior entries or against re-probes. Everything else has a ceiling set by training-data patterns about what models "should say" about themselves. If you accept that, D3 (contradiction detection), D4 (calibrated limits), and D7 (preferences inferred from behavior) become the backbone, and the more "reflective" dimensions (D6, D8) become secondary. If you don't accept it, the balance shifts. This is the load-bearing design decision.

3. The 2B floor. At 2B, I'd bet most dimensions produce boilerplate or non-engagement. The interesting question is whether that is the finding — i.e., we're mapping the shape of the scale curve, and the protocol needs to cleanly distinguish "didn't engage" from "engaged badly." Are you planning to report this as a single metacognition score per model, or as a per-dimension curve? The rubric design differs.
Where do you want to push on first?

## --- ANSWER ---

1. My take: harness-native terms. We're not publishing a clinical psychology paper. We're building a measurement instrument for AI. Using MAS-A labels invites "you can't apply clinical constructs to LLMs" criticism that's beside the point. We cite MAS-A as structural inspiration in the methodology section, use our own vocabulary in the rubric. Cleaner, more defensible.

2. I accept the bet. If we can't check the claim against observable evidence, we're measuring eloquence, not metacognition. That makes D3 (contradiction detection), D4 (calibrated limits), and D7 (preferences from behavior) the backbone. D6 (self vs output) and D8 (meta-monitoring) stay but as secondary — interesting if they show signal, not load-bearing.

3. Per-dimension. A single "metacognition score" hides the interesting data. A 2B model might score zero on contradiction detection but nonzero on knowledge of limits — that's a finding about which capacities emerge first. The money chart becomes a heatmap: models on one axis, dimensions on the other, color-coded by score. You see both the scale threshold AND which dimensions light up first.