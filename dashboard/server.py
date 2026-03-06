#!/usr/bin/env python3
"""Dashboard server for the Local Claude Companion.

Run:  python3 dashboard/server.py
Open: http://localhost:7888
"""

import json
import os
import re
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
MIND_PATH = BASE_DIR / "mind.md"
CONFIG_PATH = BASE_DIR / "config.yaml"
CONFIG_TEMPLATE_PATH = BASE_DIR / "config.template.yaml"
LOG_PATH = BASE_DIR / "logs" / "pulse.log"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
KNOWLEDGE_INDEX_PATH = KNOWLEDGE_DIR / "index.md"
LOCK_PATH = BASE_DIR / "logs" / ".pulse_lock"
PID_PATH = BASE_DIR / "logs" / "pulse.pid"

PORT = int(os.environ.get("DASHBOARD_PORT", 7888))


def is_companion_running() -> bool:
    if not PID_PATH.exists():
        return False
    try:
        pid = int(PID_PATH.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        return False


def read_mind() -> dict:
    """Parse mind.md into structured sections."""
    if not MIND_PATH.exists():
        return {"exists": False, "raw": "", "sections": {}}
    raw = MIND_PATH.read_text(encoding="utf-8")
    sections = {}
    current_section = None
    current_lines = []

    for line in raw.splitlines():
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        elif current_section:
            current_lines.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    return {"exists": True, "raw": raw, "sections": sections}


def parse_source_config(text: str) -> list:
    """Parse the source configuration table from mind.md."""
    sources = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and not line.startswith("| Source") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                sources.append({
                    "name": parts[0],
                    "status": parts[1],
                    "notes": parts[2],
                })
    return sources


def parse_pending_tasks(text: str) -> list:
    """Parse pending tasks from mind.md section."""
    if "_No tasks yet._" in text or not text.strip():
        return []
    tasks = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            done = line.startswith("- [x]") or line.startswith("- [X]")
            label = re.sub(r"^- \[.\]\s*", "", line)
            if label == line:
                label = line[2:]
            tasks.append({"text": label, "done": done})
    return tasks


def parse_recent_events(text: str) -> list:
    """Parse recent events from mind.md section."""
    if "_No events yet._" in text or not text.strip():
        return []
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            events.append(line[2:])
    return events


def read_config() -> dict:
    path = CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_TEMPLATE_PATH
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_log_tail(lines: int = 100) -> list:
    if not LOG_PATH.exists():
        return []
    all_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    return all_lines[-lines:]


def parse_log_entry(line: str) -> dict:
    """Parse a log line into structured data."""
    m = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*(.*)", line)
    if m:
        return {"timestamp": m.group(1), "message": m.group(2)}
    return {"timestamp": "", "message": line}


def read_knowledge_index() -> list:
    if not KNOWLEDGE_INDEX_PATH.exists():
        return []
    raw = KNOWLEDGE_INDEX_PATH.read_text(encoding="utf-8")
    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("- "):
            entries.append(line[2:])
    return entries


def list_knowledge_files() -> dict:
    result = {"meetings": [], "emails": [], "notes": []}
    for category in result:
        cat_dir = KNOWLEDGE_DIR / category
        if cat_dir.exists():
            for f in sorted(cat_dir.iterdir(), reverse=True):
                if f.suffix == ".md":
                    stat = f.stat()
                    result[category].append({
                        "name": f.name,
                        "path": str(f.relative_to(BASE_DIR)),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
    return result


def read_knowledge_file(rel_path: str) -> str:
    """Read a knowledge file by relative path (sanitized)."""
    safe = Path(rel_path).name
    for category in ("meetings", "emails", "notes"):
        fp = KNOWLEDGE_DIR / category / safe
        if fp.exists():
            return fp.read_text(encoding="utf-8")
    return ""


def compute_pulse_stats() -> dict:
    """Extract stats from log file."""
    if not LOG_PATH.exists():
        return {"total_pulses": 0, "last_pulse": None, "tool_calls": 0, "errors": 0}
    text = LOG_PATH.read_text(encoding="utf-8")
    full_pulses = len(re.findall(r"Full pulse complete", text))
    reactive_pulses = len(re.findall(r"Reactive pulse complete", text))
    tool_starts = len(re.findall(r"TOOL START:", text))
    errors = len(re.findall(r"error", text, re.IGNORECASE))
    slack_out = len(re.findall(r"SLACK OUTBOUND END:.*status=OK", text))

    last_pulse = None
    for m in re.finditer(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*pulse complete", text, re.IGNORECASE):
        last_pulse = m.group(1)

    return {
        "full_pulses": full_pulses,
        "reactive_pulses": reactive_pulses,
        "total_pulses": full_pulses + reactive_pulses,
        "tool_calls": tool_starts,
        "errors": errors,
        "slack_messages_sent": slack_out,
        "last_pulse": last_pulse,
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves static files and JSON API endpoints."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/"):
            self.handle_api(path, parse_qs(parsed.query))
            return

        # Serve static files
        if path == "" or path == "/":
            file_path = STATIC_DIR / "index.html"
        else:
            file_path = STATIC_DIR / path.lstrip("/")

        if file_path.exists() and file_path.is_file():
            self.send_static(file_path)
        else:
            self.send_error(404)

    def handle_api(self, path: str, params: dict):
        try:
            data = self.route_api(path, params)
            self.send_json(data)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def route_api(self, path: str, params: dict) -> dict:
        if path == "/api/status":
            mind = read_mind()
            config = read_config()
            stats = compute_pulse_stats()
            sources = []
            if mind["exists"] and "Source Configuration" in mind["sections"]:
                sources = parse_source_config(mind["sections"]["Source Configuration"])

            tasks = []
            if mind["exists"] and "Pending Tasks" in mind["sections"]:
                tasks = parse_pending_tasks(mind["sections"]["Pending Tasks"])

            events = []
            if mind["exists"] and "Recent Events" in mind["sections"]:
                events = parse_recent_events(mind["sections"]["Recent Events"])

            active_context = ""
            if mind["exists"] and "Active Context" in mind["sections"]:
                active_context = mind["sections"]["Active Context"]

            inbox = ""
            if mind["exists"] and "Inbox Zero Tracker" in mind["sections"]:
                inbox = mind["sections"]["Inbox Zero Tracker"]

            last_pulse = ""
            if mind["exists"] and "Last Pulse" in mind["sections"]:
                last_pulse = mind["sections"]["Last Pulse"]

            preferences = ""
            if mind["exists"] and "Preferences" in mind["sections"]:
                preferences = mind["sections"]["Preferences"]

            next_instructions = ""
            if mind["exists"] and "Next Pulse Instructions" in mind["sections"]:
                next_instructions = mind["sections"]["Next Pulse Instructions"]

            return {
                "running": is_companion_running(),
                "locked": LOCK_PATH.exists(),
                "mind_exists": mind["exists"],
                "last_pulse": last_pulse,
                "active_context": active_context,
                "sources": sources,
                "tasks": tasks,
                "events": events,
                "inbox": inbox,
                "preferences": preferences,
                "next_instructions": next_instructions,
                "stats": stats,
                "config": {
                    "timezone": config.get("timezone", "UTC"),
                    "full_pulse_interval_minutes": config.get("full_pulse_interval_minutes", 30),
                    "slack_poll_interval_seconds": config.get("slack_poll_interval_seconds", 1),
                    "claude_model": config.get("claude_model", ""),
                    "sources": config.get("sources", {}),
                    "slack_user_id_set": bool(str(config.get("slack_user_id", "")).strip()),
                    "slack_channel_id_set": bool(str(config.get("slack_channel_id", "")).strip()),
                },
            }

        elif path == "/api/logs":
            n = int(params.get("lines", [100])[0])
            raw_lines = read_log_tail(n)
            entries = [parse_log_entry(l) for l in raw_lines]
            return {"entries": entries}

        elif path == "/api/knowledge":
            return {
                "index": read_knowledge_index(),
                "files": list_knowledge_files(),
            }

        elif path == "/api/knowledge/file":
            rel = params.get("path", [""])[0]
            return {"content": read_knowledge_file(rel)}

        elif path == "/api/mind/raw":
            mind = read_mind()
            return {"content": mind.get("raw", "")}

        else:
            return {"error": "Unknown endpoint"}

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, file_path: Path):
        ext = file_path.suffix.lower()
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }
        ct = content_types.get(ext, "application/octet-stream")
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress default access logs for cleaner output
        pass


def main():
    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"Dashboard running at http://localhost:{PORT}")
    print(f"Monitoring companion at: {BASE_DIR}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
