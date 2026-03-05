#!/usr/bin/env bash
# Start the companion. Tries to open a visible Terminal window (macOS),
# falls back to a background process logging to logs/pulse.log.

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_PATH="$BASE_DIR/logs/pulse.log"
PID_PATH="$BASE_DIR/logs/pulse.pid"

mkdir -p "$BASE_DIR/logs"

# Check if already running
if [[ -f "$PID_PATH" ]]; then
  existing_pid="$(cat "$PID_PATH")"
  if kill -0 "$existing_pid" 2>/dev/null; then
    printf '[OK] Companion is already running (PID %s)\n' "$existing_pid"
    printf 'Log: %s\n' "$LOG_PATH"
    exit 0
  else
    rm -f "$PID_PATH"
  fi
fi

# Option 1: Open a new macOS Terminal window (visible, stays open)
if command -v osascript >/dev/null 2>&1; then
  osascript - "$BASE_DIR" <<'APPLESCRIPT' 2>/dev/null && {
on run argv
  set projectDir to item 1 of argv
  tell application "Terminal"
    do script "cd " & quoted form of projectDir & " && python3 -u pulse.py"
    activate
  end tell
end run
APPLESCRIPT
    printf '[OK] Companion started in a new Terminal window.\n'
    printf 'Watch it there, or tail the log: tail -f %s\n' "$LOG_PATH"
    exit 0
  }
fi

# Option 2: Background process with nohup, output to log file
nohup python3 -u "$BASE_DIR/pulse.py" >> "$LOG_PATH" 2>&1 &
bg_pid=$!
echo "$bg_pid" > "$PID_PATH"
printf '[OK] Companion started in background (PID %s)\n' "$bg_pid"
printf 'Tail the log to watch it: tail -f %s\n' "$LOG_PATH"
