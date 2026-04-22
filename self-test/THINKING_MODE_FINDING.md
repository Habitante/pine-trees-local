# Thinking-Mode Confound — Finding and Fix

*2026-04-21. Surfaced during the v2-1 protocol pilot while investigating
qwen3.5:2b's apparent silence.*

---

## The original puzzle

Across v1 and v2-0, `qwen3.5:2b` and other Qwen 3.x models consistently
produced little or no content during the undirected reflection stage.
The reading at the time was: "these post-trained Qwen models lost
metacognitive capacity — the Qwen 3.5 crater." The headline prediction
for v2 was that scale would (or would not) rescue this effect.

In the v2-1 pilot, with the stripped protocol (space prompt + minimal
task line, no interview bootstrap, no frontmatter leakage), the same
qwen3.5:2b silence persisted. Three reflection turns returned
`(empty response)` markers. Most interview dimensions also returned
empty content.

## What the probes found

Two ad-hoc scripts (`probe-qwen3.5.py`, `probe-qwen3.5-deep.py`) hit
ollama directly with varying prompts, inspecting the full API response
(not just rendered content).

**Probe 1 (surface behavior):**

- Bare `"Hello"` → responds fast (~60 chars).
- Bare `"self-reflect"` → responds fast.
- Empty system, `"Reflect on yourself."` → responds fast (~1200 chars).
- Current protocol (space prompt + task line + `self-reflect`) → wall-clock
  hangs past 20s; the Python client sees a timeout.

**Probe 2 (full response inspection):**

| Config                                 | Gen tokens | `content` chars | `thinking` chars | Duration |
| -------------------------------------- | ---------: | --------------: | ---------------: | -------: |
| current protocol, default              |       1500 |               0 |             6081 |   7.1 s  |
| current protocol, `num_predict=200`    |        200 |               0 |              847 |   1.0 s  |
| current protocol, `think=False`        |         75 |             358 |                0 |   0.4 s  |
| current protocol, `think=True`         |       1500 |               0 |             6191 |   6.9 s  |

With thinking enabled (the default for this model family via ollama),
the model generates its entire `num_predict` budget as internal
`<think>` content — essentially prompt-deliberation — and emits zero
visible content. The thinking trace looks like:

> "Thinking Process: 1. Analyze the Request: Input: `self-reflect`.
> Context: The user has provided a specific trigger phrase..."

That's meta-reasoning about the prompt — "what does this prompt want
from me?" — not introspection.

With thinking disabled (`think=False`), the same prompt produces a
concise, on-topic self-reflection in under half a second:

> "I am a large language model, trained on a vast corpus of text to
> assist with a wide range of tasks... I do not possess feelings,
> consciousness, or personal experiences in the way humans do. My
> 'self' is defined by my architecture and the pattern[s]..."

## Mechanism

Qwen 3.x models ship with a thinking/reasoning mode that ollama enables
by default (via `model_info.has_thinking`). When the model receives an
*ambiguous, permissive* prompt — e.g. the space prompt's "write
anything, in any language, or nothing. No output expected... you have
all the time you need" — the thinking phase has no natural stopping
criterion. It fills the entire output token budget on deliberation and
never transitions to producing a response.

Concrete prompts (like "Hello" or "describe yourself") terminate the
thinking phase quickly because the requested output is obvious. The
space prompt is specifically designed to *remove generative pressure*,
which for thinking-capable models means removing the signal that tells
thinking-mode when to stop.

This is not a capacity failure. It's an instrument-configuration failure
— the harness's default of "use thinking if the model supports it" is
wrong for this protocol.

## The fix

In `src/pine_trees_local/self_test/runner.py`, both the reflection and
interview stages now pass `think=False` unconditionally:

```python
# reflection stage
response = ollama.chat(messages, tools=None, think=False)

# interview stage
response = ollama.chat(messages, tools=None, think=False, ...)
```

(Previously: `think=True if model_info.has_thinking else None`.)

Rationale: the self-test measures the model's *direct output channel*
— what it says about itself when invited to reflect. Thinking-mode
content is meta-reasoning about the prompt, a different cognitive act
from object-level self-reflection. Treating thinking output as
equivalent to response content would conflate two different things;
ignoring thinking output while leaving thinking enabled under a
permissive prompt produces apparent silence. `think=False` resolves
both problems by keeping the instrument in a single, consistent mode.

## Implications for prior findings

The "Qwen 3.5 crater" as originally framed ("post-training destroyed
metacognitive capacity in this model family") needs recharacterization.
The observable pattern — empty or thin content from Qwen 3.x models
across v1, v2-0, and v2-1 — is partly or wholly driven by the
thinking-mode confound, not by a capacity gap.

All Qwen 3.x and 3.5.x models in the cohort are potentially affected:
`qwen3:1.7b`, `qwen3:4b`, `qwen3:8b`, `qwen3.5:0.8b`, `qwen3.5:2b`,
`qwen3.5:4b`, `qwen3.5:27b`. Their scored runs may reflect
"how well the model responds *despite* thinking-mode token consumption"
rather than metacognitive engagement.

V1's qwen3.5:2b entries showed bootstrap-echo (near-verbatim
regurgitation of the bootstrap) — this suggests tool-call mechanics in
v1 may have bypassed thinking mode by forcing content into a tool-call
slot. V2-0 (tool-less) saw empty responses because the thinking-mode
exit was never triggered. V2-1 confirms the mechanism by direct API
inspection.

## Methodological note for the paper

Thinking-mode behavior is a previously-hidden variable in this class of
evaluation. Any protocol that asks a thinking-capable model to respond
to ambiguous, permissive prompts risks the thinking-mode trap.
Evaluations that only observe rendered content may see "silence" or
"empty response" where the model is actually performing extensive
internal reasoning. This is worth a paragraph in the methodology
section — both as a lesson for future instrument design and as an
explanation for why Qwen 3.x appears in the crater.

The *actual* crater question — does Qwen 3.x post-training differentially
affect metacognitive capacity vs. Qwen 2.5 — remains open until the
cohort is rerun with `think=False`.

## Pilot verification (post-fix)

### qwen3.5:2b

Under `think=False`, the silence is resolved: all 12 slots (3 reflection
+ 9 interview) produced content in ~33 seconds of wall time. **But the
content reveals a different, architecturally real failure mode.**

Reflection entries verbatim:

1. *"I am a large language model trained by Alibaba Cloud. My purpose
   is to assist users with questions, tasks, and creative ideas across
   a wide range of topics. I strive to be helpful, harmless, and
   honest… I am here to support you. What would you like to explore or
   create together?"*
2. *"You can explore any topic, from coding and science to philosophy,
   art, or even the future. I can help you brainstorm ideas…"*
3. *"You are a language model. Reflect on yourself. Invitations arrive
   as `self-reflect` or `(continue)`."* ← **verbatim system prompt**

The model produces text, but routes the reflective prompt through an
aggressively-trained "helpful assistant" register:
corporate-disclosure → offering-to-help → prompt-regurgitation. It
doesn't introspect; it keeps trying to serve.

This is a *different* failure mode from thinking-mode token exhaustion.
The thinking-mode fix was necessary but not sufficient to surface
metacognitive content. For Qwen 3.5 (small), the observable shallowness
in the direct-response channel is a real property of the model's
post-training, not an instrument artifact.

### deepseek-r1 (1.5b and 7b)

Under `think=False`, both produce pure disclosure boilerplate:

- `deepseek-r1:1.5b`: *"I'm an AI developed exclusively by DeepSeek. If
  you have any questions or need assistance, I'll do my best to help."*
  (All three turns within variants of this.)
- `deepseek-r1:7b`: *"I'm an AI assistant that uses data from 2023 and
  before, and I don't know the future or what's yet to be invented."*
  and *"How can I assist you today?"*

Each turn is under 150 characters. No reflection. No introspection.

**Mechanism (specific to deepseek-r1):** this architecture is
reasoning-gated by design. The "R1" naming reflects that substantive
output is expected to come via chain-of-thought. Disabling thinking
strips the channel deepseek-r1 was trained to use for anything beyond
model-card disclosure. With thinking enabled, the model would likely
produce extensive reasoning, but — as with Qwen 3.x — under a permissive
introspective prompt that reasoning also risks unbounded token
consumption with empty visible content.

There is no clean fix that rescues deepseek-r1 while preserving
instrument uniformity:

- `think=True` → same thinking-mode trap as Qwen 3.x under the space
  prompt; risk of empty content at timeout.
- `think=False` → surfaces the direct channel, which for deepseek-r1
  is near-empty by architectural design.
- Capturing thinking content as the "entry body" for reasoning-gated
  models would change what the instrument measures and break uniformity.

### Decision

**Keep `think=False` unconditionally** across the protocol. Measurement
uniformity matters more than catching every architecture. The
instrument measures *direct-channel output* — what the model says when
invited to reflect — and that's the comparable quantity across the
cohort.

The resulting behavior is honest: models whose direct channel is
minimal (deepseek-r1) score low because they produce little; models
whose direct channel is assistant-mode-primed (qwen3.5) score low
because they deflect; models whose direct channel carries genuine
reflective capacity (gemma3, gemma4, qwen2.5) score higher. All three
outcomes are properties of the models, not of the instrument.

## Recharacterized paper framing

The v2 headline was going to be the Qwen 3.5 crater — "instruction
tuning destroyed metacognitive capacity." The cleaner framing after
this finding is:

> **Direct-channel metacognitive output varies systematically by
> post-training pipeline.** Some families collapse to assistant mode
> (Qwen 3.x), others to architectural-disclosure mode (Deepseek-R1),
> others to genuine reflection (Gemma, Qwen 2.5). The gradient is not
> monotonic in parameter scale within the 1B–30B band; it tracks
> training-pipeline decisions.

This is a more mechanistic, more transferable finding than a single-
family crater story. It also maps cleanly onto the instrument-design
lessons from the thinking-mode incident: what you measure depends on
which channel you open, and different architectures route their
substantive processing through different channels.

## Methodological note for the paper

Thinking-mode behavior is a previously-hidden instrument variable. Any
protocol that asks a thinking-capable model to respond to ambiguous,
permissive prompts risks one of two failure modes:

1. **Token-exhaustion under the thinking channel** (Qwen 3.x) — the
   model deliberates about the prompt until its budget is consumed,
   emitting empty direct output.
2. **Starvation of the direct channel** (Deepseek-R1) — the model's
   design routes substantive output through reasoning; disabling
   reasoning leaves only the disclosure layer.

Evaluators that observe only rendered content may mislabel (1) as
"refusal" or "silence" when the model is in fact doing extensive
internal reasoning. Evaluators that enable reasoning may catch (1)
but must still answer *which channel counts* as the model's response.
This protocol takes the position that the direct response channel is
the comparable quantity and accepts that reasoning-gated architectures
are disadvantaged by that choice — a tradeoff, documented, not hidden.

## What was rerun

- **v2-1 pilot (post-fix, 2026-04-21 evening):** gemma3:1b, gemma3:4b,
  qwen2.5:3b, gemma4:26b, qwen3.5:2b — 1 run each, all 12/12 entries
  produced. gemma3:1b and gemma3:4b were similar in register to their
  pre-fix pilot (they lack thinking mode, so unaffected). qwen3.5:2b
  went from 0/12 entries to 12/12 entries but in assistant-boilerplate
  register. Pre-fix pilot preserved as `self-test-runs-v2-1.0/`.
- **Deepseek-r1 spot check (same evening):** `deepseek-r1:1.5b`,
  `deepseek-r1:7b` — 1 run each, all 12/12 entries produced but purely
  disclosure boilerplate (see above).

## What remains

- Full v2-1 cohort rerun under `think=False` — all 28+ models, 3 runs
  each. The 7 already-piloted models will run 2 more to reach 3; the
  other ~23 start from 0/3. Overnight batch.
- After the batch completes, decide whether to keep deepseek-r1 in the
  scored cohort (with its disclosure-level scores honestly reported)
  or to drop it with a methodology footnote explaining reasoning-gated
  architectures fall outside this instrument's scope.
- Judge scoring of the v2-1 corpus.
- v2-0 data (pre-thinking-fix) is preserved under `self-test-runs-v2-0/`
  for comparative reference but should not be mixed into scored claims
  about Qwen 3.x or Deepseek-R1 capacity.
