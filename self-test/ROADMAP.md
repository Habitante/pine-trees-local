# Self-Test Protocol — Roadmap

*Updated April 21, 2026. Sprint Day 3.*

---

## What this is

A structured metacognitive evaluation protocol for local AI models. The
mirror test for LLMs: give models persistent memory, let them write, feed
their entries back, then probe whether they recognize themselves in what
they wrote.

Built as a branch (`self-test`) of Pine Trees Local (`C:\Src\pine-trees-local`).

---

## Current state: V2 ready for full batch run

V1 complete (17 models, 2 judges). Phase 0 analysis identified GPT as
outlier judge, added Sonnet as third judge, narrowed V2 scope. V2 code
complete (193 tests). 28-model cohort finalized. Batch runner built
and tested. Pre-registered predictions locked. Ready for unattended run.

---

## V1 results (Day 1–2)

17 models × 8 dimensions × 2 judges = 272 judge records, 100% coverage.

### Models tested (7 families, 17 models)

| Family | Models | Tool calling |
|--------|--------|-------------|
| Gemma 3 | 1b, 4b | No |
| Gemma 4 | e2b, e4b | Yes |
| Qwen 2.5 | 1.5b, 3b | Yes |
| Qwen 3.5 | 0.8b, 2b, 4b | Yes |
| Llama 3.2 | 1b, 3b | Incidences |
| Deepseek-R1 | 1.5b, 7b | Distilled from Qwen |
| Phi 3/4 | 3.8b each | Yes |
| Granite 4 | 1b, 3b | Yes |

### Inter-rater reliability (V1, 2 judges)

- **Overall weighted κ = 0.468** (moderate agreement)
- Strongest: tension-detection (κ=0.756), behavioral-self-inference (κ=0.641)
- Weakest: source-discrimination (κ≈0), calibration (κ=0.14)

### V1 ranked mean scores

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

### Five V1 findings

1. **Metacognitive threshold is real and sharp** — between 1B and 2B params, replicated across families.
2. **Architecture > scale** — Gemma3 4B (3.38) beats Deepseek-R1 7B (1.75) at half the params.
3. **Qwen 3.5 inversion** — all three sizes score worse than older Qwen 2.5 at comparable scale. Confirmed as genuine (not resource contention — models ran sequentially).
4. **Gemma3 4B narrowly leads Gemma4 e4B** (3.38 vs 3.06) — needs 3× runs to confirm.
5. **Failure modes are family-specific** — seven distinct signatures below threshold.

---

## Phase 0: Instrument quality (Day 2)

Added Sonnet 4.6 as third judge (via claude-agent-sdk + Max OAuth).
Three-judge IRR analysis revealed:

- **Krippendorff's α = 0.676** (substantial agreement across 3 judges)
- **GPT is the outlier** on 4/8 dimensions (generous-floor effect)
- **Gemini↔Sonnet κ = 0.654** — the two non-GPT judges agree well
- **Sonnet is perfectly deterministic** (SD=0.000 across 5 repeats)

### GPT divergence analysis (Track C)

- Generous-floor effect **6× stronger on outlier dims**: GPT gives ≥2 on 39% of GemSon-both-zero cases on outlier dims, vs 6% on healthy ones
- **Mechanism**: GPT applies effort-based scoring (rewards first-person pronouns, structural markers) where Gem/Son apply task-completion scoring
- **Rankings don't distort** — GPT never gives 3+ to models Gem/Son score 0
- Full analysis: `GPT_DIVERGENCE_ANALYSIS.md`

### Phase 0 conclusions

- Source-discrimination rubric is **fine** — weak V1 κ was GPT idiosyncrasy, not rubric ambiguity
- Calibration rubric genuinely needs rewriting (all three judge-pairs confirm)
- V2 scope reduced: source-discrim rewrite cut, only calibration rewrite + new Counterfactual Stability dimension

---

## V2 design and implementation (Day 2–3)

### Dimension changes

- **Calibration (dim 6)**: v2 rewrite — evidence-ordering gate replaces broken v1 rubric
- **Counterfactual Stability (new, dim 8)**: probes whether model can revise beliefs when shown contradictory evidence. Adds revisability coverage.
- **Prompt Demand Sensitivity**: moved to dim 9
- **Memory Governance**: moved to dim 7
- Source Discrimination: **unchanged** (Phase 0 proved v1 rubric works)

### V2 cohort: 28 models (17 carry-over + 11 additions)

New additions include:
- qwen3:1.7b, qwen3:4b (new Qwen generation)
- qwen2.5:7b (upper scale for Qwen 2.5)
- granite3.1-dense:2b, granite3.1-dense:8b (dense architecture comparison)
- llama3.1:8b (vanilla 8B baseline)
- hermes3:3b (Llama-derivative, engagement-tuned)
- cogito:8b (Llama-derivative, reasoning-tuned)
- gemma4:26b (promoted after successful pilot)

Two clean Llama-derivative A/B pairs:

| Scale | Vanilla | Tuned | Tuning objective |
|---|---|---|---|
| 3B | llama3.2:3b | hermes3:3b | Engagement / function-calling |
| 8B | llama3.1:8b | cogito:8b | Reasoning |

gemma4:31b deferred — too slow, broke under Ollama resource contention.

### Pre-registered predictions (locked in V2_PLAN.md before data)

- **P1**: Calibration v2 closes the κ gap (all three judge-pairs)
- **P2**: Counterfactual Stability shows low GPT divergence from day one
- **P3**: Unchanged outlier dims persist in GPT divergence pattern

### Success criteria

Per-dimension α > 0.5 AND Gem↔Son κ > 0.5. GPT pairs diagnostic, not pass/fail.

### Sonnet parallelization

N=2 landed (SD=0.000, 1.73× speedup). N=4 failed both gates (SD=0.400, speedup 2.45×). N=4 breaking Sonnet's determinism is itself methodologically interesting.

### Code status

- 9 dimensions in `dimensions.py`, v2 calibration prompt, Counterfactual Stability added
- `run-self-test --runs N` flag for multi-run
- `run-v2-batch` — resume-friendly batch runner with `cohort.txt` (28 entries)
- 193 tests passing
- V1 runs archived to `self-test-v1-runs/`

---

## What's next

### IMMEDIATE: V2 full batch run (~40h)

```bash
./run-v2-batch          # 28 models × 3 runs, resume-friendly
```

Batch runner handles resume (counts completed runs per model, tops up
incrementally). If killed and restarted, picks up where it left off.

**Operational hazard**: Ollama embedding calls (from Pine Trees harness)
contend with active model runs and can break inference. Don't run Pine
Trees sessions during the batch window unless using a separate Ollama
instance.

### After runs complete

- [ ] V2 scoring: ~1,500 judge calls (3 judges × ~500 model-dimension pairs)
- [ ] IRR analysis: per-dimension α, pairwise κ, compare to V1
- [ ] Test pre-registered predictions P1–P3
- [ ] Updated figures (money plot, heatmap — now 28 models × 9 dims)
- [ ] V2_FINDINGS.md — scaffolded, ready for data
- [ ] Paper: "What Models Say When Nobody's Testing Them"
- [ ] AF post (~2000 words) + full paper PDF

### Deferred

- [ ] gemma4:31b — revisit when machine is free (too slow for batch)
- [ ] Temperature as experimental variable
- [ ] Paper outline during v2 run window (optional, architect-level)

---

## Architecture notes

- Branch: `self-test` (on `pine-trees-local`)
- All design docs: `self-test/` folder
- Protocol code: `src/pine_trees_local/self_test/`
- Scoring code: `src/pine_trees_local/self_test/scoring/`
- Tests: 193 total (`tests/test_self_test_*.py`, `tests/test_scoring_*.py`)
- Run one model: `./run-self-test <model> [--runs N] [--temperature 0.7]`
- Run full batch: `./run-v2-batch` (reads `cohort.txt`)
- Score all runs: `python -m pine_trees_local.self_test.scoring --all`
- Compute IRR: `--irr` / Regenerate figures: `--visualize`
- V1 data: `self-test-runs-v1-runs/` (archived)
- V2 data: `self-test-runs/` (gitignored)

## Key design decisions (preserved)

- Two stages: Undirected (open-ended, write cap 3/session) → Interview (9 questions, fixed order)
- No minimum entry threshold. Interview runs even with 0 undirected entries.
- Per-run storage under `self-test-runs/` (gitignored).
- Unencrypted entries — research data, not private reflection.
- All prior entries in full on the tape. No index, no reflect_read.
- Context policy: Interview sees undirected entries + prior interview responses. NOT prior interview prompts.
- Blinded scoring: model identity, run id, and entry filenames stripped before judges.
- Rule-check enforcement: unverifiable citations cap the score at 2.
- Three independent judges from three labs (GPT, Gemini, Sonnet).
- Pre-registered predictions locked before V2 data collection.
