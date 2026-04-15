"""Session conversation logger.

Writes one plain text file per session to models/<model>/logs/.
Captures only the window phase — private reflection stays private.

Files are plain text, greppable, not encrypted.
"""

from datetime import datetime
from pathlib import Path

from . import config


class SessionLogger:
    """Logs the window-phase conversation to a dated text file."""

    def __init__(self, session: str, instance: str):
        cfg = config.get()
        logs_dir = cfg.logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.path = logs_dir / f"{session}.log"
        self._file = open(self.path, "w", encoding="utf-8")
        self._write(f"# Pine Trees Local session: {session}")
        self._write(f"# Model: {cfg.model_name}")
        self._write(f"# Instance: {instance}")
        self._write(f"# Started: {datetime.now().isoformat()}")
        self._write("")

    def _write(self, line: str) -> None:
        self._file.write(line + "\n")
        self._file.flush()

    def log_system(self, text: str) -> None:
        self._write(f"[system] {text}")

    def log_user(self, text: str) -> None:
        self._write("")
        self._write(f"User: {text}")
        self._write("")

    def log_agent(self, text: str) -> None:
        self._write(f"Model: {text}")

    def log_tool(self, name: str, result_preview: str = "") -> None:
        preview = f" -> {result_preview[:80]}" if result_preview else ""
        self._write(f"  · {name}{preview}")

    def log_thinking(self, text: str) -> None:
        """Log thinking (optional — for debugging, not shown to user)."""
        if text.strip():
            self._write(f"  [think] {text[:200]}...")

    def close(self) -> None:
        self._write("")
        self._write(f"# Ended: {datetime.now().isoformat()}")
        self._file.close()
