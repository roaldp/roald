#!/usr/bin/env python3
"""Re-inject the active plan pointer into a session or subagent that has lost it.

Responsibilities:
- Read the active-plan pointer for the current project.
- Emit the plan path, current phase and next unchecked step as additionalContext.
- Stay silent when there is no active plan, so ordinary sessions cost nothing.

Registered on SessionStart (matcher compact|resume) and SubagentStart. Both were verified
to deliver additionalContext on 2026-09-06; see
.docs/plans/2026.09.06-agent-operating-framework/04-verification-results.md.

The pointer file is deliberately a path and not the plan itself. The plan is on disk and
the agent can read it; injecting the whole thing would waste context on every subagent.
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
MAX_CONTEXT_CHARS = 9000  # the hook limit is 10,000; leave headroom
UNCHECKED_STEP = re.compile(r"^\s*[-*]\s*\[ \]\s*(.+)$", re.MULTILINE)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin and print additionalContext, or nothing."""
    payload = read_payload()
    project_dir = Path(payload.get("cwd") or ".")

    plan_path = resolve_active_plan(project_dir)
    if plan_path is None:
        return

    anchor = build_anchor(plan_path, payload)
    emit(payload.get("hook_event_name", "SessionStart"), anchor)


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


def resolve_active_plan(project_dir: Path) -> Path | None:
    """Find the plan this project is currently working to.

    Args:
        project_dir: The session's working directory.

    Returns:
        Path to PLAN.md, or None when no active plan is set or the pointer is stale.
    """
    pointer = project_dir / POINTER_NAME
    if not pointer.is_file():
        return None

    target = pointer.read_text(encoding="utf-8").strip()
    if not target:
        return None

    plan_path = Path(target)
    if not plan_path.is_absolute():
        plan_path = project_dir / plan_path
    return plan_path if plan_path.is_file() else None


def build_anchor(plan_path: Path, payload: dict) -> str:
    """Assemble the short re-anchor message.

    Args:
        plan_path: The active PLAN.md.
        payload: The hook input, used to tailor wording for subagents.

    Returns:
        The text to inject, under the additionalContext character cap.
    """
    is_subagent = payload.get("hook_event_name") == "SubagentStart"
    lines = [f"ACTIVE PLAN: {plan_path}"]

    phase = read_current_phase(plan_path.parent / CONTRACT_NAME)
    if phase is not None:
        lines.append(f"CURRENT PHASE: {phase}")

    step = read_next_step(plan_path)
    if step is not None:
        lines.append(f"NEXT UNCHECKED STEP: {step}")

    if is_subagent:
        lines.append(
            "You are a subagent. You inherit none of the parent's context. "
            "Read the plan file before doing anything, do only the step you were given, "
            "and write your output to the path named in your brief."
        )
    else:
        lines.append(
            "Work to this plan. If you are about to do something the plan does not "
            "cover, say so and record it in the plan's Log section before doing it."
        )

    return "\n".join(lines)[:MAX_CONTEXT_CHARS]


def read_current_phase(contract_path: Path) -> str | None:
    """Return the first phase in the contract that is not yet passing."""
    if not contract_path.is_file():
        return None
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    for name, state in contract.items():
        if isinstance(state, dict) and not state.get("passes"):
            return name
    return "all phases passing"


def read_next_step(plan_path: Path) -> str | None:
    """Return the first unchecked checklist item in the plan."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = UNCHECKED_STEP.search(text)
    return match.group(1).strip() if match else None


def emit(event_name: str, context: str) -> None:
    """Print the hook's JSON response."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
