#!/usr/bin/env python3
"""Consolidate pulse update logs into mind.md.

Reads logs/pulse_updates.jsonl, merges noteworthy events into mind.md's
Recent Events section, and archives processed entries.

Run periodically (every 6h) or on demand:
    python3 scripts/consolidate.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
MIND_PATH = BASE_DIR / "mind.md"
UPDATES_PATH = BASE_DIR / "logs" / "pulse_updates.jsonl"
ARCHIVE_PATH = BASE_DIR / "logs" / "pulse_updates.archive.jsonl"

MAX_RECENT_EVENTS = 20


def load_updates() -> list[dict]:
    if not UPDATES_PATH.exists():
        return []
    entries = []
    for line in UPDATES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def archive_updates(entries: list[dict]) -> None:
    """Move processed entries to archive and clear the main log."""
    if not entries:
        return
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_PATH, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # Truncate the active log
    UPDATES_PATH.write_text("", encoding="utf-8")


def build_event_lines(entries: list[dict]) -> list[str]:
    """Build Recent Events lines from JSONL entries (only noteworthy ones)."""
    events = []
    for entry in entries:
        ts = entry.get("timestamp", "")[:16]
        entry_type = entry.get("type", "unknown")

        if entry_type == "check":
            new_items = entry.get("new_items", 0)
            if new_items == 0:
                continue  # Skip "nothing new" checks — no noise
            sources = entry.get("sources", {})
            parts = []
            for src, data in sources.items():
                count = data.get("count", data.get("new", data.get("unprocessed", 0)))
                if count and count > 0:
                    parts.append(f"{src}: {count} new")
            src_str = ", ".join(parts) if parts else "items detected"
            events.append(f"- {ts} — Check pulse: {src_str}.")

        elif entry_type == "deep":
            events.append(f"- {ts} — Deep pulse completed.")

        elif entry_type == "reactive":
            preview = entry.get("message_preview", "user message")
            events.append(f"- {ts} — Reactive pulse: {preview}")

        elif entry_type == "consolidation":
            events.append(f"- {ts} — Knowledge consolidation completed.")

    return events


def update_mind_recent_events(new_lines: list[str]) -> None:
    """Prepend new event lines to the Recent Events section in mind.md."""
    if not MIND_PATH.exists() or not new_lines:
        return

    text = MIND_PATH.read_text(encoding="utf-8")

    pattern = r"(## Recent Events\n)(.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return

    existing = match.group(2).strip()
    if existing == "_No events yet._":
        existing = ""

    # Combine: new events first (most recent), then existing
    all_lines = new_lines + ([existing] if existing else [])
    # Limit total entries
    combined = "\n".join(all_lines[:MAX_RECENT_EVENTS])

    updated = text[: match.start(2)] + combined + "\n" + text[match.end(2) :]
    MIND_PATH.write_text(updated, encoding="utf-8")


def main() -> int:
    entries = load_updates()
    if not entries:
        print("No updates to consolidate.")
        return 0

    new_lines = build_event_lines(entries)
    if new_lines:
        update_mind_recent_events(new_lines)
        print(f"Consolidated {len(new_lines)} events into mind.md Recent Events")
    else:
        print("All entries were routine checks — nothing to add to mind.md")

    archive_updates(entries)
    print(f"Archived {len(entries)} JSONL entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
