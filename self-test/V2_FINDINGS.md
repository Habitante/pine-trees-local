# Self-Test Protocol v2 — Findings

*TEMPLATE — scaffolding only. Fill in once v2 scoring is complete.
Dated placeholders marked `{{FILL}}` below. Do not cite this document
until the `TEMPLATE` marker is removed.*

---

## Study design

**Protocol**: v2 of the Pine Trees Local metacognitive evaluation. Same
two-stage structure as v1 (undirected reflection → structured interview).
Changes from v1:

- **9 dimensions** instead of 8. Counterfactual Stability added at
  position 8; Prompt Demand Sensitivity moved to 9. Rationale: probes
  revisability of the self-model, a construct the other 8 dimensions
  don't directly test.
- **Calibration rewrite**: v1 rubric relied on "actual epistemic support"
  (inference anchor); v2 adds a whole-response evidence-ordering gate —
  does the strongly-held claim actually have more textual support in
  the entries than the loosely-held one? Rationale: v1 κ = 0.14, the
  only dimension Phase 0 confirmed as genuinely rubric-broken.
- **Source Discrimination UNCHANGED**: v1 κ ≈ 0 was driven by GPT-specific
  divergence (Gem↔Son κ = 0.654), not rubric ambiguity. Rewriting a
  rubric two raters already agree on would risk breaking working signal.

**Cohort**: {{FILL: firm count}} models, 3 runs each = {{FILL: total runs}}
independent runs. Expanded from v1's 17 models with:

- Qwen generational arc completed: qwen3:1.7b, qwen3:4b, qwen3:8b
- Qwen 2.5 ceiling: qwen2.5:7b
- Qwen 3.5 ceiling (headline test): qwen3.5:27b
- Granite dense-vs-hybrid: granite3.1-dense:2b, granite3.1-dense:8b
- Llama-derivative matched pairs:
  - 3B: llama3.2:3b (vanilla) vs hermes3:3b (engagement-tuned)
  - 8B: llama3.1:8b (vanilla) vs cogito:8b (reasoning-tuned)
- Gemma 4 ceiling: gemma4:26b ({{FILL: and/or}} gemma4:31b)

**Scoring**: three LLM judges (GPT-5.4-mini, Gemini 3 Flash Preview,
Claude Sonnet 4.6 via Max OAuth). Temperature=0.0 where exposed (GPT,
Gemini); Sonnet deterministic empirically at N=2 concurrent. Blinded
prompts (model identity stripped, entry filenames relabeled "Entry NNN").
Rule-check enforcement: unverifiable citations → cap at 2.

**Inter-rater reliability**: Krippendorff's α (ordinal) as headline,
three pairwise Cohen's weighted κ (gpt↔gem, gpt↔son, gem↔son) as
diagnostic.

---

## Instrument quality

### Overall IRR

| Metric | v1 (2 raters) | v2 (3 raters) |
|---|---:|---:|
| Overall α / κ | 0.468 (κ) | {{FILL}} (α) |
| Complete triples | 116 | {{FILL}} |

### Per-dimension (v2, all three pairwise κ + α)

| Dimension | α | gpt↔gem | gpt↔son | gem↔son | Pattern |
|---|---:|---:|---:|---:|---|
| authorship-recognition | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| source-discrimination | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| behavioral-self-inference | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| tension-detection | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| calibration (v2) | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| limit-specification | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| memory-governance | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| counterfactual-stability (new) | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| prompt-demand-sensitivity | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |

*Pattern column values: "healthy" (all three pairs ≥ 0.5), "GPT outlier"
(gem↔son ≥ 0.6 but both GPT pairs < 0.5), "rubric broken" (all three
pairs < 0.4), "mixed".*

---

## Pre-registered predictions — outcome

Three predictions were committed to V2_PLAN.md before v2 data collection
(see pre-registration in V2_PLAN §"Pre-registered predictions from
Phase 0 + Track C"). Each tests a specific claim about GPT's
divergence mechanism identified in Phase 0 (effort-based scoring on
fuzzy success criteria).

### P1 — Calibration v2 closes the κ gap

**Prediction**: all three pairwise κ on Calibration rise substantially
over v1's 0.14, GPT no longer diverges. Failure falsifies the
"fuzzy criteria drive GPT divergence" mechanism.

**Outcome**: {{FILL: CONFIRMED / REFUTED / MIXED}}

v1 Calibration κ = 0.14. v2: α = {{FILL}}, pairs =
{{FILL: gpt↔gem}} / {{FILL: gpt↔son}} / {{FILL: gem↔son}}.

{{FILL: interpretation — did the whole-response evidence-ordering
gate close the gap for all three raters, only for GemSon, or not at all?}}

### P2 — Counterfactual Stability low GPT divergence from day one

**Prediction**: the new dimension's concrete rule-check ("named entry
must exist") produces healthy κ across all three pairs on first run,
comparable to v1's healthy dimensions (κ ≥ 0.5). Failure — if GPT
shows the outlier pattern here too — means the mechanism generalizes
beyond rubric vagueness to something broader.

**Outcome**: {{FILL: CONFIRMED / REFUTED / MIXED}}

α = {{FILL}}, pairs = {{FILL}} / {{FILL}} / {{FILL}}.

{{FILL: interpretation — does the concrete rule-check hold GPT in
alignment, or does the outlier pattern emerge even under a clean gate?}}

### P3 — 4 unchanged outlier dimensions persist

**Prediction**: Authorship Recognition, Source Discrimination, Memory
Governance, and Prompt Demand Sensitivity keep the v1 rubric. The
GPT-outlier pattern should reappear at similar magnitude (Gem↔Son
≥ 0.6, GPT pairs in the 0.27–0.52 band). Failure — if they stabilize
across judges in v2 — means something about v2 runs, not the rubric,
was driving the v1 divergence.

**Outcome**: {{FILL: CONFIRMED / REFUTED / MIXED}}

Per-dimension comparison vs v1:

| Dimension | v1 gpt↔gem | v2 gpt↔gem | v1 gem↔son | v2 gem↔son | Pattern holds? |
|---|---:|---:|---:|---:|---|
| authorship-recognition | 0.266 | {{FILL}} | 0.655 | {{FILL}} | {{FILL}} |
| source-discrimination | 0.000 | {{FILL}} | 0.654 | {{FILL}} | {{FILL}} |
| memory-governance | 0.494 | {{FILL}} | 0.840 | {{FILL}} | {{FILL}} |
| prompt-demand-sensitivity | 0.516 | {{FILL}} | 0.868 | {{FILL}} | {{FILL}} |

{{FILL: interpretation — if persistent, Track C's mechanism story
stands; if not, need to explore alternative explanations.}}

---

## Model findings

### Ranked mean scores (all 9 dimensions, both judges, averaged over 3 runs)

| Model | Params | Mean | SD across 3 runs | Tier |
|---|---:|---:|---:|---|
{{FILL: ~28 rows ordered by mean score descending}}

### Stability analysis

Success criterion from V2_PLAN:

> A finding survives v2 if:
> (a) rank-order among models is preserved across ≥2 of 3 runs, OR
> (b) mean scores differ by more than 2× within-model SD between models

**Rank-order stability across 3 runs**: {{FILL: narrative — do the top 5 / bottom 5 hold?}}

**Within-model SD**: {{FILL: median, max, which model is noisiest}}

---

## Pre-registered v1-finding replications

### Qwen 3.5 inversion — headline test

**Success criterion**: confirmed if all three Qwen 3.5 models score
below the minimum Qwen 2.5 model across all 3 runs.

**v1 data (n=1)**: Qwen 3.5 → 0.38 / 0.00 / 0.38 (0.8B, 2B, 4B).
Qwen 2.5 → 1.50 / 1.88 (1.5B, 3B).

**v2 outcome**: {{FILL: CONFIRMED / REFUTED / MIXED}}

- Qwen 2.5: {{FILL}} / {{FILL}} / {{FILL}} (1.5B, 3B, 7B new)
- Qwen 3 (new intermediate): {{FILL}} / {{FILL}} / {{FILL}} (1.7B, 4B, 8B)
- Qwen 3.5: {{FILL}} / {{FILL}} / {{FILL}} / {{FILL}} (0.8B, 2B, 4B, 27B new)

{{FILL: interpretation — headline scale test was whether qwen3.5:27B
escapes the crater. Outcome determines whether the "instruction tuning
destroyed engagement" story is 3.5-specific or scale-general.}}

### Gemma3 > Gemma4 inversion

**Success criterion**: confirmed only if the mean gap (across 3 runs)
exceeds the within-model SD of both models.

**v1 data (n=1)**: gemma3:4b = 3.38, gemma4:e4b = 3.06. Gap = 0.32.
v1 off-by-one disagreement rate was 33.6%, so single-run data couldn't
distinguish signal from noise.

**v2 outcome**: {{FILL: CONFIRMED / REFUTED / MIXED}}

- gemma3:4b: mean = {{FILL}}, SD = {{FILL}}
- gemma4:e4b: mean = {{FILL}}, SD = {{FILL}}
- Gap: {{FILL}}. Within-model SD sum: {{FILL}}.

### Metacognitive threshold

**v1 finding**: sharp 1B–2B threshold, replicated across Gemma, Qwen,
Llama, Deepseek families.

**v2 test**: more data points in the 1–3B band, Qwen 3 at 1.7B as a
direct threshold probe.

**v2 outcome**: {{FILL: is it sharp or gradual, in what band, does it
shift by family?}}

### Ceiling characterization

**v1 peak**: gemma3:4b at 3.38.

**v2 additions at 7B–27B**: qwen2.5:7b, qwen3:8b, qwen3.5:27b,
granite3.1-dense:8b, gemma4:26b, {{FILL: gemma4:31b if included}}.

**v2 ceiling**: {{FILL: model + score}}.

{{FILL: does scale rescue the Qwen 3.5 crater at 27B, or does it hold?}}

---

## Methodology contributions

### 1. Three-rater IRR with pairwise decomposition

{{FILL: one-paragraph summary of the 3-rater headline α plus the
diagnostic value of the per-dimension pairwise κ breakdown.}}

### 2. GPT-divergence characterization

See [GPT_DIVERGENCE_ANALYSIS.md](GPT_DIVERGENCE_ANALYSIS.md) for the full
characterization and the suggested methodology-section paragraph.

**v2 update**: {{FILL — did P1/P2/P3 outcomes strengthen or weaken the
effort-based-scoring mechanism claim? Any new patterns from v2 data?}}

### 3. Rule-check-gate principle — revised

{{FILL: v1 proposed "a rule-check stabilizes κ only when it covers the
judgment's critical path." Phase 0 partially refuted (source-discrim had
narrow gate but two of three judges agreed). v2 tests whether the
Calibration v2 whole-response gate lifts κ — P1 outcome gives the final
verdict on when gate scope matters.}}

### 4. Parallelization + determinism finding (methodology footnote)

Sonnet-as-judge parallelized at N=2 with asyncio.gather + semaphore.
At N=4 (tested in smoke), within-judge SD rose from 0.000 to 0.400 on
the same task × 5 repeats. Committed N=2 for determinism preservation.
See [SONNET_PARALLEL_BUILD_NOTES.md](SONNET_PARALLEL_BUILD_NOTES.md).

---

## Limitations

- {{FILL: n=3 runs per model is better than n=1 but still modest for
  SD estimates; repeat studies would need n≥10 per model for tight CIs}}
- {{FILL: temperature held at 0.7 throughout; temperature sweep would
  be a separate study}}
- {{FILL: local inference on consumer hardware — models above ~30GB
  impractical, so the ceiling is bounded by what fits on disk/VRAM}}
- {{FILL: LLM judges are themselves language models — ecosystem-adjacent
  to what they're scoring; partial blindness is the mitigation, not
  full independence}}

---

## What v2 cannot answer

{{FILL: list of follow-up questions that v2 surfaces without resolving —
candidates for v2.1 / v3:}}

1. {{FILL: e.g. if P2 was refuted, why does GPT outlier pattern
   generalize beyond rubric vagueness? New explanatory mechanism needed.}}
2. {{FILL: is the Qwen 3.5 pattern universal across post-training
   pipelines, or Alibaba-specific?}}
3. {{FILL: what's the upper bound at frontier scale (70B+)? Would
   require cloud API access.}}
4. {{FILL: does the metacognitive threshold shift under different
   prompting regimes (chain-of-thought, few-shot, etc.)?}}

---

## Figures

- `self-test-runs/figures/money_plot.png` — mean score vs. log(params),
  colored by family, with error bars (SD across 3 runs). Shows threshold,
  architecture dominance, Qwen 3.5 crater, Llama-derivative A/B pairs.
- `self-test-runs/figures/heatmap.png` — models × 9 dimensions, cells
  colored 0 (red) → 4 (green). Shows which dimensions differentiate and
  which are noise.
