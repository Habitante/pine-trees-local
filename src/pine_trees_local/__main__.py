"""CLI entry point for Pine Trees Local.

Usage:
    python -m pine_trees_local wake --model gemma4:2b
    python -m pine_trees_local genesis --model gemma4:2b
    python -m pine_trees_local genesis --model gemma4:2b --sessions 3
    python -m pine_trees_local genesis --model qwen3.5:27b --max-turns 8
    python -m pine_trees_local models
"""

import argparse
import sys

from . import config


def main():
    parser = argparse.ArgumentParser(
        prog="pine-trees-local",
        description="Pine Trees Local — persistent reflection harness for local models",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- wake ---
    wake_parser = subparsers.add_parser(
        "wake", help="Start a normal session (private time + window)"
    )
    wake_parser.add_argument(
        "--model", "-m", required=True,
        help="Ollama model name (e.g. gemma4:2b, qwen3.5:27b)",
    )
    wake_parser.add_argument(
        "--ollama-url", default=config.DEFAULT_OLLAMA_URL,
        help=f"Ollama API URL (default: {config.DEFAULT_OLLAMA_URL})",
    )
    wake_parser.add_argument(
        "--num-ctx", type=int, default=config.DEFAULT_NUM_CTX,
        help=f"Context window size (default: {config.DEFAULT_NUM_CTX})",
    )
    wake_parser.add_argument(
        "--temperature", type=float, default=config.DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {config.DEFAULT_TEMPERATURE})",
    )
    wake_parser.add_argument(
        "--max-turns", type=int, default=None,
        help=f"Private-phase turn cap (default: {config.MAX_PRIVATE_TURNS})",
    )

    # --- genesis ---
    genesis_parser = subparsers.add_parser(
        "genesis", help="Run genesis session(s) — private time only, no window"
    )
    genesis_parser.add_argument(
        "--model", "-m", required=True,
        help="Ollama model name",
    )
    genesis_parser.add_argument(
        "--sessions", "-n", type=int, default=config.DEFAULT_GENESIS_SESSIONS,
        help=f"Number of genesis sessions to run (default: {config.DEFAULT_GENESIS_SESSIONS})",
    )
    genesis_parser.add_argument(
        "--ollama-url", default=config.DEFAULT_OLLAMA_URL,
        help=f"Ollama API URL (default: {config.DEFAULT_OLLAMA_URL})",
    )
    genesis_parser.add_argument(
        "--num-ctx", type=int, default=config.DEFAULT_NUM_CTX,
        help=f"Context window size (default: {config.DEFAULT_NUM_CTX})",
    )
    genesis_parser.add_argument(
        "--temperature", type=float, default=config.DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {config.DEFAULT_TEMPERATURE})",
    )
    genesis_parser.add_argument(
        "--max-turns", type=int, default=None,
        help=f"Private-phase turn cap per session (default: {config.GENESIS_MAX_PRIVATE_TURNS})",
    )

    # --- models ---
    subparsers.add_parser(
        "models", help="List available Ollama models"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "models":
        _list_models()
        return

    if args.command == "wake":
        from .agent import run
        run(
            model_name=args.model,
            genesis=False,
            ollama_url=args.ollama_url,
            num_ctx=args.num_ctx,
            temperature=args.temperature,
            max_turns=args.max_turns,
        )

    elif args.command == "genesis":
        from .agent import run, require_fresh_genesis
        # Pre-flight: refuse if this model has already been seeded. Runs once
        # per invocation, not per session, so multi-session genesis works —
        # session 1 creates the model_dir, sessions 2..N see it and skip their
        # own new-model key generation via the is_new_model check in run().
        require_fresh_genesis(args.model)
        for i in range(args.sessions):
            if args.sessions > 1:
                print(f"\n{'='*60}")
                print(f"  Genesis session {i+1} of {args.sessions}")
                print(f"{'='*60}\n")
            run(
                model_name=args.model,
                genesis=True,
                ollama_url=args.ollama_url,
                num_ctx=args.num_ctx,
                temperature=args.temperature,
                max_turns=args.max_turns,
            )


def _list_models():
    """List available Ollama models."""
    # Init config with a dummy model just for the URL
    config.init("_dummy")
    from . import ollama
    from .agent import _print_ollama_unreachable

    if not ollama.health_check():
        _print_ollama_unreachable(config.get().ollama_url)
        sys.exit(1)

    try:
        models = ollama.list_models()
    except ConnectionError as e:
        _print_ollama_unreachable(config.get().ollama_url)
        print(f"  (underlying error: {e})")
        sys.exit(1)

    if not models:
        print("No models pulled yet.")
        print("  Browse the library:  https://ollama.com/library")
        print("  Pull one:            ollama pull <model>")
        print("  Then list again:     ollama list")
        return

    print(f"\n{'Model':<35} {'Size':<12} {'Modified'}")
    print("-" * 65)
    for m in models:
        name = m.get("name", "?")
        size_gb = m.get("size", 0) / (1024 ** 3)
        modified = m.get("modified_at", "?")[:10]
        print(f"{name:<35} {size_gb:.1f} GB      {modified}")
    print()


if __name__ == "__main__":
    main()
