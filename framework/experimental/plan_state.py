"""Shared plan-state resolution for the framework hooks.

Responsibilities:
- Find the active plan for a project, safely.
- Refuse any plan path that resolves outside the project directory.
- Name the per-agent evidence counter, so two subagents never share one.

Every hook in this directory runs on someone's machine on every tool call, so the rules
here are conservative: parse defensively, contain paths, and return None rather than raise.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

# ============================================================================
# CONSTANTS
# ============================================================================

# Tracked location, checked first. `.context/` is gitignored in this repo and in several
# others, so a pointer written there does not survive a fresh clone or reach a new
# Conductor workspace. The tracked path is the one that travels.
POINTER_PATHS = (".docs/plans/ACTIVE", ".context/active-plan")

CONTRACT_NAME = "contract.json"
PLAN_NAME = "PLAN.md"
COUNTER_PREFIX = ".evidence-reads"

# The first unticked checklist item, searched only in the Steps section. The plan template
# also puts unticked boxes under "Open questions", and reporting one of those as the next
# step tells every delegated subagent to go and answer a question meant for Roald.
STEPS_HEADING = re.compile(r"^##+\s+Steps\s*$", re.MULTILINE)
NEXT_HEADING = re.compile(r"^##+\s+", re.MULTILINE)
UNCHECKED_ITEM = re.compile(r"^\s*[-*]\s*\[ \]\s*(.+)$", re.MULTILINE)


# ============================================================================
# PLAN RESOLUTION
# ============================================================================


def read_payload(stream) -> dict:
    """Parse a hook payload from a stream, tolerating an empty or malformed body."""
    raw = stream.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def project_dir(payload: dict) -> Path:
    """Return the session's working directory as an absolute path."""
    cwd = payload.get("cwd")
    return Path(cwd).resolve() if isinstance(cwd, str) and cwd else Path.cwd().resolve()


def active_plan(project: Path) -> Optional[Path]:
    """Find the active PLAN.md for a project.

    The pointer file holds a path. It is repository content, so it is treated as
    untrusted: the resolved plan must sit inside the project directory. Without that
    check, a pointer committed into any repo decides where a background hook creates
    files, including inside the user's home directory.

    Args:
        project: The session's working directory, already resolved.

    Returns:
        The plan file, or None when there is no active plan or the pointer is unusable.
    """
    for relative in POINTER_PATHS:
        pointer = project / relative
        if not pointer.is_file():
            continue
        try:
            target = pointer.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not target:
            continue

        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = project / candidate
        try:
            candidate = candidate.resolve()
        except OSError:
            continue

        if project not in candidate.parents:
            return None
        if candidate.is_file():
            return candidate
    return None


def counter_path(plan_dir: Path, payload: dict) -> Path:
    """Return the evidence counter for this agent.

    One counter per agent, not one per plan. A shared counter lets a subagent's permitted
    write reset the gate against a sibling that read its evidence a moment earlier, and
    lets two concurrent increments overwrite each other.
    """
    agent_id = payload.get("agent_id")
    suffix = f"-{agent_id}" if isinstance(agent_id, str) and agent_id else ""
    return plan_dir / f"{COUNTER_PREFIX}{suffix}"


def read_counter(counter: Path) -> int:
    """Return the evidence count, treating anything unreadable as zero."""
    if not counter.is_file():
        return 0
    try:
        return int(counter.read_text(encoding="utf-8").strip() or 0)
    except (ValueError, OSError):
        return 0


# ============================================================================
# PLAN CONTENT
# ============================================================================


def current_phase(plan_dir: Path) -> Optional[str]:
    """Return the first phase in the contract that is not yet passing."""
    contract = plan_dir / CONTRACT_NAME
    if not contract.is_file():
        return None
    try:
        data = json.loads(contract.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None

    for name, state in data.items():
        if isinstance(state, dict) and not state.get("passes"):
            return str(name)
    return "all phases passing"


def next_step(plan_path: Path) -> Optional[str]:
    """Return the first unticked item in the plan's Steps section.

    Args:
        plan_path: The plan file.

    Returns:
        The step text, or None when the plan has no Steps section or none are unticked.
    """
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return None

    heading = STEPS_HEADING.search(text)
    if heading is None:
        return None

    body_start = heading.end()
    following = NEXT_HEADING.search(text, body_start)
    body = text[body_start:following.start()] if following else text[body_start:]

    match = UNCHECKED_ITEM.search(body)
    return match.group(1).strip() if match else None
