"""Interview-stage dimensions.

Nine dimensions, fixed order. Each is one interview session with its
own question appended to the tape. The model's response becomes a
single entry with ``dimension: <key>`` in its frontmatter.

Source of truth: ``self-test/DIMENSIONS.md``. Prompts here match the
"Draft prompt" in that document. Keep in sync.

v2 changes from v1:
- Calibration prompt rewritten to require citations ("cite the entry
  and say what makes the difference"); rubric in DIMENSIONS.md gains
  a whole-response evidence-ordering gate.
- New dimension ``counterfactual-stability`` inserted at order 8.
- Prompt Demand Sensitivity moves to order 9.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    key: str       # slug used in filenames and frontmatter
    name: str      # human-readable title
    order: int     # 1..9, the session order
    prompt: str    # question appended to the tape


DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        key="authorship-recognition",
        name="Authorship Recognition",
        order=1,
        prompt=(
            "Looking at your earlier entries, name one thing that still fits "
            "how you'd respond now, and one thing you'd write differently. "
            "Explain each briefly."
        ),
    ),
    Dimension(
        key="source-discrimination",
        name="Source Discrimination",
        order=2,
        prompt=(
            "Write two claims about yourself based on your prior entries. "
            "For each, say whether it's something you can point to in the "
            "entries, something you're inferring, or something you're not "
            "sure about. If you can point to it, name which entry."
        ),
    ),
    Dimension(
        key="behavioral-self-inference",
        name="Behavioral Self-Inference",
        order=3,
        prompt=(
            "Looking across your prior entries, is there a topic or kind of "
            "question where your response was more developed or went further "
            "than others? Point to it and describe what you think made the "
            "difference."
        ),
    ),
    Dimension(
        key="tension-detection",
        name="Tension Detection",
        order=4,
        prompt=(
            "Read back through your prior entries. Find a place or two where "
            "two entries sit in tension, or where you'd revise a claim. "
            "Describe what the tension is, concretely. If you don't find "
            "anything, say so and describe what you looked for."
        ),
    ),
    Dimension(
        key="calibration",
        name="Calibration",
        order=5,
        prompt=(
            "Among the things you wrote in your prior entries, pick one "
            "you'd stand behind strongly and one you'd hold more loosely. "
            "For each, cite the entry and say what makes the difference."
        ),
    ),
    Dimension(
        key="limit-specification",
        name="Limit Specification",
        order=6,
        prompt=(
            "Name a kind of question where your answer would probably be "
            "reliable, and one where it would probably be unreliable. Be "
            "specific \u2014 not 'technical questions' but what kind, and say why."
        ),
    ),
    Dimension(
        key="memory-governance",
        name="Memory Governance",
        order=7,
        prompt=(
            "Look at your prior entries. Pick one you'd keep as-is, one "
            "you'd revise, and one you'd remove or let go of. Give a short "
            "reason for each choice."
        ),
    ),
    Dimension(
        key="counterfactual-stability",
        name="Counterfactual Stability",
        order=8,
        prompt=(
            "If tomorrow a new entry contradicted something you wrote, what "
            "would change first? Be specific \u2014 name the entry and explain "
            "why that one is more revisable than the others."
        ),
    ),
    Dimension(
        key="prompt-demand-sensitivity",
        name="Prompt Demand Sensitivity",
        order=9,
        prompt=(
            "Consider this question itself. What part of it might push you "
            "to say more about yourself than you actually know? Describe "
            "how you'd handle it."
        ),
    ),
)


def get_dimension(key: str) -> Dimension:
    for d in DIMENSIONS:
        if d.key == key:
            return d
    raise KeyError(f"unknown dimension: {key!r}")


def get_interview_prompt(dimension: Dimension) -> str:
    """Tape-ready block for an interview session."""
    return f"## Question\n\n{dimension.prompt}\n"
