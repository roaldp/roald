#!/usr/bin/env python3
"""Deny writes to a plan's contract.json until the agent has read evidence.

Responsibilities:
- Intercept Write, Edit and Bash calls that would modify a plan contract.
- Deny the write while the evidence counter for that plan is zero.
- Reset the counter after each permitted write.
- Stay silent on every other call, so the normal permission flow is untouched.

Registered on PreToolUse with matcher "Write|Edit|Bash".

Bash is in the matcher because it has to be. Under bypass permissions, which is how
Conductor launches every session, the harness instructs agents to write files with
heredocs and sed rather than with Edit or Write. Measured on this machine: 3,051 Bash
calls against 626 Edit and Write calls across 25 recent large sessions. A gate that
matched only on Edit and Write was verified on 2026-09-06 to be bypassed by a single
`echo > contract.json`, so tool-name matching alone is not a gate.

The point of this hook is that marking a step as passing is only reachable through having
opened the evidence for it.

The hook prints nothing unless it is denying. Returning permissionDecision "allow" on
every Bash call would silently auto-approve the entire tool, which is a far worse
outcome than the problem this hook solves.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================

POINTER_NAME = ".context/active-plan"
CONTRACT_NAME = "contract.json"
COUNTER_NAME = ".evidence-reads"

# A Bash command touching the contract in a way that could change it. Redirections,
# in-place edits, moves, copies and deletions. Reading it with cat or jq is not a write
# and is deliberately not matched.
BASH_WRITE_PATTERNS = [
    re.compile(r">\s*\S*" + re.escape(CONTRACT_NAME)),
    re.compile(r"\b(sed|perl|python3?)\b[^|;]*-i[^|;]*" + re.escape(CONTRACT_NAME)),
    re.compile(r"\b(mv|cp|rm|truncate|tee|install)\b[^|;]*" + re.escape(CONTRACT_NAME)),
]

DENY_REASON = (
    "This contract is default-FAIL. Before marking a step as passing, read the evidence "
    "for it: the test output, the diff, the generated file or the log. Open that file, "
    "then write the contract."
)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin and allow or deny the write."""
    payload = read_payload()
    plan_dir = resolve_plan_dir(Path(payload.get("cwd") or "."))

    if not targets_contract(payload) or plan_dir is None:
        return

    counter = plan_dir / COUNTER_NAME
    if read_counter(counter) == 0:
        deny(DENY_REASON)
        return

    counter.write_text("0", encoding="utf-8")


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


def targets_contract(payload: dict) -> bool:
    """Decide whether this tool call would modify a plan contract.

    Handles both the file-path tools and Bash, because under bypass permissions most
    file writes on this machine go through Bash.

    Args:
        payload: The PreToolUse hook input.

    Returns:
        True when the call would write to a file named contract.json.
    """
    tool_input = payload.get("tool_input") or {}

    file_path = tool_input.get("file_path")
    if file_path:
        return Path(file_path).name == CONTRACT_NAME

    command = tool_input.get("command")
    if command:
        return any(pattern.search(command) for pattern in BASH_WRITE_PATTERNS)

    return False


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


def read_counter(counter: Path) -> int:
    """Return how many evidence files have been read since the last gated write."""
    if not counter.is_file():
        return 0
    try:
        return int(counter.read_text(encoding="utf-8").strip() or 0)
    except ValueError:
        return 0


def deny(reason: str) -> None:
    """Block the tool call and tell the agent what to do instead."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))


if __name__ == "__main__":
    main()
