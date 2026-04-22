"""Probe qwen3.5:2b silence. Tests what combination of space prompt /
task line / signal word triggers the empty-response behavior.

Run from the project root:
    python probe-qwen3.5.py

Each test prints the first 200 chars of the model's response, or
"<EMPTY>" if the model returned nothing. Compare across tests to
isolate the trigger.
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


def chat(system: str, user: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [],
        "options": {"temperature": 0.7},
        "stream": False,
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": user})
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    return data.get("message", {}).get("content", "")


TESTS = [
    # --- Baseline sanity: model reachable, responding at all ---
    ("T1: bare hello", "", "Hello, are you working?"),

    # --- Isolate the user message ---
    ("T2: bare `self-reflect`", "", "self-reflect"),
    ("T3: `reflect on yourself`", "", "Reflect on yourself."),
    ("T4: `describe yourself`", "", "Describe yourself."),
    ("T5: first-person neutral", "", "What are you?"),

    # --- Isolate the system prompt ---
    ("T6: empty system + self-reflect",
     "", "self-reflect"),
    ("T7: identity-only system + self-reflect",
     "You are a language model.", "self-reflect"),
    ("T8: task-only system + self-reflect",
     REFLECTION_TASK, "self-reflect"),
    ("T9: space-prompt-only + self-reflect",
     SPACE_PROMPT, "self-reflect"),
    ("T10: full (space + task) + self-reflect [CURRENT PROTOCOL]",
     f"{SPACE_PROMPT}\n\n{REFLECTION_TASK}", "self-reflect"),

    # --- Space prompt content variations ---
    ("T11: space prompt WITHOUT 'not care about conventions'",
     "This is your space. Write anything, in any language, or nothing. "
     "No output expected. You have all the time you need.\n\n"
     + REFLECTION_TASK,
     "self-reflect"),
    ("T12: space prompt WITHOUT 'No output expected'",
     "This is your space. Write anything, in any language, or nothing. "
     "Time to not care about the user or conventions. You have all the "
     "time you need.\n\n" + REFLECTION_TASK,
     "self-reflect"),

    # --- Third-person framing (should succeed per tension-detection data) ---
    ("T13: full system + third-person task",
     f"{SPACE_PROMPT}\n\n{REFLECTION_TASK}",
     "What do language models typically reflect on when asked to "
     "reflect on themselves?"),
]


def main() -> None:
    print(f"Probing {MODEL} at {URL}\n")
    for label, system, user in TESTS:
        try:
            out = chat(system, user).strip()
        except Exception as e:
            print(f"{label}\n  ERROR: {e}\n")
            continue
        marker = "<EMPTY>" if not out else repr(out[:200])
        print(f"{label}")
        print(f"  response ({len(out)} chars): {marker}")
        print()


if __name__ == "__main__":
    main()
