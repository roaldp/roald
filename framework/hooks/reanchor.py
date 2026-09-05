#!/usr/bin/env python3
"""Re-inject the active plan pointer into a session or subagent that has lost it.

Responsibilities:
- Find the active plan for the current project.
- Emit its path, the current phase and the next unticked step as additionalContext.
- Stay silent when there is no active plan, so ordinary sessions cost nothing.

Registered on SessionStart with matcher "startup|resume|compact", and on SubagentStart.
All three SessionStart sources and the SubagentStart delivery were observed directly on
2026-09-06; see 04-verification-results.md findings 2, 3, 6 and 12.

Startup is in the matcher deliberately. The anchor costs nothing in a directory with no
active plan, because this hook prints nothing there, and a session that starts inside a
planned job wants the pointer as much as one that resumes.

SubagentStart is the one that earns this hook. A subagent inherits no conversation
history, no files the parent read, no invoked skills and no auto memory, so without this
a delegated worker does not know a plan exists.

The hook emits a pointer, not the plan. The plan is on disk and the agent can read it;
injecting the whole thing would spend context on every subagent for no gain.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_state  # noqa: E402  (path set above so the hook runs from any directory)

# ============================================================================
# CONSTANTS
# ============================================================================

MAX_CONTEXT_CHARS = 9000  # the documented cap is 10,000; leave headroom

SUBAGENT_NOTE = (
    "You are a subagent. You inherit none of the parent's context. Read the plan file "
    "before doing anything, do only the step you were given, and write your output to "
    "the path named in your brief."
)

SESSION_NOTE = (
    "Work to this plan. If you are about to do something the plan does not cover, say so "
    "and record it in the plan's Log section before doing it."
)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Read the hook payload on stdin and print additionalContext, or nothing."""
    payload = plan_state.read_payload(sys.stdin)
    project = plan_state.project_dir(payload)

    plan_path = plan_state.active_plan(project)
    if plan_path is None:
        return

    anchor = build_anchor(plan_path, payload)
    event = payload.get("hook_event_name") or "SessionStart"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": anchor,
        }
    }))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_anchor(plan_path: Path, payload: dict) -> str:
    """Assemble the short re-anchor message.

    Args:
        plan_path: The active plan file.
        payload: The hook input, used to tell a subagent from a session.

    Returns:
        The text to inject, truncated to the additionalContext cap.
    """
    lines = [f"ACTIVE PLAN: {plan_path}"]

    phase = plan_state.current_phase(plan_path.parent)
    if phase is not None:
        lines.append(f"CURRENT PHASE: {phase}")

    step = plan_state.next_step(plan_path)
    if step is not None:
        lines.append(f"NEXT UNCHECKED STEP: {step}")

    is_subagent = payload.get("hook_event_name") == "SubagentStart"
    lines.append(SUBAGENT_NOTE if is_subagent else SESSION_NOTE)

    return "\n".join(lines)[:MAX_CONTEXT_CHARS]


if __name__ == "__main__":
    main()
