#!/usr/bin/env python3
"""Count evidence files the agent has read, so contract_gate.py can release its block.

Responsibilities:
- Watch successful Read calls.
- Increment a per-plan counter when the file read looks like evidence.

Registered on PostToolUse with matcher "Read|Bash". Bash is included because under bypass
permissions the harness instructs agents to read with cat, head and sed -n rather than with
the Read tool. A counter that only watched Read would stay at zero and deadlock the gate.

Evidence means something the agent did not write in this turn and that shows whether a step
actually worked: test output, a log, a diff, a screenshot, or any file inside the active
plan's own directory.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================

POINTER_NAME = ".context/active-plan"
COUNTER_NAME = ".evidence-reads"

EVIDENCE_SUFFIXES = {".log", ".txt", ".json", ".xml", ".png", ".jpg", ".diff", ".patch"}
EVIDENCE_HINTS = ("test", "output", "result", "report", "coverage", "screenshot", "evidence")

# Reading these can never count as evidence. The contract and the plan are the things the
# agent is asserting about, and the counter is the gate's own state. Without this, the
# Edit tool's mandatory read-before-write silently unlocks the gate every time.
NEVER_EVIDENCE = {"contract.json", "PLAN.md", ".evidence-reads"}

# Bash commands that read a file rather than write it. A redirection anywhere in the
# command disqualifies it, so `cat evidence.log > contract.json` never counts as a read.
BASH_READERS = {"cat", "head", "tail", "less", "more", "bat", "jq", "grep", "rg", "sed", "awk"}
BASH_REDIRECT = re.compile(r"(?<!\d)>|\btee\b")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin and bump the counter when evidence was read."""
    payload = read_payload()
    plan_dir = resolve_plan_dir(Path(payload.get("cwd") or "."))
    if plan_dir is None:
        return

    read_paths = extract_read_paths(payload)
    if not any(is_evidence(path, plan_dir) for path in read_paths):
        return

    counter = plan_dir / COUNTER_NAME
    current = int(counter.read_text(encoding="utf-8").strip() or 0) if counter.is_file() else 0
    counter.write_text(str(current + 1), encoding="utf-8")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def read_payload() -> dict:
    """Parse the hook JSON from stdin, tolerating an empty or malformed body."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def extract_read_paths(payload: dict) -> list[Path]:
    """Return the files this tool call read.

    Handles the Read tool's file_path, and Bash commands that read a file with cat, head,
    grep and friends. A Bash command containing a redirection is treated as a write and
    contributes nothing, so piping evidence into the contract cannot unlock the gate.

    Args:
        payload: The PostToolUse hook input.

    Returns:
        Paths the call read. Empty when the call read nothing identifiable.
    """
    tool_input = payload.get("tool_input") or {}

    file_path = tool_input.get("file_path")
    if file_path:
        return [Path(file_path)]

    command = tool_input.get("command")
    if not command or BASH_REDIRECT.search(command):
        return []

    try:
        tokens = shlex.split(command)
    except ValueError:
        return []

    if not tokens or Path(tokens[0]).name not in BASH_READERS:
        return []
    return [Path(token) for token in tokens[1:] if not token.startswith("-")]


def resolve_plan_dir(project_dir: Path) -> Path | None:
    """Return the directory of the active plan, or None when no plan is active."""
    pointer = project_dir / POINTER_NAME
    if not pointer.is_file():
        return None
    target = pointer.read_text(encoding="utf-8").strip()
    if not target:
        return None
    plan_path = Path(target)
    if not plan_path.is_absolute():
        plan_path = project_dir / plan_path
    return plan_path.parent if plan_path.is_file() else None


def is_evidence(path: Path, plan_dir: Path) -> bool:
    """Decide whether a file counts as evidence for the active plan."""
    if path.name in NEVER_EVIDENCE:
        return False
    if plan_dir in path.parents:
        return True
    if path.suffix.lower() in EVIDENCE_SUFFIXES:
        return True
    lowered = path.name.lower()
    return any(hint in lowered for hint in EVIDENCE_HINTS)


if __name__ == "__main__":
    main()
