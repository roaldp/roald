#!/usr/bin/env python3
"""Snapshot available MCP tools/servers and compare with previous inventory."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CONTEXT_DIR = Path(__file__).parent.parent / ".context"
INVENTORY_PATH = CONTEXT_DIR / "mcp_tools.json"


def get_mcp_servers() -> list[str]:
    """Run `claude mcp list` and parse server names from output."""
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        servers = []
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line:
                servers.append(line)
        return sorted(servers)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def load_previous() -> dict:
    if INVENTORY_PATH.exists():
        try:
            return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_inventory(data: dict) -> None:
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    current_servers = get_mcp_servers()
    previous = load_previous()
    previous_servers = previous.get("servers", [])

    added = sorted(set(current_servers) - set(previous_servers))
    removed = sorted(set(previous_servers) - set(current_servers))

    inventory = {
        "timestamp": datetime.now().isoformat(),
        "servers": current_servers,
        "changes": {
            "added": added,
            "removed": removed,
        },
    }
    save_inventory(inventory)

    print(f"MCP servers: {len(current_servers)} detected")
    if current_servers:
        for s in current_servers:
            print(f"  - {s}")
    else:
        print("  (none found — claude mcp list returned no output)")
    if added:
        print(f"Added since last scan: {', '.join(added)}")
    if removed:
        print(f"Removed since last scan: {', '.join(removed)}")
    if not added and not removed and previous_servers:
        print("No changes since last scan.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
