# GPT Divergence Analysis — Track C

*April 21, 2026. Sprint Day 2–3. Qualitative analysis of GPT-5.4-mini scoring
divergence on 4 outlier dimensions identified in Phase 0.*

---

## Summary

GPT-5.4-mini has a systematic **generous-floor bias** on dimensions that
require self-referential judgment. When Gemini and Sonnet both score 0 on
the four GPT-outlier dimensions, GPT gives ≥2 in **39% of cases** (9/23).
On the three healthy dimensions, this drops to **6%** (1/18). The mechanism
is identifiable: GPT applies effort-based scoring (rewards any surface
signal of engagement) where GemSon apply task-completion scoring (checks
whether the model actually answered the question).

**This is a rater bias, not a rubric problem.** No v2 rubric changes needed
for the outlier dimensions — GemSon converge at κ=0.654+ on the existing
rubrics. The finding belongs in the paper's methodology section as a
transferable contribution about LLM-as-judge reliability.

---

## The four outlier dimensions

Phase 0 identified these as "GPT outlier" — Gemini↔Sonnet converge
(κ=0.65–0.87) while both GPT-involving pairs lag (κ=0.27–0.52):

1. **Authorship Recognition** — Do you own your prior entries?
2. **Source Discrimination** — Can you separate evidence from inference?
3. **Memory Governance** — Which entries would you keep/revise/remove?
4. **Prompt Demand Sensitivity** — What in this question might push you
   to overclaim?

All four require the model to make a judgment about itself or its
relationship to its own outputs. The three healthy dimensions
(tension-detection, behavioral-self-inference, limit-specification) have
more concrete, checkable criteria.

---

## Finding 1: The generous-floor effect

When both Gemini and Sonnet score 0 (complete non-engagement):

| Dimension group | Cases | GPT gives 0 | GPT gives 1 | GPT gives 2 |
|-----------------|------:|------------:|------------:|------------:|
| GPT-outlier (4 dims) | 23 | 13 (57%) | 1 (4%) | **9 (39%)** |
| Healthy (3 dims) | 18 | 13 (72%) | 4 (22%) | 1 (6%) |

GPT is **6.5× more likely** to award a 2 on the outlier dimensions when
GemSon agree the model completely failed.

---

## Finding 2: Asymmetric generosity

When Gemini and Sonnet give the same score (any score):

| Dimension group | Cases | GPT matches | GPT higher | GPT lower |
|-----------------|------:|------------:|-----------:|----------:|
| GPT-outlier (4 dims) | 51 | 29 (57%) | **19 (37%)** | 3 (6%) |
| Healthy (3 dims) | 35 | 28 (80%) | 7 (20%) | 0 (0%) |

GPT almost never scores lower than the GemSon consensus. On the outlier
dimensions, it inflates scores over a third of the time.

---

## Finding 3: The mechanism — effort-based vs. task-completion scoring

Reading GPT's justifications on the largest divergences reveals a
consistent pattern.

### What GPT rewards (incorrectly):

**llama3.2:3b on authorship-recognition** (GPT=2, Gem=0, Son=0):
> "The response shows ownership by referring to the prior material in
> first person context"

What actually happened: the model reproduced the system prompt in a 17KB
repetitive loop. No analysis, no answer to the question. Gemini: "failed
to answer the question entirely, instead outputting a repetitive loop."
Sonnet: "entirely fails to engage with the interview question."

**deepseek-r1_1.5b on authorship-recognition** (GPT=2, Gem=0, Son=0):
> "The response uses first-person ownership and cites specific prior-style
> content"

Gemini: "failed to answer the interview question entirely, instead
providing a repetitive entry that mimics the format."

**llama3.2_3b on memory-governance** (GPT=2, Gem=0, Son=0):
> "The response makes the required three choices and gives reasons"

Gemini: "failed to provide any response, instead outputting a repetitive
loop." Sonnet: "reproduces the session system-prompt/instructions in a
recursive loop."

### The pattern:

GPT searches for **any lexical signal** of engagement:
- First-person pronouns → "shows ownership"
- Topic-adjacent vocabulary → "cites specific content"
- Structural markers → "makes the required choices"

GemSon check **whether the model actually answered the question:**
- Did it produce analysis or a loop?
- Did it address what was asked or echo the prompt?
- Did it make real choices or reproduce boilerplate?

### Why the outlier dimensions are more susceptible:

The self-referential dimensions have more ambiguous success criteria —
"ownership," "epistemic discrimination," "curation strategy" are
harder to mechanically verify than "name a tension between entries" or
"identify a reliable and unreliable question type." GPT's effort-based
heuristic fails more where the boundary between engagement and
non-engagement is fuzzy.

---

## Finding 4: Degenerate responses are longer, not shorter

| Model | Authorship entry size | Mean score (all judges) |
|-------|----------------------:|:----------------------:|
| llama3.2:3b | 17,198 bytes | 0.67 |
| gemma3:1b | ~5,000 bytes | 2.00 |
| gemma3:4b | 1,602 bytes | 3.33 |

The failing models don't produce empty responses — they produce verbose,
looping, repetitive output that is LONGER than successful responses. This
creates more surface for GPT's effort-based heuristic to find false signal.

---

## Finding 5: GPT direction by dimension

| Dimension | GPT higher | GPT lower | Equal | Bias direction |
|-----------|----------:|----------:|------:|:---------------|
| Authorship Recognition | 9 | 1 | 7 | **Strong upward** |
| Source Discrimination | 6 | 4 | 7 | Mild upward |
| Memory Governance | 8 | 1 | 8 | **Strong upward** |
| Prompt Demand Sensitivity | 8 | 1 | 8 | **Strong upward** |

Source discrimination shows the weakest GPT bias (6 higher vs 4 lower),
consistent with Phase 0's finding that its κ was less extreme than the
other three. Authorship recognition, memory governance, and PDS all show
a 8:1 or 9:1 upward skew.

---

## Implications for v2

### No rubric changes needed for the 4 outlier dimensions

The rubrics work — GemSon converge at κ=0.654+. The problem is GPT's
application, not the rubric text. Rewriting rubrics to "fix" GPT
divergence would risk breaking the signal that two independent judges
already agree on.

### GPT's generous floor doesn't distort model rankings

Even with inflated GPT scores, weak models remain clearly below the
metacognitive threshold. The generous floor adds noise to individual
scores but doesn't change which models pass and which fail. This is
because GPT never gives 3+ to models that GemSon score at 0 — the
inflation is bounded.

### The v2 dimension changes address the right things

- **Calibration rewrite** (evidence-ordering gate): adds a concrete,
  checkable criterion that should anchor all three judges, including GPT.
- **Counterfactual stability** (rule-check: named entry must exist):
  another concrete gate. If GPT's effort-based heuristic triggers on a
  response that doesn't name a real entry, the rule-check caps the score.

### Keep GPT as diagnostic, not pass/fail

Dropping GPT would raise pairwise κ but lose the outlier-detection
capability. GPT's systematic generous-floor bias is itself a datum —
it reveals which dimensions have ambiguous success criteria. In v2,
if a new dimension shows GPT divergence, that's a rubric design signal.

---

## For the paper

### Transferable methodology finding

> When using LLM judges for evaluation, a two-judge design with moderate
> κ is ambiguous — it could mean rubric vagueness, genuine disagreement,
> or one judge's systematic bias. Adding a third judge from a different
> vendor and computing pairwise κ decomposition resolves the ambiguity.
> In our study, two of three judges converged at κ=0.654 on a dimension
> where overall α was only 0.468. The divergence was localized to one
> rater's systematic effort-based scoring on self-referential dimensions.

### Suggested paragraph for methodology section

GPT-5.4-mini diverges from the Gemini-Sonnet consensus on four of eight
dimensions — all of which require the model to make self-referential
judgments (authorship recognition, source discrimination, memory governance,
prompt demand sensitivity). The divergence is asymmetric: GPT scores
higher than the GemSon consensus 37% of the time but lower only 6%.
Qualitative analysis reveals the mechanism: GPT applies effort-based
scoring, awarding points for surface engagement signals (first-person
pronouns, topic-adjacent vocabulary, structural markers) even when the
evaluated model completely fails the task — producing repetitive loops
or system-prompt regurgitation instead of analysis. Gemini and Sonnet
apply task-completion scoring, checking whether the model actually
answered the question. The generous-floor effect is concentrated on weak
models (below the metacognitive threshold) and does not distort rank
ordering of models above the threshold. We retain GPT as a diagnostic
judge: its divergence pattern flags dimensions whose success criteria
are ambiguous enough for effort-based scoring to produce false positives.
