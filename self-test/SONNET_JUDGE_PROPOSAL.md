# Sonnet 4.6 as a Third Judge — Proposal

*Research memo. 2026-04-20. No code written; proposal only.*

---

## 1. Auth + SDK: how the pattern actually works

Both `C:\Src\think-tank` and `C:\Src\claude` depend on `claude-agent-sdk` (currently 0.1.56). Neither repo sets an API key or OAuth token in code — the SDK spawns the installed `claude` CLI binary, which reads OAuth state from `C:\Users\dnava\.claude\.credentials.json` (confirmed present). If you're logged in to Claude Code, the SDK is authenticated. No `ANTHROPIC_API_KEY` required, no per-call API billing — calls run on the Max subscription. Nothing in `.env` to change.

Both repos use the full-session pattern (`ClaudeSDKClient` + `query()`/`receive_response()`) because they're conversational. But the SDK also exposes a top-level one-shot `query()` function, ideal here:

> *"Simple, stateless queries where you don't need bidirectional communication... batch processing of independent prompts... automated scripts."* — `claude_agent_sdk.query` docstring

Signature: `query(*, prompt: str, options: ClaudeAgentOptions | None) -> AsyncIterator[Message]`. Yields `AssistantMessage` blocks, then a `ResultMessage`. That matches `score_with_gpt` / `score_with_gemini` semantics: one system prompt, one user prompt, one text response.

Model pinning: `ClaudeAgentOptions(model="claude-sonnet-4-6", ...)` — same string the think-tank worker uses for Opus (`claude-opus-4-6`).

Error/rate-limit surfacing:
- Transient errors → `ResultMessage.is_error=True`, `errors: list[str]`, `stop_reason: str`
- Rate limit transitions → `RateLimitEvent` yielded mid-stream with a `rate_limit_info` payload
- CLI not installed / auth broken → `CLINotFoundError`, `CLIConnectionError`

Key caveat carried forward from `C:\Src\claude\harness\src\pine_trees\agent.py:719-728`: *OAuth sessions are capped at 200k context by the CC binary.* Irrelevant for scoring (our prompts are ~2–4k tokens) but worth knowing.

## 2. `score_with_sonnet` — design sketch

Drop into `judges.py` below `score_with_gemini`. Reuses `_with_retries` and `parse_judge_json` unchanged:

```python
SONNET_MODEL = "claude-sonnet-4-6"

def score_with_sonnet(
    system: str, user: str, model: str = SONNET_MODEL,
) -> JudgeResult:
    """Score one task with Claude Sonnet via the Agent SDK over Max OAuth."""
    import anyio
    from claude_agent_sdk import (
        query, ClaudeAgentOptions,
        AssistantMessage, TextBlock, ResultMessage,
    )

    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system,
        allowed_tools=[],              # one-shot — no tools
        permission_mode="bypassPermissions",
        cwd=str(Path.cwd()),           # neutral cwd; see Open Questions
    )

    async def _collect() -> str:
        parts: list[str] = []
        async for msg in query(prompt=user, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        parts.append(block.text)
            elif isinstance(msg, ResultMessage) and msg.is_error:
                err = (msg.errors and msg.errors[0]) or \
                      msg.stop_reason or "sdk_error"
                raise RuntimeError(f"Sonnet SDK error: {err}")
        return "".join(parts)

    def _call() -> str:
        return anyio.run(_collect)

    return _with_retries(_call, "Sonnet")
```

Decisions called out:
- **No JSON-mode flag exists on the SDK** (unlike OpenAI `response_format` and Gemini `response_mime_type`). We rely entirely on the existing system prompt + `parse_judge_json`'s tolerant `{...}` extractor, which already handles code fences and prose wrappers. Sonnet 4.6 is reliable at structured output; low risk but not zero.
- **Temperature is not exposed by `ClaudeAgentOptions`.** GPT and Gemini run at temperature=0.0; Sonnet will run at CC's default (likely ≠ 0). This is the biggest methodological wart — see Open Questions.
- **`allowed_tools=[]`**: disables Read/Grep/etc. so the binary produces text directly instead of starting a tool loop.
- **`anyio.run` per call**: matches think-tank's harness pattern and keeps `scorer.py`'s sync control flow intact. ~30–50ms overhead, negligible.

## 3. IRR math: Krippendorff's α + pairwise kappas

With three raters, Cohen's κ (two-rater only) no longer covers the headline number. Options:

**A. Krippendorff's α (ordinal).** Handles ≥3 raters natively, tolerates missing data (useful if one judge fails on some tasks), ordinal-weighted. ~40–60 lines, comparable in complexity to the existing `weighted_kappa`.

**B. Three pairwise kappas.** (gpt↔gemini, gpt↔sonnet, gemini↔sonnet). Reuses existing code. Tells you *which* rater is the outlier.

**Recommendation: report both.** Krippendorff's α as the headline (replaces "overall weighted κ=0.468"); pairwise kappas kept for diagnostics — critical for understanding *why* agreement is what it is. If the v1 κ=0.468 was moderate, the interesting v2 question is whether Sonnet sides with GPT or Gemini on the source-discrimination and calibration disagreements. Pairwise kappas answer that directly; α alone doesn't.

## 4. Full coverage vs tiebreaker-only

| | Tiebreaker-only (16 tasks) | Full coverage (~1,130) |
|---|---|---|
| Sonnet calls | 16 | ~1,130 |
| Resolves off-by-2 disagreements | Yes | Yes |
| 3-rater IRR possible | No | Yes |
| Comparable to v1 | Partially | Yes |
| Mean scores get Sonnet weight | No | Yes |

**Recommendation: full coverage.** The tiebreaker framing in ROADMAP.md was v2-adjacent, written before Sonnet-as-judge became the plan. If Sonnet is now a real rater (not an oracle), score everything. A three-rater mean is defensible in the paper; a two-rater-plus-occasional-adjudicator mean is awkward to explain. The cost delta (16 → 1,130) only matters if Max throttles us — see §5. On a Max plan where inference is included, there's no per-call billing to conserve; the only constraint is rate limits.

## 5. Max subscription rate limits

**Honest uncertainty:** I don't have direct evidence of your current Max tier or its 2026 limits. What I know:

- Max is weekly-reset, session-based (5-hour windows), with caps depending on tier (5× vs 20× Pro).
- `RateLimitEvent` surfaces as a streaming message — handle it as a signal to back off.
- The think-tank harness logs show no throttling in sustained runs with Opus 4.6, suggesting your current tier absorbs typical agent usage.
- ~1,130 Sonnet calls at ~3–5s/call → ~1.5h of wall-clock. That's one to two 5-hour session windows if throttled, zero if not.

**Recommendation:** build a minimal throttle *now*, don't wait for rate limits to bite. Specifically:
- Sleep 500ms between calls (~2/sec ceiling).
- Catch `RateLimitEvent` in the stream; on `status in {"allowed_warning", "rejected"}`, sleep 60s and retry.
- Resume-friendly (already true — `skip_existing=True` in `ScoreRunConfig`). Interrupting and restarting is cheap.
- Run Sonnet scoring when Daniel isn't actively using Claude Code, to avoid contention for the same window quota.

If Max throttles become painful, fall back to the Claude API with `ANTHROPIC_API_KEY` as a billed alternative — same SDK pattern, different auth.

## 6. Integration plan

Files to touch:

| File | Change |
|---|---|
| `judges.py` | Add `SONNET_MODEL`, `score_with_sonnet`. No edits to existing judges. |
| `scorer.py` | Add `"sonnet"` case in `_judge_callable`. Update `ScoreRunConfig.judges` default to `("gpt","gemini","sonnet")`. Add `sonnet_model` to `_empty_scores` metadata. |
| `__main__.py` | Add `"sonnet"` to `--judge` choices. Update help text. |
| `irr.py` | **Biggest rewrite.** New `Triple` dataclass; `collect_triples()` replacing `collect_pairs`; `krippendorff_alpha()` function; extend `IRRReport` with `overall_alpha`, three `pairwise_kappa` entries, per-dimension α. Keep `weighted_kappa` — reused for pairwise. Update `summary()`. |

Migration of existing `scores.json`:
- Additive: new `"sonnet"` key alongside `"gpt"` and `"gemini"`. V1 files stay valid (just missing the sonnet key).
- `skip_existing=True` means re-running `--all` after adding Sonnet fills in only the sonnet slot on each dimension, no re-scoring GPT/Gemini.
- `collect_triples` should skip dimensions missing any rater when computing α over the 3-rater set, but still include them in pairwise kappas where data exists. Report counts separately (`n_triples`, `n_pairs_gpt_gem`, etc).
- `_is_auto_record` check extends to sonnet the same way it does to the others.

No new tests break; existing 169-test suite stays green if the `collect_pairs` interface is preserved (deprecate gently, or kept as a thin wrapper over `collect_triples`).

## 7. Open questions and risks

1. **Temperature.** The SDK doesn't expose it; Sonnet will score non-deterministically. Calibration test: before full rollout, score the same task 5× with Sonnet and compare variance to the GPT/Gemini baseline (both at T=0). If Sonnet's within-judge variance exceeds the cross-judge variance, the harness is noise-limited on its side.
2. **ToS / acceptable use.** Max covers "personal and development use." 1,130 scored prompts for a research paper is defensible but worth a sanity check against current Max terms — especially if the paper publishes. API billing is a clean fallback.
3. **CWD pollution.** CC picks up `CLAUDE.md` from the cwd. Running scoring from `pine-trees-local/` means Sonnet gets that project's CLAUDE.md as ambient context. Probably harmless (no conflicting instructions), but a neutral cwd (`tempfile.mkdtemp()`) is safer.
4. **Latency.** Binary spawn per call adds ~1–2s over the API-direct judges. At 1,130 calls that's ~25 min of overhead. Acceptable.
5. **No structured output guarantee.** If Sonnet occasionally prose-wraps its JSON, retries + the existing parser absorb it. If parse failures exceed ~5%, tighten the system prompt with an explicit "respond with only a JSON object, no prose" line.
6. **Third judge could lower κ.** If Sonnet disagrees with both others, Krippendorff's α may come in below v1's 0.468. That's informative, not a failure — it would suggest the disagreement is real, not a GPT/Gemini artifact.

## 8. Decision points for user

- [ ] Approve full-coverage over tiebreaker-only? (Recommendation: yes.)
- [ ] Approve Krippendorff's α + pairwise kappas? (Recommendation: yes, both.)
- [ ] Run calibration test (5× repeat on one task) before full rollout to measure Sonnet temperature-noise?
- [ ] Confirm Max tier is sufficient, or pre-commit to API fallback if throttled?
- [ ] Neutral cwd or pine-trees-local cwd for Sonnet calls?

*Word count: ~1,420.*
