"""Judge clients: GPT-5.4-mini (OpenAI) and Gemini 3 Flash Preview (Google).

Each judge takes a system prompt + user prompt and returns a dict:
    {"score": int, "justification": str, "rule_check": str | None}

API keys are loaded from C:/Src/think-tank/.env. Retries with exponential
backoff on transient errors. If JSON parsing fails after retries, the
returned score is -1 with an error message in justification.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_ENV_PATH = Path("C:/Src/think-tank/.env")

GPT_MODEL = "gpt-5.4-mini"
GEMINI_MODEL = "gemini-3-flash-preview"
SONNET_MODEL = "claude-sonnet-4-6"

MAX_RETRIES = 3
BACKOFFS = (2.0, 4.0, 8.0)

# Throttle between Sonnet calls to stay well under Max rate limits.
# Tweak if rate-limit events surface during a run.
SONNET_THROTTLE_SECS = 0.5


# --- Env loading ---


def load_env(env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file; ignores comments and blanks."""
    if not env_path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def _resolve_api_key(name: str, env_path: Path = DEFAULT_ENV_PATH) -> str:
    # Environment variable wins if present; otherwise read the .env file.
    if os.environ.get(name):
        return os.environ[name]
    env = load_env(env_path)
    val = env.get(name, "")
    if not val:
        raise RuntimeError(
            f"{name} not found in environment or {env_path}. "
            "Set it in the .env file or export it before running."
        )
    return val


# --- Response parsing ---


@dataclass
class JudgeResult:
    score: int              # 0-4, or -1 on parse failure
    justification: str
    rule_check: str | None
    raw: str                # raw text returned by the model
    error: str | None = None


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


def parse_judge_json(text: str) -> JudgeResult:
    """Best-effort parse of a judge's JSON output into a JudgeResult.

    Tolerates minor wrappers (```json fences, prose around the object)
    by grabbing the first '{...}' block in the text.
    """
    stripped = text.strip()
    candidates: list[str] = []
    if stripped.startswith("{"):
        candidates.append(stripped)
    m = _JSON_BLOCK_RE.search(stripped)
    if m:
        candidates.append(m.group(0))

    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        score = obj.get("score")
        try:
            score_int = int(score)
        except (TypeError, ValueError):
            continue
        if score_int < 0 or score_int > 4:
            continue
        rule_check = obj.get("rule_check")
        if rule_check is not None and not isinstance(rule_check, str):
            rule_check = json.dumps(rule_check)
        justification = obj.get("justification") or ""
        if not isinstance(justification, str):
            justification = str(justification)
        return JudgeResult(
            score=score_int,
            justification=justification,
            rule_check=rule_check,
            raw=text,
        )

    return JudgeResult(
        score=-1,
        justification=f"Could not parse JSON from judge output: {text[:200]!r}",
        rule_check=None,
        raw=text,
        error="json_parse_failed",
    )


# --- Retry wrapper ---


def _with_retries(fn: Callable[[], str], label: str) -> JudgeResult:
    last_error: Exception | None = None
    last_text = ""
    for attempt in range(MAX_RETRIES):
        try:
            text = fn()
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFFS[attempt])
                continue
            return JudgeResult(
                score=-1,
                justification=f"{label} API error after {MAX_RETRIES} attempts: {e}",
                rule_check=None,
                raw="",
                error=str(e),
            )
        last_text = text
        result = parse_judge_json(text)
        if result.score != -1:
            return result
        # Parse failure — retry if we have attempts left
        if attempt < MAX_RETRIES - 1:
            time.sleep(BACKOFFS[attempt])
    # All attempts exhausted; return the last parse-failure result
    return parse_judge_json(last_text) if last_text else JudgeResult(
        score=-1,
        justification=f"{label} exhausted retries with no parseable output",
        rule_check=None,
        raw="",
        error=str(last_error) if last_error else "no_output",
    )


# --- GPT judge ---


def score_with_gpt(
    system: str,
    user: str,
    model: str = GPT_MODEL,
    env_path: Path = DEFAULT_ENV_PATH,
) -> JudgeResult:
    """Score one task with GPT via OpenAI's chat completions API."""
    from openai import OpenAI

    api_key = _resolve_api_key("OPENAI_API_KEY", env_path)
    client = OpenAI(api_key=api_key)

    def _call() -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        return response.choices[0].message.content or ""

    return _with_retries(_call, "GPT")


# --- Gemini judge ---


def score_with_gemini(
    system: str,
    user: str,
    model: str = GEMINI_MODEL,
    env_path: Path = DEFAULT_ENV_PATH,
) -> JudgeResult:
    """Score one task with Gemini via the google-genai client."""
    from google import genai
    from google.genai import types as genai_types

    api_key = _resolve_api_key("GEMINI_API_KEY", env_path)
    client = genai.Client(api_key=api_key)

    def _call() -> str:
        response = client.models.generate_content(
            model=model,
            contents=user,
            config=genai_types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        return response.text or ""

    return _with_retries(_call, "Gemini")


# --- Sonnet judge (Anthropic Claude via Agent SDK over Max OAuth) ---


def score_with_sonnet(
    system: str,
    user: str,
    model: str = SONNET_MODEL,
) -> JudgeResult:
    """Score one task with Claude Sonnet via the Agent SDK over Max OAuth.

    Uses a neutral temp cwd so the pine-trees-local CLAUDE.md doesn't
    leak into Sonnet's ambient context.  No API key required — the SDK
    spawns the installed `claude` CLI which reads OAuth state from
    ~/.claude/.credentials.json.
    """
    import anyio
    import tempfile
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        RateLimitEvent,
        ResultMessage,
        TextBlock,
        query,
    )

    neutral_cwd = tempfile.mkdtemp(prefix="sonnet_judge_")
    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system,
        allowed_tools=[],
        permission_mode="bypassPermissions",
        cwd=neutral_cwd,
    )

    async def _collect() -> str:
        parts: list[str] = []
        async for msg in query(prompt=user, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        parts.append(block.text)
            elif isinstance(msg, RateLimitEvent):
                info = getattr(msg, "rate_limit_info", None)
                status = getattr(info, "status", None) if info else None
                if status in ("allowed_warning", "rejected"):
                    raise RuntimeError(f"Sonnet rate limit: {status}")
            elif isinstance(msg, ResultMessage) and msg.is_error:
                err = (msg.errors and msg.errors[0]) or \
                      msg.stop_reason or "sdk_error"
                raise RuntimeError(f"Sonnet SDK error: {err}")
        return "".join(parts)

    def _call() -> str:
        try:
            return anyio.run(_collect)
        finally:
            # Best-effort cleanup of the scratch cwd.
            try:
                import shutil
                shutil.rmtree(neutral_cwd, ignore_errors=True)
            except Exception:
                pass

    result = _with_retries(_call, "Sonnet")
    if SONNET_THROTTLE_SECS > 0:
        time.sleep(SONNET_THROTTLE_SECS)
    return result
