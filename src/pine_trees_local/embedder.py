"""Embedding via Ollama's local API.

Calls /api/embed with nomic-embed-text. Pure stdlib — no external
dependencies. Uses task prefixes (search_document / search_query)
for better retrieval quality.
"""

import json
import urllib.request
import urllib.error

from . import config


def embed_document(text: str) -> list[float]:
    """Embed text for storage. Returns 768-dim vector."""
    return _embed(f"search_document: {text}")


def embed_query(text: str) -> list[float]:
    """Embed text for search. Returns 768-dim vector."""
    return _embed(f"search_query: {text}")


def _embed(text: str) -> list[float]:
    """Call Ollama's /api/embed endpoint."""
    cfg = config.get()
    payload = json.dumps({"model": cfg.embed_model, "input": text}).encode()
    req = urllib.request.Request(
        f"{cfg.ollama_url}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Ollama unreachable at {cfg.ollama_url}: {e}"
        ) from e

    embeddings = data.get("embeddings")
    if not embeddings or not embeddings[0]:
        raise ValueError(f"Empty embedding response: {data}")
    return embeddings[0]
