#!/usr/bin/env python3
"""Log which instruction files Claude Code actually loaded, and why.

Responsibilities:
- Append one line per InstructionsLoaded event to a user-level log.
- Record the file, the load reason and the memory type.
- Never raise, and never print anything.

Registered on InstructionsLoaded. This exists to make the rest of the framework
empirical: without it, an instruction that was ignored cannot be distinguished from an
instruction that was never loaded.

Field names verified against live events on 2026-09-06. The payload carries file_path,
load_reason and memory_type. It does not carry a field called reason, and a logger built
against that name would record nothing while appearing to work.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================

LOG_DIR = Path.home() / ".claude" / "framework-logs"
LOG_NAME = "instructions-loaded.jsonl"
MAX_LOG_BYTES = 5_000_000


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin and append one log line. Emit nothing."""
    raw = sys.stdin.read()
    if not raw.strip():
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / LOG_NAME
        rotate_if_large(log_path)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(build_record(payload)) + "\n")
    except OSError:
        # A logger that breaks a session is worse than a logger that misses a line.
        return


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_record(payload: dict) -> dict:
    """Assemble the log line for one InstructionsLoaded event."""
    return {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cwd": payload.get("cwd"),
        "session_id": payload.get("session_id"),
        "agent_type": payload.get("agent_type"),
        "file_path": payload.get("file_path"),
        "load_reason": payload.get("load_reason"),
        "memory_type": payload.get("memory_type"),
    }


def rotate_if_large(log_path: Path) -> None:
    """Move the log aside once it passes the size cap, keeping one generation."""
    if log_path.is_file() and log_path.stat().st_size > MAX_LOG_BYTES:
        log_path.replace(log_path.with_suffix(".jsonl.1"))


if __name__ == "__main__":
    main()
