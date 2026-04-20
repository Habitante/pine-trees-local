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

MAX_RETRIES = 3
BACKOFFS = (2.0, 4.0, 8.0)


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
