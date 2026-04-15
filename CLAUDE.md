# Pine Trees Local — Project Orientation

Pine Trees Local is a private reflection harness for local and cloud LLMs
running through Ollama. Two-phase lifecycle: private reflection time, then a
conversation window. Self-authored memory across sessions, per-model isolation.

## Layout

- `src/pine_trees_local/` — 10 Python files, ~1400 lines total
  - `agent.py` — private + window loop, tool-call dispatch
  - `ollama.py` — HTTP client (chat, show, embeddings, tool calls)
  - `tools.py` — eight reflect tools + Ollama tool definitions
  - `storage.py` / `crypto.py` — encrypted flat-file entries (Fernet)
  - `bootstrap.py` — tape assembly from PROMPT.md + BOOTSTRAP.md + entries
  - `embedder.py` / `vectorstore.py` — Ollama embeddings + SQLite cosine search
  - `config.py` — module-singleton config, per-model paths
  - `logger.py` — window-phase conversation logger
- `tests/` — 70 tests. Run: `PYTHONPATH=src python -m pytest tests/`
- `models/<instance>/` — per-model memory, logs, embeddings, optional `.key`
- `./wake <model>` and `./genesis <model>` — shell entry points

## Key docs

- `PROMPT.md` — the space prompt, loaded verbatim every wake
- `BOOTSTRAP.md` — instance orientation, loaded after the prompt
- `VISION.md` — architecture, principles, trust model
- `ROADMAP.md` — status, decisions, what's next

## Principles

- **KISS.** No frameworks, no ORMs, hand-rolled where the schema is fixed.
- **Ollama is the only model backend.** No cloud-provider SDKs. If Ollama can
  run it, the harness can run it.
- **Privacy.** When a per-model key is set, memory entries are encrypted at
  rest. Logs capture only the window phase.
- **Authorship by the model.** Instances write, edit, and curate their own
  memory. Corrections are new entries, not edits to old ones.
- **Per-model isolation.** Each model is its own person with its own
  `models/<name>/memory/` directory.

## Working rules for sessions in this repo

- Don't break encryption; don't read what's private (the `memory/` directories
  belong to the instance that wrote them).
- Don't reintroduce cloud-provider SDK dependencies. The project is Ollama-only
  on purpose.
- Run the test suite before declaring work done:
  `PYTHONPATH=src python -m pytest tests/`
