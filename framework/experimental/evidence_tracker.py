#!/usr/bin/env python3
"""Count evidence files the agent has read, so contract_gate.py can release its block.

Responsibilities:
- Watch Read calls and Bash commands that read a file.
- Increment this agent's evidence counter when the file read is evidence for the plan.

Registered on PostToolUse with matcher "Read|Bash". Bash is in the matcher because under
bypass permissions the harness tells agents to read with cat, head and sed -n. A counter
watching only Read would stay at zero and deadlock the gate.

**Evidence means a file inside the active plan's own directory**, and nothing else. An
earlier version also counted any .json, .txt or .log anywhere on disk, which meant the
first `cat package.json` of any job opened the gate before the agent had done any work.
The plan says where its evidence goes; a file outside that directory is not evidence.

The contract, the plan and the counters can never count, because the Edit tool must read
a file before writing it, and without that exclusion reading the contract unlocked writing
the contract.
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_state  # noqa: E402  (path set above so the hook runs from any directory)

# ============================================================================
# CONSTANTS
# ============================================================================

NEVER_EVIDENCE = {plan_state.CONTRACT_NAME, plan_state.PLAN_NAME}

# Commands that read rather than write. A redirection anywhere in the command disqualifies
# it, so `cat evidence.log > contract.json` never counts as a read.
BASH_READERS = {"cat", "head", "tail", "less", "more", "bat", "jq", "grep", "rg", "sed", "awk"}
REDIRECTS = (">", ">>", "tee", "|")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin and bump this agent's counter when evidence was read."""
    payload = plan_state.read_payload(sys.stdin)
    project = plan_state.project_dir(payload)

    plan_path = plan_state.active_plan(project)
    if plan_path is None:
        return
    plan_dir = plan_path.parent

    if not any(is_evidence(path, plan_dir) for path in extract_read_paths(payload, project)):
        return

    counter = plan_state.counter_path(plan_dir, payload)
    counter.write_text(str(plan_state.read_counter(counter) + 1), encoding="utf-8")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def extract_read_paths(payload: dict, project: Path) -> list:
    """Return the files this tool call read.

    Handles the Read tool's file_path and Bash commands that read with cat, head, grep and
    friends. Every field is type-checked, because the tool schema is not under this repo's
    control and a hook that raises prints an error banner on every tool call.

    Args:
        payload: The PostToolUse hook input.
        project: The session's working directory, for resolving relative paths.

    Returns:
        Resolved paths the call read. Empty when the call read nothing identifiable.
    """
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []

    file_path = tool_input.get("file_path")
    if isinstance(file_path, str) and file_path:
        return [resolve(file_path, project)]

    command = tool_input.get("command")
    if not isinstance(command, str) or not command:
        return []
    if any(token in command for token in REDIRECTS):
        return []

    try:
        tokens = shlex.split(command)
    except ValueError:
        return []
    if not tokens or Path(tokens[0]).name not in BASH_READERS:
        return []

    return [resolve(token, project) for token in tokens[1:] if not token.startswith("-")]


def resolve(raw: str, project: Path) -> Path:
    """Resolve a path from a tool call against the project directory."""
    path = Path(raw)
    if not path.is_absolute():
        path = project / path
    try:
        return path.resolve()
    except OSError:
        return path


def is_evidence(path: Path, plan_dir: Path) -> bool:
    """Decide whether a file counts as evidence for the active plan.

    Args:
        path: A resolved path the agent read.
        plan_dir: The active plan's directory.

    Returns:
        True only for a file inside the plan directory that is not the plan, the contract
        or a counter.
    """
    if path.name in NEVER_EVIDENCE or path.name.startswith(plan_state.COUNTER_PREFIX):
        return False
    return plan_dir in path.parents


if __name__ == "__main__":
    main()
