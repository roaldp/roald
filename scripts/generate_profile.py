#!/usr/bin/env python3
"""Generate profile.json from Roald runtime state.

Reads mind.md, config.yaml, knowledge/, and logs/ from the Roald base directory
and produces a profile.json that the dashboard can render.

Usage:
    python3 scripts/generate_profile.py                  # uses current directory
    python3 scripts/generate_profile.py /path/to/roald   # custom base dir
"""

import json
import re
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Workstream definitions — maps workspace IDs to keywords found in mind.md
# ---------------------------------------------------------------------------

WORKSTREAMS = [
    # Populate with your workspace-specific keywords locally.
    # These keywords are used to route tasks from mind.md to workspaces.
    # Example entry:
    # {
    #     "id": "ws-dealflow", "icon": "🔍", "name": "Deal Flow",
    #     "agent": "Deal Flow", "style": "chat",
    #     "keywords": ["company-a", "company-b", "term sheet", "due diligence"],
    #     "subtasks": [
    #         {"id": "st-dd", "name": "Active DD", "detail": "...", "keywords": [...]},
    #     ],
    # },
    {
        "id": "ws-dealflow",
        "icon": "🔍",
        "name": "Deal Flow",
        "agent": "Deal Flow",
        "style": "chat",
        "keywords": ["deal flow", "term sheet", "ic memo", "due diligence", "dd sync", "dd kickoff", "cla"],
        "subtasks": [
            {"id": "st-dd", "name": "Active DD", "detail": "Companies in active due diligence.", "keywords": ["dd sync", "dd kickoff", "ic memo", "cla"]},
            {"id": "st-pipeline", "name": "Pipeline", "detail": "New opportunities and early conversations.", "keywords": ["term sheet", "deal flow"]},
        ],
    },
    {
        "id": "ws-dc",
        "icon": "🖥️",
        "name": "DC & Infrastructure",
        "agent": "Infrastructure",
        "style": "chat",
        "keywords": ["server", "datacenter", "data center", "gpu", "node", "infrastructure"],
        "subtasks": [
            {"id": "st-server-deals", "name": "Server deals", "detail": "Active server and DC infrastructure negotiations.", "keywords": ["server", "datacenter"]},
            {"id": "st-dc-urgent", "name": "Urgent items", "detail": "Blockers and time-sensitive DC items.", "keywords": ["urgent", "blocked"]},
        ],
    },
    {
        "id": "ws-fundops",
        "icon": "💼",
        "name": "Fund Operations",
        "agent": "Fund Ops",
        "style": "chat",
        "keywords": ["spv", "fund", "lp", "quarterly", "ruling", "legal", "buyout", "asset purchase"],
        "subtasks": [
            {"id": "st-spv-legal", "name": "SPV & Legal", "detail": "SPV structures, legal rulings, and fund admin.", "keywords": ["spv", "buyout", "asset purchase", "ruling"]},
            {"id": "st-lp-relations", "name": "LP Relations", "detail": "LP updates, quarterly reports, and investor comms.", "keywords": ["lp", "quarterly"]},
        ],
    },
    {
        "id": "ws-portfolio",
        "icon": "🤝",
        "name": "Portfolio & Relations",
        "agent": "Relations",
        "style": "chat",
        "keywords": ["portfolio", "founder", "sync", "follow up", "follow-up", "nurture"],
        "subtasks": [
            {"id": "st-portfolio-syncs", "name": "Portfolio syncs", "detail": "Upcoming and recent founder check-ins.", "keywords": ["sync", "portfolio"]},
            {"id": "st-partnerships", "name": "Partnerships & outreach", "detail": "Partner follow-ups and ecosystem outreach.", "keywords": ["partner", "outreach"]},
        ],
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_id(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode()).hexdigest()[:8]


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return ""


def tail_file(path: Path, n: int = 50) -> list[str]:
    text = read_file(path)
    if not text.strip():
        return []
    lines = text.strip().splitlines()
    return lines[-n:]


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_sections(text: str) -> dict[str, str]:
    """Split markdown by ## headers into {section_name: content}."""
    sections: dict[str, str] = {}
    current = None
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def parse_bullet_items(text: str) -> list[str]:
    """Extract top-level bullet list items (- or * prefix)."""
    if not text or text.startswith("_No ") or text.startswith("_Add "):
        return []
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            items.append(stripped[2:].strip())
    return items


def parse_source_table(text: str) -> list[dict]:
    """Parse the Source Configuration markdown table."""
    sources = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| Source") or line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 2:
            sources.append({
                "source": parts[0],
                "status": parts[1] if len(parts) > 1 else "unknown",
                "notes": parts[2] if len(parts) > 2 else "",
            })
    return sources


def parse_preferences(text: str) -> dict[str, str]:
    """Extract **Key:** value pairs from Preferences section."""
    prefs = {}
    for match in re.finditer(r"\*\*([^*]+)\*\*:?\s*(.+)", text):
        key = match.group(1).strip()
        value = match.group(2).strip().strip("_").strip()
        if value and not value.startswith("Not set"):
            prefs[key] = value
    return prefs


def parse_knowledge_index(text: str) -> dict[str, list[str]]:
    """Parse knowledge/index.md into {section: [entries]}."""
    sections = parse_sections(text)
    result: dict[str, list[str]] = {}
    for section_name in ("Meetings", "Emails", "Notes", "People"):
        content = sections.get(section_name, "")
        result[section_name] = parse_bullet_items(content)
    return result


def load_config(path: Path) -> dict:
    """Load config.yaml. Uses PyYAML if available, falls back to basic parsing."""
    text = read_file(path)
    if not text.strip():
        return {}
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        config = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line and not line.startswith("-"):
                key, _, value = line.partition(":")
                value = value.strip().strip('"').strip("'")
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                config[key.strip()] = value
        return config


def list_knowledge_files(knowledge_dir: Path, subdir: str) -> list[dict]:
    """List files in a knowledge subdirectory, sorted by date (newest first)."""
    d = knowledge_dir / subdir
    if not d.is_dir():
        return []
    files = []
    for f in sorted(d.glob("*.md"), reverse=True):
        name = f.stem
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)", name)
        if date_match:
            files.append({
                "date": date_match.group(1),
                "slug": date_match.group(2),
                "name": name,
                "path": str(f.relative_to(knowledge_dir.parent)),
            })
        else:
            files.append({"date": "", "slug": name, "name": name, "path": str(f.relative_to(knowledge_dir.parent))})
    return files


# ---------------------------------------------------------------------------
# Profile builder helpers
# ---------------------------------------------------------------------------

def compute_light(feed_entries: list[dict]) -> str:
    for fe in feed_entries:
        if fe["status"] == "urgent":
            return "red"
    for fe in feed_entries:
        if fe["status"] in ("question", "pending"):
            return "yellow"
    return "green"


def compute_subtask_status(feed_entries: list[dict]) -> str:
    statuses = [fe["status"] for fe in feed_entries]
    if "urgent" in statuses:
        return "urgent"
    if "question" in statuses:
        return "question"
    if "pending" in statuses:
        return "pending"
    if "running" in statuses:
        return "running"
    return "done"


DEFAULT_ACTIONS = [
    {"type": "approve", "label": "Approve"},
    {"type": "redirect", "label": "Redirect"},
    {"type": "dismiss", "label": "Dismiss"},
]


def item_matches_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def infer_proposed_action(task_text: str):
    """Derive a proposed action string from a task description."""
    t = task_text.lower()
    if any(w in t for w in ["follow up", "follow-up", "reach out", "email", "send", "respond", "reply"]):
        return f"Draft and queue: {task_text[:80]}"
    if any(w in t for w in ["schedule", "calendar", "set up", "book"]):
        return f"Add to calendar: {task_text[:80]}"
    if any(w in t for w in ["review", "check", "analyze", "read"]):
        return f"Prepare review summary: {task_text[:80]}"
    if any(w in t for w in ["draft", "write", "prepare", "memo"]):
        return f"Draft document: {task_text[:80]}"
    return None


def build_source_status(sources: list[dict]) -> list[dict]:
    """Convert source table entries to SourceStatus objects."""
    status_map = {
        "active": "active",
        "error": "error",
        "failure": "error",
        "pending_discovery": "pending_discovery",
        "pending": "pending_discovery",
    }
    result = []
    for src in sources:
        raw_status = src["status"].lower().replace(" ", "_")
        mapped = status_map.get(raw_status, "pending_discovery")
        result.append({
            "name": src["source"],
            "status": mapped,
            "notes": src.get("notes", "") or None,
        })
    # Strip None notes
    for r in result:
        if not r["notes"]:
            del r["notes"]
    return result


# ---------------------------------------------------------------------------
# Workstream builder
# ---------------------------------------------------------------------------

def build_workstream_workspaces(
    pending_tasks: list[str],
    recent_events: list[str],
    now: str,
) -> list[dict]:
    """Build workstream workspaces by routing tasks/events to workstreams by keyword."""

    # Route each task to workstreams + subtasks
    # A task can match multiple workstreams; we assign to the first match
    # (order in WORKSTREAMS determines priority)
    workstream_tasks: dict[str, dict[str, list[str]]] = {
        ws["id"]: {st["id"]: [] for st in ws["subtasks"]}
        for ws in WORKSTREAMS
    }

    unmatched_tasks: list[str] = []

    for task in pending_tasks:
        matched = False
        for ws_def in WORKSTREAMS:
            if item_matches_keywords(task, ws_def["keywords"]):
                # Route to the matching subtask
                for st_def in ws_def["subtasks"]:
                    if item_matches_keywords(task, st_def["keywords"]):
                        workstream_tasks[ws_def["id"]][st_def["id"]].append(task)
                        matched = True
                        break
                if not matched:
                    # Assign to first subtask of the workspace
                    first_st = ws_def["subtasks"][0]["id"]
                    workstream_tasks[ws_def["id"]][first_st].append(task)
                    matched = True
                break
        if not matched:
            unmatched_tasks.append(task)

    workspaces = []

    for ws_def in WORKSTREAMS:
        subtasks = []
        ws_has_content = False

        for st_def in ws_def["subtasks"]:
            tasks_for_st = workstream_tasks[ws_def["id"]][st_def["id"]]
            feed: list[dict] = []

            for task in tasks_for_st:
                tid = make_id(ws_def["id"], st_def["id"], task)
                is_urgent = any(w in task.lower() for w in ["urgent", "asap", "immediately", "overdue", "!"])
                is_question = any(w in task.lower() for w in ["?", "decide", "should we", "which"])
                status = "urgent" if is_urgent else "question" if is_question else "pending"
                entry: dict = {
                    "id": tid,
                    "type": "escalation" if is_question else "agent_output",
                    "status": status,
                    "title": task,
                    "body": task,
                    "time": now,
                    "actions": DEFAULT_ACTIONS,
                }
                proposed = infer_proposed_action(task)
                if proposed and status == "pending":
                    entry["proposedAction"] = proposed
                feed.append(entry)

            # Add relevant recent events as done entries
            for evt in recent_events:
                if item_matches_keywords(evt, st_def["keywords"]):
                    eid = make_id(ws_def["id"], st_def["id"], "event", evt)
                    feed.append({
                        "id": eid,
                        "type": "agent_output",
                        "status": "done",
                        "title": evt,
                        "body": evt,
                        "time": now,
                        "actions": [],
                    })

            if feed:
                ws_has_content = True
                subtasks.append({
                    "id": st_def["id"],
                    "name": st_def["name"],
                    "detail": st_def["detail"],
                    "status": compute_subtask_status(feed),
                    "light": compute_light(feed),
                    "feed": feed,
                })

        if ws_has_content:
            workspaces.append({
                "id": ws_def["id"],
                "icon": ws_def["icon"],
                "name": ws_def["name"],
                "agent": ws_def["agent"],
                "style": ws_def["style"],
                "subtasks": subtasks,
            })

    return workspaces, unmatched_tasks


# ---------------------------------------------------------------------------
# Email workspace builder
# ---------------------------------------------------------------------------

def build_email_workspace(
    inbox_items: list[str],
    email_files: list[dict],
    now: str,
):
    email_feed = []
    for item in inbox_items:
        eid = make_id("email", item)
        email_feed.append({
            "id": eid,
            "type": "agent_output",
            "status": "pending",
            "title": item,
            "body": item,
            "time": now,
            "actions": DEFAULT_ACTIONS,
            "proposedAction": f"Send response: {item[:60]}",
        })
    for ef in email_files[:5]:
        eid = make_id("email-file", ef["name"])
        email_feed.append({
            "id": eid,
            "type": "agent_output",
            "status": "done",
            "title": f"Email processed: {ef['slug'].replace('-', ' ')}",
            "body": f"Stored in knowledge/emails/{ef['name']}.md on {ef['date']}.",
            "time": ef["date"],
            "actions": [],
        })
    if not email_feed:
        return None
    return {
        "id": "ws-email",
        "icon": "📧",
        "name": "Email",
        "agent": "Email",
        "style": "triage",
        "subtasks": [{
            "id": "st-inbox",
            "name": "Inbox triage",
            "detail": "Emails needing attention or recently processed.",
            "status": compute_subtask_status(email_feed),
            "light": compute_light(email_feed),
            "feed": email_feed,
        }],
    }


# ---------------------------------------------------------------------------
# Main profile builder
# ---------------------------------------------------------------------------

def build_profile(base_dir: Path) -> dict:
    """Build the complete Profile JSON from Roald runtime state."""

    mind_text = read_file(base_dir / "mind.md")
    config = load_config(base_dir / "config.yaml")
    knowledge_text = read_file(base_dir / "knowledge" / "index.md")

    mind = parse_sections(mind_text)
    sources = parse_source_table(mind.get("Source Configuration", ""))
    pending_tasks = parse_bullet_items(mind.get("Pending Tasks", ""))
    recent_events = parse_bullet_items(mind.get("Recent Events", ""))
    inbox_items = parse_bullet_items(mind.get("Inbox Zero Tracker", ""))
    preferences = parse_preferences(mind.get("Preferences", ""))
    active_context = mind.get("Active Context", "").strip()
    last_pulse = mind.get("Last Pulse", "").strip()

    knowledge_dir = base_dir / "knowledge"
    email_files = list_knowledge_files(knowledge_dir, "emails")

    now = datetime.now(timezone.utc).strftime("%H:%M")

    # Identity
    model_name = config.get("claude_model", "sonnet")
    identity = {
        "companionName": "Roald",
        "orgName": preferences.get("Organization", "My Organization"),
        "modelName": f"Claude {model_name.capitalize()}",
    }

    # Source status (top bar dot)
    source_status = build_source_status(sources)

    # Build workstream workspaces
    workspaces, unmatched_tasks = build_workstream_workspaces(pending_tasks, recent_events, now)

    # Email workspace (always first, triage style)
    email_ws = build_email_workspace(inbox_items, email_files, now)
    if email_ws:
        workspaces.insert(0, email_ws)

    # If there are unmatched tasks and no other workspace caught them,
    # append a catch-all tasks workspace
    if unmatched_tasks:
        catch_feed = []
        for task in unmatched_tasks:
            tid = make_id("catchall", task)
            is_urgent = any(w in task.lower() for w in ["urgent", "asap", "immediately", "overdue"])
            is_question = any(w in task.lower() for w in ["?", "decide", "should we"])
            status = "urgent" if is_urgent else "question" if is_question else "pending"
            catch_feed.append({
                "id": tid,
                "type": "escalation" if is_question else "agent_output",
                "status": status,
                "title": task,
                "body": task,
                "time": now,
                "actions": DEFAULT_ACTIONS,
            })
        workspaces.append({
            "id": "ws-tasks",
            "icon": "✅",
            "name": "Tasks",
            "agent": "Tasks",
            "style": "chat",
            "subtasks": [{
                "id": "st-misc",
                "name": "Miscellaneous",
                "detail": f"{len(unmatched_tasks)} tasks not assigned to a specific workstream.",
                "status": compute_subtask_status(catch_feed),
                "light": compute_light(catch_feed),
                "feed": catch_feed,
            }],
        })

    # Welcome workspace if nothing at all
    if not workspaces:
        workspaces.append({
            "id": "ws-welcome",
            "icon": "👋",
            "name": "Getting Started",
            "agent": "Setup",
            "style": "chat",
            "subtasks": [{
                "id": "st-welcome",
                "name": "Roald is setting up",
                "detail": "Run a pulse to start populating the dashboard with real data.",
                "status": "running",
                "light": "yellow",
                "feed": [{
                    "id": "fe-welcome",
                    "type": "agent_output",
                    "status": "running",
                    "title": "Waiting for first pulse — no data yet",
                    "body": "Roald hasn't completed a full pulse yet. Once it runs, this dashboard will show your emails, meetings, tasks, and source status.\n\nTo trigger a pulse manually, send a message to Roald on Slack.",
                    "time": now,
                    "actions": [],
                }],
            }],
        })

    # Agenda
    agenda = []
    if active_context and not active_context.startswith("_No "):
        time_pattern = r"(\d{1,2}:\d{2})\s*[-—:]\s*(.+)"
        for match in re.finditer(time_pattern, active_context):
            agenda.append({
                "time": match.group(1),
                "event": match.group(2).strip(),
                "status": "upcoming",
            })

    if not agenda:
        for evt in recent_events:
            if any(w in evt.lower() for w in ["meeting", "call", "sync", "prep", "calendar"]):
                agenda.append({
                    "time": "",
                    "event": evt[:80],
                    "status": "done",
                })
                if len(agenda) >= 5:
                    break

    if last_pulse and not last_pulse.startswith("_No "):
        pulse_time_match = re.search(r"(\d{2}:\d{2})", last_pulse)
        pulse_time = pulse_time_match.group(1) if pulse_time_match else ""
        agenda.insert(0, {
            "time": pulse_time,
            "event": f"Last pulse: {last_pulse}",
            "status": "done",
        })

    if not agenda:
        agenda.append({
            "time": now,
            "event": "No calendar data — Roald reads from active context",
            "status": "upcoming",
        })

    profile: dict = {
        "identity": identity,
        "workspaces": workspaces,
        "agenda": agenda,
        "inputPlaceholder": "Ask Roald anything, give instructions, or override agent behavior...",
    }
    if source_status:
        profile["sourceStatus"] = source_status

    return profile


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        base_dir = Path(sys.argv[1]).expanduser().resolve()
    else:
        base_dir = Path.cwd()

    if not base_dir.is_dir():
        print(f"Error: {base_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    profile = build_profile(base_dir)
    output_path = base_dir / "profile.json"
    output_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ws_count = len(profile["workspaces"])
    feed_count = sum(
        len(st["feed"])
        for ws in profile["workspaces"]
        for st in ws["subtasks"]
    )
    src_count = len(profile.get("sourceStatus", []))
    print(f"Generated {output_path}")
    print(f"  {ws_count} workspaces, {feed_count} feed entries, {len(profile['agenda'])} agenda items, {src_count} sources")


if __name__ == "__main__":
    main()
