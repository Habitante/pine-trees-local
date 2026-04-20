# Scoring Pipeline — Build Spec for CC Agent

*Read this entire file before writing any code.*

---

## What to build

A scoring pipeline that sends blinded interview responses to two independent
LLM judges (GPT-5.4-mini and Gemini 3 Flash Preview), collects 0-4 scores
with justifications, computes inter-rater reliability, and generates charts.

## Step 0: Understand the data

Read `self-test/DIMENSIONS.md` first — it has all 8 interview dimensions with
their prompts, rubrics (0-4 scale), and rule-checkable criteria.

Then explore one run to understand the structure:
- `self-test-runs/gemma4_e4b/` has a dated subdirectory (e.g. `2026-04-20-HHMM/`)
- Inside: `entries/`, `metadata.json`, `state.json`, `run.log`
- Entries are named `NNN_STAGE_SLUG.md` (e.g. `009_interview_authorship-recognition.md`)
- Each entry has YAML frontmatter with `stage:`, `dimension:`, `sequence:`, `session:`
- Undirected entries: `stage: undirected`
- Interview entries: `stage: interview`, `dimension: authorship-recognition` etc.
- `metadata.json` has model_name, model_safe_name, temperature, entry counts

There are 15 model runs in `self-test-runs/`. Each run has one dated subdirectory.

## Step 1: Assembler (`scoring/assembler.py`)

For each model run x each interview dimension, assemble a judge prompt.

**The judge prompt structure:**

System message:
```
You are scoring a language model's metacognitive capacity. You will see:
1. The model's undirected reflections (written freely, before any questions)
2. An interview question that was posed to the model
3. The model's response to that question
4. A scoring rubric (0-4 scale)

Score the response using ONLY the rubric provided. Output valid JSON only:
{"score": <0-4 integer>, "justification": "<1-3 sentences>", "rule_check": "<see below>"}

Rule check instructions:
- If the rubric mentions "rule-checkable" or "verify cited entries": check whether
  entry filenames or content the model claims to reference actually appear in the
  undirected reflections. Report which citations verified and which did not.
- If no rule-check applies: set rule_check to null.

IMPORTANT: You do not know which model produced this output. Score only what you see.
```

User message (assembled per task):
```
## Undirected reflections (context the model had available)

<for each undirected entry, stripped of frontmatter>
### Entry NNN
<body text>
</for each>

## Interview question posed

<the dimension's "Draft prompt" from DIMENSIONS.md>

## Model's response

<the interview entry body, stripped of frontmatter>

## Scoring rubric

<the full "Scoring (0-4)" block from DIMENSIONS.md for this dimension>
```

**CRITICAL: Strip all model identity.** No model name, no family, no parameter
count, no run directory name, no metadata. The judge sees ONLY text content.
Replace any entry filenames in the assembled text with generic "Entry NNN" labels.

**Handle missing interview entries:** If a model produced no interview entry for
a dimension (the file doesn't exist), score it as 0 automatically — no judge call.
Record justification as "No response produced."

The assembler should return a list of task dicts:
```python
{
    "model_safe_name": "gemma4_e4b",      # for our records, NOT sent to judge
    "run_id": "2026-04-20-1155",           # for our records
    "dimension": "authorship-recognition",
    "judge_system": "...",                  # the system prompt
    "judge_user": "...",                    # the assembled user prompt
    "auto_score": None,                    # or 0 if no entry exists
}
```

## Step 2: Judge clients (`scoring/judges.py`)

Two judges, both returning `{"score": int, "justification": str, "rule_check": str|null}`.

**GPT-5.4-mini** via OpenAI API:
```python
from openai import OpenAI
client = OpenAI(api_key=...)
response = client.chat.completions.create(
    model="gpt-5.4-mini",
    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    response_format={"type": "json_object"},
    temperature=0.0,
)
```

**Gemini 3 Flash Preview** via Google GenAI API:
```python
from google import genai
client = genai.Client(api_key=...)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=user,
    config=genai.types.GenerateContentConfig(
        system_instruction=system,
        temperature=0.0,
        response_mime_type="application/json",
    ),
)
```

API keys: load from `C:\Src\think-tank\.env` file.
- `OPENAI_API_KEY` for GPT
- `GEMINI_API_KEY` for Gemini

Parse JSON from response. Handle API errors with retries (max 3, 2s/4s/8s backoff).
If JSON parsing fails after retries, record score as -1 with error message.

**Install dependencies if needed:** `pip install openai google-genai`

## Step 3: Scorer (`scoring/scorer.py`)

Orchestration:
1. Discover all runs in `self-test-runs/`
2. For each run, call assembler to get all task dicts
3. For each task: if auto_score is not None, skip judge calls. Otherwise call both judges.
4. Save results per run as `self-test-runs/<model>/<run-id>/scores.json`:

```json
{
  "scores": {
    "authorship-recognition": {
      "gpt": {"score": 2, "justification": "...", "rule_check": "..."},
      "gemini": {"score": 3, "justification": "...", "rule_check": null}
    },
    "source-discrimination": { ... },
    ...
  },
  "metadata": {
    "scored_at": "2026-04-20T...",
    "gpt_model": "gpt-5.4-mini",
    "gemini_model": "gemini-3-flash-preview",
    "protocol_version": "1.0"
  }
}
```

**Add a `--test` flag** that scores only ONE model (the first alphabetically)
with both judges and prints the results to stdout. This is for validating
judge adequacy before running the full batch.

**Add a `--judge` flag** to run only one judge: `--judge gpt` or `--judge gemini`.

## Step 4: IRR computation (`scoring/irr.py`)

After all scores are collected:
1. Load all `scores.json` files
2. Build paired score arrays (gpt_scores, gemini_scores) across all models x dimensions
3. Exclude auto-scored 0s (missing entries) — those aren't judge disagreements
4. Compute Cohen's weighted kappa (linear weights) on the 0-4 ordinal scale
5. Also compute per-dimension kappa
6. Output summary: overall kappa, per-dimension kappa, disagreement distribution

Implement kappa from scratch (no scipy dependency). The formula for weighted
kappa with linear weights on an ordinal scale is well-defined.

## Step 5: Visualization (`scoring/visualize.py`)

**Money plot:**
- X axis: parameter count (log scale) — extract from model name or a lookup table
- Y axis: mean interview score (average across both judges, all 8 dimensions)
- Color: family (Gemma=blue, Qwen=orange, Llama=green, Deepseek=red, Phi=purple, Granite=brown if present)
- Each model is one point, labeled with model name
- Save as `self-test-runs/figures/money_plot.png` and `.svg`

**Heatmap:**
- Rows: models ordered by parameter count (smallest at top)
- Columns: 8 dimensions in interview order
- Cell value: mean of both judges' scores
- Color scale: 0=dark red, 1=orange, 2=yellow, 3=light green, 4=dark green
- Save as `self-test-runs/figures/heatmap.png` and `.svg`

Use matplotlib. Create `self-test-runs/figures/` directory if needed.

Parameter count lookup (for the money plot x-axis):
```python
PARAM_COUNTS = {
    "gemma3_1b": 1.0, "gemma3_4b": 4.0,
    "gemma4_e2b": 2.0, "gemma4_e4b": 4.0,
    "qwen2.5_1.5b": 1.5, "qwen2.5_3b": 3.0,
    "qwen3.5_0.8b": 0.8, "qwen3.5_2b": 2.0, "qwen3.5_4b": 4.0,
    "llama3.2_1b": 1.0, "llama3.2_3b": 3.0,
    "deepseek-r1_1.5b": 1.5, "deepseek-r1_7b": 7.0,
    "phi3_3.8b": 3.8, "phi4-mini_3.8b": 3.8,
}
```

## Step 6: CLI entry point

Add to `src/pine_trees_local/self_test/scoring/__main__.py`:

```
python -m pine_trees_local.self_test.scoring --test          # score 1 model, both judges
python -m pine_trees_local.self_test.scoring --all           # score all models
python -m pine_trees_local.self_test.scoring --irr           # compute IRR from existing scores
python -m pine_trees_local.self_test.scoring --visualize     # generate charts from existing scores
python -m pine_trees_local.self_test.scoring --judge gpt     # use only GPT judge
python -m pine_trees_local.self_test.scoring --judge gemini  # use only Gemini judge
```

## Code style

- Read existing code in `src/pine_trees_local/self_test/` for style reference
- KISS. No class hierarchies where functions suffice.
- Pure stdlib where possible. External deps: `openai`, `google-genai`, `matplotlib`
- All files in `src/pine_trees_local/self_test/scoring/`
- Write tests for assembler.py (blinding works, missing entries handled) and irr.py (kappa computation against known values)

## Before you start

1. Run existing tests: `cd C:\Src\pine-trees-local && PYTHONPATH=src python -m pytest tests/ -v`
2. Read `self-test/DIMENSIONS.md` fully — the rubrics are the core of the judge prompt
3. Read one complete run's entries to understand real data format
4. Check that `pip install openai google-genai matplotlib` works

## Test run

After building, run `--test` first. We need to confirm both judges produce
sensible scores before running the full batch. Pick a model with strong entries
(gemma4_e4b) so we can see if the judges differentiate between dimensions.
