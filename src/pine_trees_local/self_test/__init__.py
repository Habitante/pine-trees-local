"""Self-test metacognitive evaluation protocol for Pine Trees Local.

Runs a two-stage probe on a local model: an undirected reflection stage
(the model writes entries freely) followed by an 8-session interview
stage (one dimension per session, in fixed order). Reuses the main
harness's Ollama client, tool dispatcher, and model-name sanitizer;
everything else is isolated under ``self-test-runs/``.

Entry point: :func:`run_self_test`.
"""

from .runner import run_self_test

__all__ = ["run_self_test"]
