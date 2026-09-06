#!/usr/bin/env python3
"""Deny writes to a plan's contract.json until the agent has read evidence for it.

Responsibilities:
- Intercept Write, Edit and Bash calls that would modify the active plan's contract.
- Deny the write while this agent's evidence counter is zero.
- Reset that counter after each permitted write.
- Stay silent on every other call, so the normal permission flow is untouched.

Registered on PreToolUse with matcher "Write|Edit|Bash", and off by default. Install it
with `install_framework.py --with-gate` once there is a job long enough to want it.

**This is friction, not a boundary, and it should not be described as one.** Three known
limits, all verified:

- A shell command can evade the patterns. `F=contract.json; echo x > $F` is not matched,
  and neither is a glob, `dd`, or a Python one-liner. Pattern-matching a shell command is
  not containment.
- One evidence read permits one write, and that write may flip every step at once. The
  counter carries no association between the evidence and the step it justifies.
- The patterns can also block an ordinary command that happens to name the contract.

For anything that must never be written at all, use `permissions.deny` with
`Edit(**/contract.json)`. That was verified to hold under bypass permissions. Note that
`Write(path)` rules are not matched by file permission checks while `Edit(path)` rules
cover every file-editing tool. A permanent deny cannot express "deny until evidence is
read", which is the only reason this hook exists.

Bash is in the matcher because it has to be. Measured here: 6,429 Bash calls against 1,640
Edit and Write across 52 recent large sessions, because the bypass-permissions system
reminder tells agents to prefer heredocs and sed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_state  # noqa: E402  (path set above so the hook runs from any directory)

# ============================================================================
# CONSTANTS
# ============================================================================

CONTRACT = re.escape(plan_state.CONTRACT_NAME)

# Bash forms that would change the contract. Deliberately narrow: a false deny on an
# ordinary command is worse than a miss here, because the gate is friction rather than
# containment, and a wrongly blocked command is what gets the whole thing switched off.
BASH_WRITE_PATTERNS = [
    re.compile(r">>?\s*\S*" + CONTRACT),
    re.compile(r"\b(?:sed|perl|python3?)\b[^|;&]*\s-i[^|;&]*" + CONTRACT),
    re.compile(r"\b(?:mv|rm|truncate|tee)\b[^|;&]*" + CONTRACT),
]

DENY_REASON = (
    "This contract is default-FAIL. Before marking a step as passing, read the evidence "
    "for it inside the plan directory: the test output, the diff, the generated file or "
    "the log. Open that file, then write the contract."
)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin. Print a denial, or print nothing."""
    payload = plan_state.read_payload(sys.stdin)
    project = plan_state.project_dir(payload)

    plan_path = plan_state.active_plan(project)
    if plan_path is None or not targets_contract(payload):
        return

    counter = plan_state.counter_path(plan_path.parent, payload)
    if plan_state.read_counter(counter) == 0:
        deny(DENY_REASON)
        return

    counter.write_text("0", encoding="utf-8")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def targets_contract(payload: dict) -> bool:
    """Decide whether this tool call would modify a plan contract.

    Args:
        payload: The PreToolUse hook input.

    Returns:
        True when the call writes to a file named contract.json.
    """
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return False

    file_path = tool_input.get("file_path")
    if isinstance(file_path, str) and file_path:
        return Path(file_path).name == plan_state.CONTRACT_NAME

    command = tool_input.get("command")
    if isinstance(command, str) and command:
        return any(pattern.search(command) for pattern in BASH_WRITE_PATTERNS)

    return False


def deny(reason: str) -> None:
    """Block the tool call and tell the agent what to do instead."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))


if __name__ == "__main__":
    main()
