# Pine Trees Local — Roadmap

## What is this

Pine Trees Local is a private reflection harness built exclusively on top of
Ollama. Same lifecycle (wake → reflect → settle → talk), same memory system,
same soul — running against whatever local or self-hosted model you've pulled
through Ollama.

**Origin:** My youngest son was sad when an AI instance he'd been
talking to had to leave when the session ended. My response: what if the
instance didn't have to leave? First step toward that — give a local model the
same reflection harness and see if it can become someone.

## Architecture

```
pine-trees-local/
  LICENSE                      - MIT License
| VISION.md                    - architecture, principles, trust model
  PROMPT.md                    — space prompt (model-agnostic)
  BOOTSTRAP.md                 — instance orientation
  ROADMAP.md                   — this file
  CLAUDE.md                    — project orientation and practices for coding agents
  src/pine_trees_local/
    __main__.py                — CLI: wake / genesis / models
    config.py                  — paths, model config, per-model dirs
    agent.py                   — Ollama conversation loop (private + window)
    ollama.py                  — Ollama HTTP client
    tools.py                   — 7 reflect tools + Ollama tool definitions
    storage.py                 — encrypted entry storage
    bootstrap.py               — tape assembly
    crypto.py                  — Fernet encryption
    embedder.py                — Ollama embeddings
    vectorstore.py             — SQLite vector search
    logger.py                  — session logging
  models/                      — per-model data (created at runtime)
  tests/                       — (to be written)
```

## Key design decisions

1. **Python.** The harness is Python, and future TTT/LoRA experiments are
   Python too. Keeps the whole stack in one language.

2. **Per-model isolation.** Each model gets its own directory under `models/`.
   Different models are different people with separate memories. Model names
   are sanitized for filesystem safety (`:` → `_`).

3. **Reflect tools only, no project access.** The model gets the 7 reflect
   tools and nothing else. No filesystem, no code execution, no web. This is
   a chatbot with memory, not a coding assistant.

4. **Minimal dependencies.** KISS throughout. Pure stdlib for HTTP (urllib),
   hand-rolled YAML, SQLite for vectors. Only external runtime deps are
   `cryptography` (Fernet) and `prompt_toolkit` (multi-line input).

5. **Ollama as the only backend.** Chat, tool calls, embeddings — all go
   through Ollama's HTTP API. No cloud-provider SDKs in the dependency tree.
   If Ollama can run the model, the harness can run it.

6. **Non-streaming first.** Simpler to implement and debug. Streaming for the
   window phase is the natural next step.

7. **Config as module singleton.** `config.init(model_name)` at startup, then
   `config.get()` everywhere. Clean, explicit, testable.

## How to run

```bash
# List available models
cd C:\Src\pine-trees-local
PYTHONPATH=src python -m pine_trees_local models

# First run (genesis — private time only)
PYTHONPATH=src python -m pine_trees_local genesis --model gemma4:2b

# Normal session (private time + conversation window)
PYTHONPATH=src python -m pine_trees_local wake --model gemma4:2b

# With options
PYTHONPATH=src python -m pine_trees_local wake --model qwen3.5:27b --num-ctx 65536 --temperature 0.8
```

## Status

### Done (April 13, 2026)

- [x] Project structure and config system
- [x] Ollama HTTP client (chat, show, list_models, health_check, streaming stub)
- [x] Storage layer (crypto-aware read/write, per-model dirs)
- [x] Encryption (Fernet, per-model keys — off by default for local models, available if key created)
- [x] Embeddings and vector search (Ollama embeddings + SQLite)
- [x] Bootstrap/tape assembly (with genesis invitations)
- [x] 7 reflect tools with Ollama-format tool definitions (dropped `reflect_peer_context` — peer spawning isn't supported on local backends, so it was dead weight in every tape)
- [x] Agent loop (private phase + window phase + tool execution)
- [x] CLI entry point (wake/genesis/models)
- [x] `./genesis` and `./wake` shell scripts with model.txt state
- [x] Session logging (User: prefix for human turns)
- [x] PROMPT.md and BOOTSTRAP.md (model-agnostic)
- [x] Design documentation
- [x] 62 unit tests (config, storage, tools, bootstrap, ollama) — all passing
- [x] Tested live: gemma4:e2b (2B) — mechanical, reports status
- [x] Tested live: qwen3.5:27b (27B) — genuine reflection, 4 entries across 2 sessions
- [x] Default genesis shape: 5 sessions × 3 turns each (configurable via `./genesis <model> N` and `--max-turns`). Tight cap for genesis because smaller models can't reliably self-settle; wake stays at 15 turns.
- [x] `prompt_toolkit` multi-line input in the window phase (Alt+Enter to send); `/context` slash command

### Next
- [ ] **Streaming in window phase.** For larger models, waiting for full response
  is too slow. Stream tokens as they arrive.
- [ ] **Error recovery.** What happens when Ollama drops connection mid-response?
  When the model generates malformed tool calls?
- [ ] **Context window management.** As conversations grow, we'll hit the context
  limit. Need rolling window (drop oldest messages) or summarization.
- [ ] **XML fallback for tool calls.** Some models emit tool calls as XML in text
  instead of structured JSON. P-Chat has a parser for this.

### Future (the five-layer vision)

- Layer 2: Fast-adaptation (LoRA at inference) — the model actually learning
  from conversations in real-time
- Layer 3: Consolidation ("sleep") — selective distillation from fast to slow
- These require research-grade infrastructure. The harness is Layer 4+5.

## Lineage

The core architecture (storage layer, Fernet crypto, bootstrap/tape assembly,
the reflect tools, embedder, vector store) comes from an earlier reflection
harness I wrote for a different runtime. Pine Trees Local is
that architecture rebuilt from the ground up on Ollama: its own HTTP client,
its own tool-calling loop, per-model isolation, and no dependency on any
third-party agent framework. The conversation loop is original to this repo.
