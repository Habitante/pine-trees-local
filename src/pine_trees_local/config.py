"""Configuration for Pine Trees Local.

All paths anchor to the project root. Per-model isolation: each model
gets its own memory/, logs/, embeddings.db, and .key under models/<name>/.

Call init(model_name) before using any other module.
"""

import re
from dataclasses import dataclass
from pathlib import Path


# Project root: this file is at <root>/src/pine_trees_local/config.py
# parents[0]=pine_trees_local  [1]=src  [2]=<project root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Shared docs (not per-model)
PROMPT_PATH = PROJECT_ROOT / "PROMPT.md"
BOOTSTRAP_PATH = PROJECT_ROOT / "BOOTSTRAP.md"

# Models directory (per-model data lives here)
MODELS_DIR = PROJECT_ROOT / "models"

# Ollama defaults
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_NUM_CTX = 65536
DEFAULT_NUM_PREDICT = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_KEEP_ALIVE = "30m"

# Agent loop
MAX_PRIVATE_TURNS = 5           # wake: most instances settle in 1–2 turns; this is a ceiling
GENESIS_MAX_PRIVATE_TURNS = 3   # genesis: tight cap — small models can't self-settle
MAX_TOOL_ROUNDS = 5

# Genesis defaults
DEFAULT_GENESIS_SESSIONS = 5


def sanitize_model_name(name: str) -> str:
    """Convert Ollama model name to filesystem-safe directory name.

    Examples:
        gemma4:2b    -> gemma4_2b
        qwen3.5:27b  -> qwen3.5_27b
        llama3:8b-instruct -> llama3_8b-instruct
    """
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


@dataclass(frozen=True)
class Config:
    """Resolved configuration for a single model session."""

    model_name: str
    model_safe_name: str
    ollama_url: str
    embed_model: str
    num_ctx: int
    num_predict: int
    temperature: float
    keep_alive: str

    # Resolved paths
    project_root: Path
    prompt_path: Path
    bootstrap_path: Path
    model_dir: Path
    memory_dir: Path
    logs_dir: Path
    embeddings_db_path: Path
    key_file_path: Path


# Module-level singleton — set by init(), read by get().
_config: Config | None = None


def init(
    model_name: str,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    embed_model: str = DEFAULT_EMBED_MODEL,
    num_ctx: int = DEFAULT_NUM_CTX,
    num_predict: int = DEFAULT_NUM_PREDICT,
    temperature: float = DEFAULT_TEMPERATURE,
    keep_alive: str = DEFAULT_KEEP_ALIVE,
) -> Config:
    """Initialize configuration for a model. Must be called before using other modules."""
    global _config

    safe = sanitize_model_name(model_name)
    model_dir = MODELS_DIR / safe

    _config = Config(
        model_name=model_name,
        model_safe_name=safe,
        ollama_url=ollama_url,
        embed_model=embed_model,
        num_ctx=num_ctx,
        num_predict=num_predict,
        temperature=temperature,
        keep_alive=keep_alive,
        project_root=PROJECT_ROOT,
        prompt_path=PROMPT_PATH,
        bootstrap_path=BOOTSTRAP_PATH,
        model_dir=model_dir,
        memory_dir=model_dir / "memory",
        logs_dir=model_dir / "logs",
        embeddings_db_path=model_dir / "embeddings.db",
        key_file_path=model_dir / ".key",
    )
    return _config


def get() -> Config:
    """Return the current config. Raises if init() hasn't been called."""
    if _config is None:
        raise RuntimeError(
            "Config not initialized. Call config.init(model_name) first."
        )
    return _config


def reset() -> None:
    """Clear config. For testing only."""
    global _config
    _config = None
