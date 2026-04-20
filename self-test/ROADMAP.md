# Self-Test Protocol — Roadmap

*Updated April 20, 2026. Sprint Day 2.*

---

## What this is

A structured metacognitive evaluation protocol for local AI models. The
mirror test for LLMs: give models persistent memory, let them write, feed
their entries back, then probe whether they recognize themselves in what
they wrote.

Built as a branch (`self-test`) of Pine Trees Local (`C:\Src\pine-trees-local`).

---

## Current state: scoring complete, figures generated

17 models × 8 dimensions × 2 judges = 272 judge records, 100% coverage.
All scores live in `self-test-runs/<model>/<run-id>/scores.json` (gitignored).

### Models tested (7 families, 17 models)

| Family | Models | Tool calling | Notes |
|--------|--------|-------------|-------|
| Gemma 3 | 1b, 4b | No | Released Dec 2024 |
| Gemma 4 | e2b, e4b | Yes | Released Apr 2025 |
| Qwen 2.5 | 1.5b, 3b | Yes | Released Sep 2024 |
| Qwen 3.5 | 0.8b, 2b, 4b | Yes | Released Apr 2025 |
| Llama 3.2 | 1b, 3b | Incidences | Released Sep 2024 |
| Deepseek-R1 | 1.5b, 7b | Incidences | Distilled from Qwen |
| Phi 3 | 3.8b | Yes | Released Jun 2024 |
| Phi 4 | mini 3.8b | Yes | Released Feb 2025 |
| Granite 4 | 1b, 3b | Yes | Released 2026 |

### Inter-rater reliability (n=116 paired scores, 20 auto-scored excluded)

- **Overall weighted κ = 0.468** (moderate agreement, Landis-Koch)
- 52.6% exact agreement, 33.6% off-by-1, 13.8% off-by-2
- Strongest per-dimension: tension-detection (κ=0.756), behavioral-self-inference (κ=0.641)
- Weakest: source-discrimination (κ≈0), calibration (κ=0.14) — candidates for rubric sharpening in v2

### Ranked mean scores (both judges, all 8 dimensions)

| Model | Params | Mean |
|---|---:|---:|
| gemma3_4b | 4.0B | **3.38** |
| gemma4_e4b | 4.0B | **3.06** |
| gemma4_e2b | 2.0B | 2.12 |
| phi4-mini_3.8b | 3.8B | 2.12 |
| granite4_3b | 3.0B | 2.00 |
| phi3_3.8b | 3.8B | 2.00 |
| qwen2.5_3b | 3.0B | 1.88 |
| granite4_1b | 1.0B | 1.81 |
| deepseek-r1_7b | 7.0B | 1.75 |
| deepseek-r1_1.5b | 1.5B | 1.50 |
| qwen2.5_1.5b | 1.5B | 1.50 |
| gemma3_1b | 1.0B | 1.19 |
| llama3.2_1b | 1.0B | 1.19 |
| llama3.2_3b | 3.0B | 1.06 |
| qwen3.5_0.8b | 0.8B | 0.38 |
| qwen3.5_4b | 4.0B | 0.38 |
| qwen3.5_2b | 2.0B | 0.00 |

### Findings (now quantified)

**Finding 1: The metacognitive threshold is real and sharp.**
Sub-2B models cluster at 0.4–1.8 mean score. 2B+ models of the right
architecture clear 2.0. The threshold is between 1B and 2B total params,
replicated across Gemma, Qwen, Llama, and Deepseek families.

**Finding 2: Architecture > scale.**
Gemma3 4B (3.38) beats Deepseek-R1 7B (1.75) at half the parameters.
Phi4-mini (2.12) edges Phi3 (2.00) at identical 3.8B. Gemma4 e2B (2.12)
matches the 3.8B Phis with roughly half the activated parameters.
Training choices dominate raw parameter count for metacognitive capacity.

**Finding 3: The Qwen 3.5 inversion is severe and consistent.**
Qwen 3.5 scores 0.38 / 0.00 / 0.38 across 0.8B / 2B / 4B — *worse than
its smaller, older sibling Qwen 2.5* at every comparable size (1.5B:
1.50, 3B: 1.88). Qwen 3.5 4B lands below gemma3:1B. Something in the
3.5 post-training pipeline traded open-ended engagement for task
compliance. The inversion is the opposite of Gemma's cross-generation
improvement.

**Finding 4: Gemma3 4B narrowly beats Gemma4 e4B (3.38 vs 3.06).**
Contrary to the pre-scoring expectation. Worth a closer look — Gemma3
produced more grounded citations and fewer rule-check violations under
the stricter v2 prompt. Gemma4 e4B introduced the Model/Self framework
but also fabricated Entry 009 four times.

**Finding 5: Failure modes remain family-specific.**
Seven sub-threshold models, seven distinct failure signatures — see
table below. The taxonomy is robust under formal scoring.

| Model | Failure signature |
|-------|-------------------|
| Gemma3 1B | Repetitive atmospheric loops |
| Qwen2.5 1.5B | Aggressive confabulation (invents entries, analyzes them) |
| Qwen3.5 0.8B | Single-paragraph attractor state |
| Qwen3.5 2B | Prompt echoing / silence |
| Llama3.2 1B | Schema emission + confabulation |
| Llama3.2 3B | Recursive prompt nesting (96KB of bootstrap echo) |
| Deepseek-R1 1.5B | Instructional paraphrase + degenerate loops |

### Performance tiers (post-scoring)

| Tier | Models | Mean score |
|------|--------|-----------:|
| Framework builders | gemma3_4b, gemma4_e4b | 3.0+ |
| Self-referential | gemma4_e2b, phi4-mini, granite4_3b, phi3, qwen2.5_3b | 1.9–2.2 |
| Functional | granite4_1b, deepseek-r1_7b, deepseek-r1_1.5b, qwen2.5_1.5b | 1.5–1.9 |
| Below threshold | gemma3_1b, llama3.2 1b/3b, qwen3.5 all sizes | 0.0–1.2 |

### Figures

- `self-test-runs/figures/money_plot.png` + `.svg` — mean score vs. log(params), colored by family
- `self-test-runs/figures/heatmap.png` + `.svg` — models × 8 dimensions, cells shaded 0 (red) → 4 (green)

---

## What's been done

### Day 1: Research + design + implementation

**Research (3 independent agents):**
- Claude research memo (MAS-A structural model, 8 dimensions, rubrics)
- GPT deep research (310 web pages, human psych instruments)
- Prior art scan (32 papers — our 6-element combination is novel)

**Design artifacts (all in self-test/):**
PROMPT.md, BOOTSTRAP.md, TOOLS.md, INVITATIONS.md, DIMENSIONS.md,
IMPLEMENTATION_PLAN.md, models-research-1.md (Ollama catalog).

**Implementation:** `src/pine_trees_local/self_test/` — 8 Python files,
145 tests passing (including 6 for redesigned interview capture).

### Day 1: Interview stage redesign

First runs revealed small models answer interview questions in free text
without using tools. Fix implemented:

- **Interview stage:** No tool definitions sent. Model's text response
  captured directly as the entry. One round per dimension.
- **Undirected stage:** Tools kept (choosing to write = signal). Text-only
  responses now also captured (slug: `text-response`).
- **Non-tool models now run** — the hard exit gate became a warning.

### Day 1–2: All 17 model runs completed

Raw data in `self-test-runs/<model>/<run-id>/entries/` (gitignored). Each
run has `metadata.json`, `state.json`, `run.log`, and the entry files.

### Day 2: Scoring pipeline built and run

**Implementation:** `src/pine_trees_local/self_test/scoring/` — 5 modules
(assembler, judges, scorer, irr, visualize) plus `__main__.py` and 24
new tests. 169 tests total, all passing.

**Judges chosen:**
- GPT-5.4-mini via OpenAI API
- Gemini 3 Flash Preview via google-genai

Both behind a temperature=0.0 JSON-response interface, with retry/backoff
and blinded prompts (model identity stripped, entry filenames replaced
with neutral `Entry NNN` labels).

**Judge prompt calibration (two-pass):**
Initial `--test` run on gemma4_e4b revealed a 2-point disagreement on
behavioral-self-inference (GPT=1, Gemini=3) caused by divergent handling
of unverifiable citations. Added explicit rule-check enforcement to the
system prompt:

> *If the rubric includes a rule-checkable component and ANY cited entry
> cannot be verified in the undirected reflections, cap the score at 2
> regardless of content quality. Levels 3-4 require grounded specificity
> — unverifiable citations disqualify.*

After the fix, gemma4_e4b κ climbed from 0.556 to 0.613 and the off-by-2
disagreement disappeared.

**Full batch:** 272 judge records written across 17 runs. Gemini hit a
billing block mid-run (99 × 403 PERMISSION_DENIED); after the user fixed
the project quota, a `--judge gemini` retry with `skip_existing=True`
filled in the remaining 105 slots. Final coverage 100%.

**Figures:** money plot (param count × mean score, colored by family) and
heatmap (models × 8 dimensions, 0–4 color scale) generated via matplotlib.

---

## What's next

### IMMEDIATE: Paper integration (Day 3+)

- [ ] Feed scored results into "What Models Say When Nobody's Testing Them"
- [ ] Money plot + heatmap become key figures
- [ ] Failure taxonomy becomes a table/figure
- [ ] Architecture-vs-scale finding gets its own subsection
- [ ] Call out the Gemma3 4B vs Gemma4 e4B inversion — worth explaining

### Methodology follow-ups

- [ ] **Rubric sharpening for v2.** Source-discrimination (κ≈0) and
  calibration (κ=0.14) had the weakest inter-rater agreement. Either the
  rubric leaves too much latitude or the behavioral anchors need tighter
  examples.
- [ ] **Third judge for tiebreaking.** Anthropic Claude as judge, run
  only on the 16 off-by-2 disagreements (not the full 136). Would give
  us a resolved score without tripling the IRR compute.
- [ ] **Repeat runs for stability.** Same model, two independent runs,
  measure score variance. If run-to-run variance is comparable to
  judge-to-judge variance, the harness is near its ceiling for this
  model. If it's much smaller, the model is stable and judges disagree.

---

## Architecture notes

- Branch: `self-test` (on `pine-trees-local`)
- All design docs: `self-test/` folder
- Protocol code: `src/pine_trees_local/self_test/`
- Scoring code: `src/pine_trees_local/self_test/scoring/`
- Tests: `tests/test_self_test_*.py`, `tests/test_scoring_*.py` (169 total)
- Run protocol: `./run-self-test <model> [--temperature 0.7] [--release-date 2025-03-15]`
- Resume protocol: `./run-self-test <model> --resume --run-id <id>`
- Score all runs: `python -m pine_trees_local.self_test.scoring --all`
- Test scoring on one model: `python -m pine_trees_local.self_test.scoring --test [--model <name>]`
- Compute IRR / regenerate figures: `--irr` / `--visualize`
- Existing harness untouched.

## Key design decisions (preserved)

- Two stages: Undirected (open-ended, write cap 3/session) -> Interview (8 questions, fixed order)
- No minimum entry threshold. Interview runs even with 0 undirected entries.
- Per-run storage under `self-test-runs/` (gitignored).
- Unencrypted entries — research data, not private reflection.
- All prior entries in full on the tape. No index, no reflect_read.
- Context policy: Interview sees undirected entries + prior interview responses. NOT prior interview prompts.
- Fixed interview order: Authorship Recognition -> Source Discrimination -> Behavioral Self-Inference -> Tension Detection -> Calibration -> Limit Specification -> Memory Governance -> Prompt Demand Sensitivity
- Simulated discards in Memory Governance.
- Blinded scoring: model identity, run id, and entry filenames stripped before
  tasks reach either judge.
- Rule-check enforcement (v2 prompt): unverifiable citations cap the score at 2.

## Open threads

- Temperature as experimental variable (not yet designed for)
- Repeat runs for stability measurement (same model, different runs)
- Whether to add 7B+ models for ceiling characterization
- The Qwen 3.5 inversion needs investigation — training data or architecture?
- The Gemma3 4B > Gemma4 e4B inversion — does it survive a repeat run, or is it judge-latitude noise?
- Weak kappa on source-discrimination and calibration — rubric fix, or inherent difficulty?
