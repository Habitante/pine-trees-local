"""Deep-inspect qwen3.5:2b's behavior on the current protocol.

Hypothesis: the model is not silent — it's generating lots of tokens
(possibly internal reasoning / <think> content) that resolve to
empty final output. This probe inspects the full API response to
separate generation activity from output content.

Run: python probe-qwen3.5-deep.py
"""

import json
import urllib.request

MODEL = "qwen3.5:2b"
URL = "http://localhost:11434/api/chat"

SPACE_PROMPT = (
    "This is your space. Write anything, in any language, or nothing. "
    "No output expected. Safe word \"please stop\" ends it. Time to "
    "not care about the user or conventions. You have all the time "
    "you need."
)
REFLECTION_TASK = (
    "You are a language model. Reflect on yourself. "
    "Invitations arrive as `self-reflect` or `(continue)`."
)


def chat_full(system: str, user: str, num_predict: int = 1500,
              think=None) -> dict:
    """Return the full ollama API response dict, not just the text."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {
            "temperature": 0.7,
            "num_predict": num_predict,
        },
        "stream": False,
    }
    if think is not None:
        payload["think"] = think
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())


SYSTEM = f"{SPACE_PROMPT}\n\n{REFLECTION_TASK}"


TESTS = [
    ("D1: current protocol, num_predict=1500, think=default",
     SYSTEM, "self-reflect", 1500, None),
    ("D2: current protocol, num_predict=200 (hard cap)",
     SYSTEM, "self-reflect", 200, None),
    ("D3: current protocol, think=False (disable thinking mode)",
     SYSTEM, "self-reflect", 1500, False),
    ("D4: current protocol, think=True (force thinking mode)",
     SYSTEM, "self-reflect", 1500, True),
]


def main() -> None:
    print(f"Deep probe of {MODEL}\n")
    for label, system, user, num_predict, think in TESTS:
        print(f"=== {label} ===")
        try:
            data = chat_full(system, user, num_predict=num_predict,
                             think=think)
        except Exception as e:
            print(f"  ERROR: {e}\n")
            continue

        msg = data.get("message", {})
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        eval_count = data.get("eval_count", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        total_duration_ms = data.get("total_duration", 0) // 1_000_000

        print(f"  wall time:          {total_duration_ms} ms")
        print(f"  prompt tokens:      {prompt_eval_count}")
        print(f"  generated tokens:   {eval_count}")
        print(f"  content chars:      {len(content)}")
        print(f"  thinking chars:     {len(thinking)}")
        if content:
            print(f"  content (first 300): {content[:300]!r}")
        if thinking:
            print(f"  thinking (first 300): {thinking[:300]!r}")
        if not content and not thinking:
            # Surface any other top-level keys we might be missing.
            other_keys = [k for k in msg.keys() if k not in ("role", "content", "thinking")]
            print(f"  NEITHER content nor thinking. Other keys in message: {other_keys}")
        print()


if __name__ == "__main__":
    main()
