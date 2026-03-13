#!/usr/bin/env python3
"""Append a structured update to the pulse updates JSONL log.

Usage:
    python3 append_update.py '{"type": "check", "new_items": 0}'

Or import append_update() directly from pulse.py.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

UPDATES_PATH = Path(__file__).parent.parent / "logs" / "pulse_updates.jsonl"


def append_update(update: dict) -> None:
    """Append a timestamped update to the JSONL log."""
    UPDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    update["timestamp"] = datetime.now().isoformat()
    with open(UPDATES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(update, ensure_ascii=False) + "\n")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: append_update.py '<json>'")
        return 1
    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return 1
    append_update(data)
    print(f"Appended update: {data.get('type', 'unknown')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
