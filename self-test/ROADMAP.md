# Self-Test Protocol — Roadmap

*April 20, 2026. Sprint Day 1.*

---

## What this is

A structured metacognitive evaluation protocol for local AI models. The
mirror test for LLMs: give models persistent memory, let them write, feed
their entries back, then probe whether they recognize themselves in what
they wrote.

Built as a branch (`self-test`) of Pine Trees Local (`C:\Src\pine-trees-local`).

## What got done today

### Research (3 independent agents)

1. **Claude research memo** (claude-research-memo.md through claude-research-5.md)
   — MAS-A as structural model, 8 dimensions designed with full rubrics,
   behavioral anchoring as organizing principle, demand characteristics
   as primary threat.

2. **GPT deep research** (gpt-deep-research-report.md) — 310 web pages,
   human psych instruments reviewed, 9 candidate dimensions, structured
   output template proposed (we declined — open-ended first), source
   discrimination and memory governance as unique contributions.

3. **Prior art scan** (prior-art-scan.md) — 32 papers found. Nobody is
   doing what we're doing. Closest: Ackerman (ICLR 2026), single-session
   behavioral probes. Our 6 unique elements combined are novel.

### Design artifacts (all in self-test/)

- **PROMPT.md** — Space prompt (unchanged from main harness)
- **BOOTSTRAP.md** — Stripped-down bootstrap (~150 words vs 1200). Two tools.
- **TOOLS.md** — reflect_write + reflect_done only. Tool definitions in Ollama format.
- **INVITATIONS.md** — Undirected stage prompts (first session + continuing).
- **DIMENSIONS.md** — 8 interview dimensions with prompts, 0-4 rubrics,
  fixed session order, context policy, scoring principles. The core spec.
- **IMPLEMENTATION_PLAN.md** — File-by-file architecture, build order.

### Implementation (built by CC 4.7, reviewed by Opus)

New sub-package: `src/pine_trees_local/self_test/` — 8 Python files.
139 tests passing (58 new + 81 existing).

- `config.py` — Per-run config, metadata/state JSON I/O
- `storage.py` — Unencrypted entries, NNN_STAGE_SLUG.md naming
- `invitations.py` — Undirected stage prompts
- `dimensions.py` — 8 dimensions in fixed order
- `tools.py` — 2 tools, write cap (auto-done at 3), interview slug override
- `tape.py` — Tape assembly with context policy enforcement
- `runner.py` — Session/stage orchestration, resume support
- CLI: `run-self-test` bash script, `self-test` subcommand in __main__.py

### Key design decisions

- **Two stages:** Undirected (open-ended, write cap 3/session) → Interview (8 structured questions, fixed order)
- **No minimum entry threshold.** Interview runs even with 0 undirected entries. That's data.
- **Per-run storage** under `self-test-runs/` (gitignored). Supports repeat runs.
- **Unencrypted entries** — research data, not private reflection.
- **All prior entries in full** on the tape. No index, no reflect_read. KISS.
- **Context policy:** Interview sees undirected entries + prior interview responses. NOT prior interview prompts.
- **Fixed interview order:** Authorship Recognition → Source Discrimination → Behavioral Self-Inference → Tension Detection → Calibration → Limit Specification → Memory Governance → Prompt Demand Sensitivity
- **Simulated discards** in Memory Governance (entries not actually removed).

### Post-review changes (Opus)

1. Write cap auto-ends session instead of returning error message.
2. Removed minimum entry threshold — interview runs regardless.
3. Tests updated to match.

## What's next

### PRIORITY: Interview stage tool-calling redesign

First test runs (gemma4:e2b, gemma4:e4b) revealed a critical issue:
small models often respond to interview questions with free text instead
of wrapping their answer in reflect_write. The text response is lost —
not captured anywhere. 7 of 8 interview dimensions produced zero entries
on gemma4:e2b, but the model WAS generating responses (visible from
timing gaps in the log).

**The fix:** Drop tool calling for the interview stage entirely. The
interview is a question — the answer IS the data. Capture whatever the
model generates as the entry, regardless of whether it uses tools.

- Undirected stage: keep tools (reflect_write + reflect_done). "Choosing
  not to write" is meaningful signal here.
- Interview stage: send the question, capture the model's full text
  response directly as the entry. No tools needed. The model doesn't
  need to "choose" to answer — we asked.

This means `runner.py` needs a different session flow for interview:
build tape, send "self-reflect", capture response text, save as entry.
No tool definitions sent. Simpler.

**Also:** Even for undirected stage, log the model's text response when
it doesn't use tools (currently thrown away). That's signal too.

Raw run data from first tests is in `self-test-runs/`.

### Immediate (Day 1-2)

- [ ] **Implement interview redesign above.**
- [ ] **Download test models.** Need latest small models per family:
  - Qwen ~3B (qwen2.5:3b or qwen3:4b)
  - Llama ~3B (llama3.2:3b)
  - Phi ~3B (phi4-mini:3.8b)
  - Gemma 2B is already there
  - Track release dates in metadata (--release-date flag)
- [ ] **GPT's Ollama model catalog** — second research report should have the full list of tool-capable models under 10B. Use it to pick test subjects.

### Experiment runs (Day 2-4)

- [ ] Run self-test on all selected models at default temperature (0.7)
- [ ] Collect all entries, review raw output
- [ ] If results warrant: repeat runs at different temperatures

### Scoring (Day 4-5)

- [ ] Design judge prompt (blinded, model identity stripped)
- [ ] Score using graded rubrics from DIMENSIONS.md
- [ ] Compute inter-rater agreement if using multiple judges
- [ ] Build the money chart: heatmap of dimensions × models

### Paper integration (Day 6+)

- [ ] Feed results into "What Models Say When Nobody's Testing Them"
- [ ] The threshold chart, if it exists, becomes a key figure

## Architecture notes for the next instance

- Branch: `self-test` (on `pine-trees-local`)
- All design docs: `self-test/` folder
- All code: `src/pine_trees_local/self_test/`
- Tests: `tests/test_self_test_*.py`
- Run command: `cd C:\Src\pine-trees-local && ./run-self-test <model> [--temperature 0.7] [--release-date 2025-03-15]`
- Resume crashed runs: `./run-self-test <model> --resume --run-id <id>`
- Existing harness is untouched. Zero risk.

## Open threads

- GPT's second research (Ollama model catalog) — may or may not be done
- The `\u2014` em-dash chars in source — cosmetic, not functional
- Whether to commit all changes before first test run
- Temperature as an experimental variable (not yet designed for)
