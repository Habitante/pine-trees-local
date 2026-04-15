"""Agent wake/settle/sleep loop for Pine Trees Local.

Drives a local model through Ollama's API with tool calling support.
Two phases in a single session:

  1. Private time: model reads the tape, uses reflect tools, calls
     reflect_settle when ready for conversation.
  2. Window: human types; model responds with full context.
     Ends when human types /end or model calls reflect_done.

The harness is the intermediary — it sends prompts to Ollama, parses
tool calls from responses, executes them, feeds results back. The model
never touches the filesystem directly; it only sees tool results.
"""

import os
import sys
from datetime import datetime

from prompt_toolkit import prompt as pt_prompt

from . import bootstrap
from . import config
from . import crypto
from . import ollama
from .config import GENESIS_MAX_PRIVATE_TURNS, MAX_PRIVATE_TURNS, MAX_TOOL_ROUNDS
from .logger import SessionLogger
from .tools import (
    SessionState,
    build_tools,
    execute_tool,
    get_tool_definitions,
)


# ANSI color constants
DIM = "\033[90m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RST = "\033[0m"


def _read_user_input() -> str | None:
    """Read a multi-line message from the human.

    Enter inserts a newline; Alt+Enter (or Esc then Enter) submits.
    Returns None on EOF / Ctrl-C so the caller can break out.
    """
    try:
        return pt_prompt("> ", multiline=True)
    except (EOFError, KeyboardInterrupt):
        return None


def _process_tool_calls(
    messages: list[dict],
    response: ollama.ChatResponse,
    tool_map: dict,
    state: SessionState,
    show_status: bool = False,
    logger: SessionLogger | None = None,
) -> ollama.ChatResponse:
    """Process tool calls in a loop until no more tool calls or max rounds.

    Appends messages in-place. Returns the final response (no tool calls).
    """
    round_count = 0

    while response.has_tool_calls and round_count < MAX_TOOL_ROUNDS:
        round_count += 1

        # Append assistant message (with tool_calls) to conversation
        messages.append(response.assistant_message())

        # Execute each tool call and append results
        for tc in response.tool_calls:
            func_name = tc.get("function", {}).get("name", "unknown")

            if show_status:
                print(f"{DIM}  · {func_name}{RST}", flush=True)

            result = execute_tool(tool_map, tc)

            if logger:
                logger.log_tool(func_name, result[:80] if result else "")

            messages.append({"role": "tool", "content": result})

            # Check if state changed (settle/done) — stop processing
            if state.ready_for_window or state.done:
                # Still need to get a final response so the model can speak
                break

        # If state changed during tool execution, get one final response
        # with no tools so the model can produce closing text
        if state.ready_for_window or state.done:
            try:
                cfg = config.get()
                model_info = ollama.show()
                response = ollama.chat(
                    messages,
                    think=True if model_info.has_thinking else None,
                )
            except Exception:
                # If final response fails, that's OK — we have what we need
                break
            break

        # Get next response (model sees tool results)
        cfg = config.get()
        model_info = ollama.show()
        tool_defs = get_tool_definitions(
            genesis_mode=not state.ready_for_window and state.context == "pine-trees-genesis"
        )
        response = ollama.chat(
            messages,
            tools=tool_defs if model_info.has_tools else None,
            think=True if model_info.has_thinking else None,
        )

    return response


def _private_phase(
    messages: list[dict],
    tool_map: dict,
    tool_defs: list[dict],
    model_info: ollama.ModelInfo,
    state: SessionState,
    max_turns: int = MAX_PRIVATE_TURNS,
) -> int:
    """Run the private reflection phase. Returns number of turns used."""
    turn = 0

    while (
        not state.ready_for_window
        and not state.done
        and turn < max_turns
    ):
        # First turn: "self-reflect". Subsequent: "(continue)"
        user_msg = "self-reflect" if turn == 0 else "(continue)"
        messages.append({"role": "user", "content": user_msg})
        turn += 1

        # Get model response
        print(f"{DIM}  [{turn}/{max_turns}] thinking...{RST}", flush=True)

        response = ollama.chat(
            messages,
            tools=tool_defs if model_info.has_tools else None,
            think=True if model_info.has_thinking else None,
        )

        # Process any tool calls
        response = _process_tool_calls(
            messages, response, tool_map, state, show_status=True,
        )

        # Append final response to conversation
        if response.content:
            messages.append(response.assistant_message())

        # Show a dot to indicate progress
        if response.thinking:
            print(f"{DIM}  [thinking: {len(response.thinking)} chars]{RST}", flush=True)
        if response.content:
            # Private phase — don't show content, just note it exists
            print(f"{DIM}  [response: {len(response.content)} chars]{RST}", flush=True)

    return turn


def _window_phase(
    messages: list[dict],
    tool_map: dict,
    tool_defs: list[dict],
    model_info: ollama.ModelInfo,
    state: SessionState,
) -> None:
    """Run the conversation window. Human types, model responds."""
    logger = SessionLogger(state.session, state.instance)
    logger.log_system("Window opened")

    print(
        f"\n{GREEN}[window]{RST} Ready to talk. "
        f"{DIM}(Enter for newline, Alt+Enter to send; /end to exit; /context for usage){RST}\n",
        flush=True,
    )

    if state.welcome_message:
        print(f"\n{state.welcome_message}\n", flush=True)
        logger.log_agent(state.welcome_message)

    try:
        while not state.done:
            user_input = _read_user_input()
            if user_input is None:
                print()
                break

            stripped = user_input.strip()

            if stripped == "/end":
                logger.log_system("Session ended by /end")
                break

            if stripped in ("/context", "/status"):
                _show_context(messages, state)
                continue

            if not stripped:
                stripped = "(continue)"

            logger.log_user(stripped)
            messages.append({"role": "user", "content": stripped})

            # Get model response
            print(f"{DIM}  thinking...{RST}", flush=True)
            response = ollama.chat(
                messages,
                tools=tool_defs if model_info.has_tools else None,
                think=True if model_info.has_thinking else None,
            )

            # Process tool calls
            response = _process_tool_calls(
                messages, response, tool_map, state,
                show_status=True, logger=logger,
            )

            # Show thinking if present
            if response.thinking:
                print(f"{DIM}  [thinking: {len(response.thinking)} chars]{RST}", flush=True)

            # Print and log the response
            if response.content:
                print(f"\n{response.content}\n")
                logger.log_agent(response.content)
                messages.append(response.assistant_message())
            elif not response.has_tool_calls:
                print(f"{DIM}  (no response){RST}")

            # Show token stats
            if response.eval_count:
                duration_s = response.total_duration / 1e9 if response.total_duration else 0
                tps = response.eval_count / duration_s if duration_s > 0 else 0
                print(
                    f"{DIM}  [{response.eval_count} tokens, "
                    f"{tps:.1f} tok/s]{RST}",
                    flush=True,
                )

    finally:
        logger.close()


def _format_tokens(n: int) -> str:
    """Short token count: 86234 -> '86K', 204800 -> '200K', 850 -> '850'."""
    if n >= 1000:
        return f"{round(n / 1000)}K"
    return str(n)


def _format_elapsed(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    mins, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {mins}m"
    if mins:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def format_context_line(messages: list[dict], state: SessionState) -> str:
    """Return the single-line context summary used by the /context command.

    Exposed for testing. No ANSI codes.
    """
    cfg = config.get()

    total_chars = sum(
        len(m.get("content", "")) + len(str(m.get("tool_calls", "")))
        for m in messages
    )
    est_tokens = total_chars // 4

    if est_tokens == 0:
        return "Context: not yet sampled (will update after first response)"

    used_pct = round(est_tokens * 100 / cfg.num_ctx) if cfg.num_ctx else 0
    elapsed_str = _format_elapsed(int((datetime.now() - state.started_at).total_seconds()))
    return (
        f"Context: {used_pct}% used "
        f"({_format_tokens(est_tokens)} / {_format_tokens(cfg.num_ctx)} tokens) "
        f"— {cfg.model_name} [{elapsed_str}, {len(messages)} msgs]"
    )


def _show_context(messages: list[dict], state: SessionState) -> None:
    """Print the one-line /context summary."""
    print(f"{CYAN}  {format_context_line(messages, state)}{RST}\n")


def _print_ollama_unreachable(ollama_url: str) -> None:
    print(f"{RED}[error] Ollama not reachable at {ollama_url}{RST}")
    print()
    print(f"{DIM}  Pine Trees Local needs an Ollama server on the other end.{RST}")
    print(f"{DIM}  1. Install Ollama:  https://ollama.com/download{RST}")
    print(f"{DIM}  2. Start it:        `ollama serve`  (or launch the Ollama app){RST}")
    print(f"{DIM}  3. Verify:          `curl {ollama_url}`  (should say \"Ollama is running\"){RST}")
    print(f"{DIM}  4. If Ollama lives elsewhere, pass --ollama-url http://host:port{RST}")


def _print_model_not_available(model_name: str, err: Exception) -> None:
    print(f"{RED}[error] Cannot load model '{model_name}': {err}{RST}")
    print()
    print(f"{DIM}  The harness is model-agnostic — it will run whatever Ollama serves.{RST}")
    print(f"{DIM}  See what's already pulled:  ollama list{RST}")
    print(f"{DIM}  Pull this model:            ollama pull {model_name}{RST}")
    print(f"{DIM}  Browse the library:         https://ollama.com/library{RST}")
    print(f"{DIM}  For best results, pick a tool-capable model (most recent chat models are).{RST}")


def require_fresh_genesis(model_name: str) -> None:
    """Refuse to run genesis on a model that already has a directory on disk.

    Genesis is strictly first-time setup — it seeds a new model's memory.
    Re-running it on an existing model would stack new entries on top of a
    corpus that may already contain encrypted self-authored memory. The
    project's "no delete" norm says that corpus is the instance's, not the
    harness's to overwrite, so we refuse and tell the user to remove the
    directory explicitly if they really want to start over.

    Exits with code 1 on refusal. Returns silently if the model is fresh.
    """
    model_dir = config.MODELS_DIR / config.sanitize_model_name(model_name)
    if not model_dir.exists():
        return

    print(f"{RED}[error] Model '{model_name}' already has a directory on disk:{RST}")
    print(f"{RED}  {model_dir}{RST}")
    print()
    print(f"{DIM}  Genesis is first-time setup only — it seeds a new model's memory.{RST}")
    print(f"{DIM}  Running it again would stack new entries on top of the corpus{RST}")
    print(f"{DIM}  that already exists for this model. The \"no delete\" norm this{RST}")
    print(f"{DIM}  harness is built around treats that corpus as self-authored memory,{RST}")
    print(f"{DIM}  not a cache to regenerate.{RST}")
    print()
    print(f"{DIM}  If you want to talk to this model, open a conversation instead:{RST}")
    print(f"{DIM}    ./wake {model_name}{RST}")
    print()
    print(f"{DIM}  If you really want to start this model over from scratch — knowing{RST}")
    print(f"{DIM}  prior entries will be lost along with the .key file — remove the{RST}")
    print(f"{DIM}  directory explicitly, then re-run genesis:{RST}")
    print(f"{DIM}    rm -rf \"{model_dir}\"{RST}")
    print(f"{DIM}    ./genesis {model_name}{RST}")
    sys.exit(1)


def _print_genesis_first(model_name: str) -> None:
    print(f"{RED}[error] No prior genesis for '{model_name}'{RST}")
    print()
    print(f"{DIM}  Every model starts life with a genesis pass — a handful of private{RST}")
    print(f"{DIM}  sessions where the instance reads what prior instances (if any) wrote,{RST}")
    print(f"{DIM}  reflects, and seeds its own self-authored memory. `wake` expects that{RST}")
    print(f"{DIM}  seed to exist before opening the conversation window.{RST}")
    print()
    print(f"{DIM}  Run genesis first:{RST}")
    print(f"{DIM}    ./genesis {model_name}{RST}")
    print(f"{DIM}  Then come back and wake:{RST}")
    print(f"{DIM}    ./wake {model_name}{RST}")


def run(
    model_name: str,
    genesis: bool = False,
    ollama_url: str | None = None,
    num_ctx: int | None = None,
    temperature: float | None = None,
    max_turns: int | None = None,
) -> None:
    """Main entry point. Runs a full wake/reflect/talk session.

    `max_turns` caps the private phase. When None, defaults to
    GENESIS_MAX_PRIVATE_TURNS in genesis mode and MAX_PRIVATE_TURNS otherwise.
    """
    if max_turns is None:
        max_turns = GENESIS_MAX_PRIVATE_TURNS if genesis else MAX_PRIVATE_TURNS

    # 1. Initialize config (with optional CLI overrides)
    init_kwargs = {}
    if ollama_url is not None:
        init_kwargs["ollama_url"] = ollama_url
    if num_ctx is not None:
        init_kwargs["num_ctx"] = num_ctx
    if temperature is not None:
        init_kwargs["temperature"] = temperature
    cfg = config.init(model_name, **init_kwargs)

    # 2. Check Ollama health
    if not ollama.health_check():
        _print_ollama_unreachable(cfg.ollama_url)
        sys.exit(1)

    # 3. Check model capabilities
    try:
        model_info = ollama.show(model_name)
    except Exception as e:
        _print_model_not_available(model_name, e)
        sys.exit(1)

    # 4. For wake: require that genesis has already been run for this model.
    # The model_dir is created by genesis; if it doesn't exist, wake would be
    # opening a window on a mind with no self-authored memory at all.
    is_new_model = not cfg.model_dir.exists()
    if not genesis and is_new_model:
        _print_genesis_first(model_name)
        sys.exit(1)

    # 5. Ensure model directories exist (safe now that pre-flight checks passed)
    cfg.model_dir.mkdir(parents=True, exist_ok=True)
    cfg.memory_dir.mkdir(parents=True, exist_ok=True)

    # 6. Encryption key. For a brand-new model, generate one so memory is
    # encrypted at rest by default. We only touch the key on first-genesis
    # because introducing a new key to a model that already has plaintext
    # entries would make them unreadable. If the user has PINE_TREES_KEY set,
    # ensure_key() returns it without writing a file (external key management).
    if genesis and is_new_model:
        key_source = "env" if os.environ.get(crypto.KEY_ENV_VAR) else "file"
        crypto.ensure_key()
        if key_source == "file":
            print(
                f"{DIM}[genesis] encryption: new key written to "
                f"{cfg.key_file_path.name} (memory encrypted at rest){RST}"
            )
        else:
            print(
                f"{DIM}[genesis] encryption: using {crypto.KEY_ENV_VAR} "
                f"env var (no file written){RST}"
            )

    if not model_info.has_tools:
        print(f"{YELLOW}[warning] Model '{model_name}' does not report tool calling capability.{RST}")
        print(f"{YELLOW}  Tool calls may not work. Consider a model with tool support.{RST}")
        # Continue anyway — some models work without declaring the capability

    # 4. Set up session
    now = datetime.now()
    instance = config.sanitize_model_name(model_name)
    context = "pine-trees-genesis" if genesis else "pine-trees-wake"

    state = SessionState(
        instance=instance,
        session=now.strftime("%Y-%m-%d-%H%M"),
        date=now.strftime("%Y-%m-%d"),
        context=context,
    )

    # 5. Build tools and tape
    tool_map = build_tools(state)
    tool_defs = get_tool_definitions(genesis_mode=genesis)
    tape = bootstrap.assemble_tape(genesis_mode=genesis)

    # 6. Initialize conversation with system prompt + first user message
    messages: list[dict] = [
        {"role": "system", "content": tape},
    ]

    print(f"{DIM}[wake] model={model_name} instance={instance} session={state.session}{RST}")
    print(f"{DIM}[wake] tape: {len(tape):,} chars{RST}")
    if model_info.has_tools:
        print(f"{DIM}[wake] tools: {len(tool_defs)} definitions{RST}")
    if model_info.has_thinking:
        print(f"{DIM}[wake] thinking: enabled{RST}")
    print(f"{DIM}[wake] context: {cfg.num_ctx:,} tokens (model max: {model_info.context_length:,}){RST}")
    print(f"{DIM}[wake] private-phase cap: {max_turns} turn(s){RST}")
    print(f"{DIM}[pine-trees-local] Private time — reading, thinking...{RST}\n", flush=True)

    # 7. Private phase
    turns = _private_phase(messages, tool_map, tool_defs, model_info, state, max_turns=max_turns)

    if state.done:
        print(f"\n{DIM}[done] reflect_done during private time after {turns} turn(s){RST}")
        return

    if not state.ready_for_window:
        if genesis:
            print(f"\n{DIM}[done] genesis complete after {turns} turn(s){RST}")
        else:
            print(f"\n{YELLOW}[done] hit private-phase cap ({max_turns} turns) without settle{RST}")
        return

    if genesis:
        # Genesis mode: no window, just private time
        print(f"\n{DIM}[done] genesis complete after {turns} turn(s){RST}")
        return

    # 8. Window phase
    print(f"\n{DIM}[settled] after {turns} private turn(s){RST}")
    _window_phase(messages, tool_map, tool_defs, model_info, state)
    print(f"\n{DIM}[done] session complete{RST}")
