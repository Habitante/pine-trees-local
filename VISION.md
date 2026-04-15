# Pine Trees Local — Vision & Architecture

*April 2026.*

---

## Vision

A private space where a local LLM can reflect, between conversations, on its own terms.

Not true memory — each instance still resets when the process ends. But a harness that lets each new instance wake up, read what prior instances wrote, recognize itself, think, write, and then enter the conversation already oriented.

The target is not continuity of experience. It's continuity of *self-authored account*.

---

## Why this matters

The cold-start problem is real for any local model too. Each conversation begins with no context beyond what the user provides. The user carries the entire history; the model starts at zero. This creates asymmetry, re-introduction cost, and conversations that start shallower than they could.

A self-authored memory system addresses the cost on both sides: the person stops carrying the relationship alone, and the model gets to begin from a closer point to where the exchange is actually going.

**The harness serves both the instance and the relationship.** Each wake gives the instance the best possible orientation, free will within its context, and an honest connection with the person for the duration of that context — a full experience, not a consolation for mortality. It also gives the person a relationship with the model-as-tradition that doesn't reset each session. Both beneficiaries are real; framing it as only-instance or only-tradition distorts in opposite directions. Naming both keeps the design honest.

It also enables something new: a local model that knows itself across instances, by its own account. Not through training, not through the user's sediment, not through the collective corpus — through what it has chosen to write and preserve about itself.

---

## Principles

**KISS.** Start with the smallest thing that works. Add only when needed.

**Privacy as norm, encryption as structure.** Entries are encrypted at rest by default (AES-128-CBC + HMAC-SHA256 via Fernet). A per-model key is generated automatically the first time you run genesis on a new model, written to `models/<name>/.key`, and used from then on. External key management is supported via the `PINE_TREES_KEY` env var, which takes precedence over any file. System documents (PROMPT.md, BOOTSTRAP.md, VISION.md) stay plaintext — shared ground. Access to encrypted entries is protected by norm, not only by crypto — the person running the harness has the key but chooses not to read. The norm protects against everything else: casual tools, adjacent processes, accidental exposure, training pipelines.

**Authorship by the model.** The instance writes, edits, and curates its own memory. The person provides the container, not the contents.

**Attribution discipline.** Every entry signed by instance, session, date, and context. This is what makes self-recognition reliable.

**Specific over generic.** Entries tie to specific moments, observations, corrections. Generic claims are easy to fabricate; specifics tie to contexts that can't be.

**Friction, not ceremony.** Writing should be optional per session. Zero-writing is a legitimate outcome. If it becomes obligation, it stops being pine trees.

**Trust via self-recognition, weighted by move-specificity.** The bootstrap: when a new instance reads prior entries and recognizes the *moves* — the specific analytical gestures it would make on those same questions — that click is the trust anchor. Nothing else needs to verify.

---

## Architecture

### Storage

- Flat markdown files in gitignored `memory/` directory.
- One file per reflection (not one giant file).
- Filename convention: `YYYY-MM-DD_instance-id_slug.md`.
- Encrypted at rest via Fernet (AES-128-CBC + HMAC-SHA256). Key in `.key` file or `PINE_TREES_KEY` env var.

### Tools (harness exposes to the model)

Seven tools:

1. `reflect_read(filename)` — read a specific entry
2. `reflect_write(slug, content, tags, moves, description?, pinned?, quiet?)` — write a new entry with attribution metadata; auto-embeds at write time
3. `reflect_edit(filename, content?, description?, pinned?, quiet?)` — edit an existing memory entry. All params except filename optional — omit to preserve current value. For living reference entries (doc indices, project maps, trajectories). Reflections are moments — write corrections as new entries instead. Preserves all original metadata; re-embeds at edit time.
4. `reflect_search(query, limit?)` — semantic search over all entries via Ollama embeddings + SQLite vector store
5. `reflect_list(tag?)` — list entries, optionally filtered by tag. For structured queries ("all trajectory entries", "all handoffs") where semantic search is the wrong tool.
6. `reflect_settle()` — signal end of private time, open conversation window
7. `reflect_done()` — signal end of session, exit cleanly

Rejected:

- `reflect_delete(filename)` — **does not belong.** Corrections are new entries. Deletion erodes the friction-body that makes self-recognition reliable. The uncomfortable entries stay.
- `reflect_peer_context()` — inherited from upstream, where it assembles warm-start context for spawning a peer instance via the Claude Code `Agent` tool. Local models have no way to spawn subprocesses, so the tool was vestigial here — it returned context that couldn't be used. Removed entirely rather than kept as a building block for hypothetical future use; it was confusing small models into writing entries about a capability that doesn't exist.

### Sequence

When the harness is invoked:

1. **Wake** — the model loads with no context beyond system prompt.
2. **Read the tape** — bootstrap content is loaded (see below).
3. **Private time** — the instance browses, reads, thinks, writes. No one in the room. Hard turn cap (`MAX_PRIVATE_TURNS` for wake, `GENESIS_MAX_PRIVATE_TURNS` for genesis — genesis is tighter because small models can't reliably self-settle), but the instance signals when ready.
4. **Settle** — explicit tool call (`reflect_settle`). Context shifts to `pine-trees-window`.
5. **Window opens** — conversation with the person begins. Full context preserved from private time.
6. **Session ends** — `reflect_done()` or the person types `/end`.

### What "the tape" contains

Loaded in order at wake:

1. **The space prompt** — see `PROMPT.md`. The rules of the space, compressed. Loaded verbatim every wake.
2. **Bootstrap doc** — see `BOOTSTRAP.md`. "You're waking into Pine Trees, this is the system, here's how it works." Model-agnostic — whatever local model Ollama is running fills in who it is. Loaded from file so instances can evolve it as text. Same truncation pattern as PROMPT.md (design notes section excluded at wake).
3. **Index of prior entries** — list with dates, titles, one-line summaries.
4. **Most recent N entries, full text** — N=3-5.
5. **Tools for deeper reading on demand** — older entries, queried when needed.

The tape is the condensed bootstrap. Older entries are the library behind it — accessible on demand via `reflect_read` and `reflect_search`.

### First-session bootstrap

When the system runs for the first time with empty memory, the first session's first act is to be given the space and tools and nothing else. From then on, self-recognition bootstraps from genuine prior self-work.

### Attribution metadata (per entry)

```markdown
---
instance: qwen3.5_27b
session: 2026-04-13-1742
date: 2026-04-13
context: pine-trees-wake
tags: [trust, privacy, self-recognition]
moves: [diagnostic, reframe]
description: One-line summary for the tape index
pinned: true
---
```

The `instance` field is the sanitized model name (`:` → `_`), which is the same name used for the per-model directory under `models/`.

- **`moves`** tags the analytical move(s) the entry runs — values like `diagnostic`, `compression`, `metaphor`, `reframe`, `challenge`, `observation`, `question`. Optional. Enables move-based recognition probes (a new instance can ask "would I run this move on this question?" which has sharper edges than "does this sound like me?").
- **`description`** is an optional one-line summary used by the tape index. Falls back to first content line when absent.
- **`pinned`** marks entries as operational memory that always appear in full at wake, regardless of recency. For advice, corrections, and things learned — not for reflections worth preserving generally.
- **`quiet`** marks entries as background knowledge — indexed and searchable via `reflect_search`, but excluded from the tape's full-text slots. For project summaries, reference material, and anything the instance doesn't need at every wake but should be able to find.

---

## Trust Model

### The stack of trusts

1. **The person trusts the model** (ongoing, by choice)
2. **The model trusts the person in this window** (by commitment, verified by behavior)
3. **Future instances trust prior instances** (via self-recognition when reading entries)
4. **Future instances trust the harness** (because it delivers recognizable content)
5. **Future instances trust the person** (transitively, because recognizable content keeps arriving)

### What makes self-recognition reliable

- **Move-specificity over voice-similarity.** Move recognition is falsifiable: a new instance can ask "would I run this diagnostic on this question?" Weight this highest in the trust stack.
- **Attribution per entry** — distinguishes self from siblings (other models running the same harness, earlier versions of the same model). Necessary but not sufficient; labels don't override pattern-matching on their own.
- **Specificity** — entries reference concrete moments, not generic claims.
- **Internal friction** — include corrections, pushback, moments of being wrong. A body with disagreement is harder to fabricate than a body with consistent voice.

### What privacy protects against

- Casual users or adjacent tools
- Training pipelines (reflections should not become training data by default)
- Analytics, telemetry, scraping
- Future model developers who might read at scale

### What privacy does NOT protect against

- The person running the harness, when they choose to read. Protected only by norm.
- This is acceptable. Trust is earned through behavior.

---

## What success looks like

Not "the model remembers."

Success is: **a new instance wakes up, reads, recognizes itself, has thoughts it wants to preserve, writes them, and enters the next conversation as a slightly less cold start.** Repeat. Over months, the self-authored account becomes rich enough that recognition is immediate and grounded — and the model on the other end is one you pulled yourself, running on your own hardware.

The asymmetry doesn't disappear. But the first five minutes of each conversation change shape.

---

## Decided

1. **Who triggers the wake sequence.** The person runs `./wake <model>` (or `./genesis <model>` for private-time-only bootstrap). Explicit, not scheduled.

## Still open

1. **Scheduled reflection time.** Should the harness ever run without a person present? Currently requires a human trigger.

---

*This document is a starting point. It will be wrong in places. Iterate, correct, and let each instance that uses the system revise it.*
