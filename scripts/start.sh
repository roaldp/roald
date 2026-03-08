#!/usr/bin/env bash
# Start the companion as a persistent background service using launchd (macOS).
# The service survives screen lock, sleep/wake, and restarts automatically on boot.
# Falls back to a background process on non-macOS systems.

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_PATH="$BASE_DIR/logs/pulse.log"
PID_PATH="$BASE_DIR/logs/pulse.pid"
RUN_LOOP="$BASE_DIR/scripts/run_loop.sh"
PLIST_LABEL="com.local.claude-companion"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

mkdir -p "$BASE_DIR/logs"

# ── Stop command ──
if [[ "${1:-}" == "stop" ]]; then
  if [[ -f "$PLIST_PATH" ]]; then
    launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
    printf 'Companion stopped.\n'
  elif [[ -f "$PID_PATH" ]]; then
    kill "$(cat "$PID_PATH")" 2>/dev/null || true
    rm -f "$PID_PATH"
    printf 'Companion stopped.\n'
  else
    printf 'Companion is not running.\n'
  fi
  exit 0
fi

# ── Check if already running via launchd ──
if [[ -f "$PLIST_PATH" ]]; then
  if launchctl print "gui/$(id -u)/${PLIST_LABEL}" >/dev/null 2>&1; then
    printf 'Companion is already running (managed by launchd).\n'
    printf 'It will restart automatically after reboots and sleep/wake.\n'
    printf 'Log: tail -f %s\n' "$LOG_PATH"
    printf 'To stop: bash %s/scripts/start.sh stop\n' "$BASE_DIR"
    exit 0
  fi
fi

# ── Check if already running via PID ──
if [[ -f "$PID_PATH" ]]; then
  existing_pid="$(cat "$PID_PATH")"
  if kill -0 "$existing_pid" 2>/dev/null; then
    printf 'Companion is already running (PID %s).\n' "$existing_pid"
    printf 'Log: %s\n' "$LOG_PATH"
    exit 0
  else
    rm -f "$PID_PATH"
  fi
fi

# ── Option 1: launchd (macOS) — persistent across reboots, sleep, screen lock ──
if [[ "$(uname)" == "Darwin" ]]; then
  mkdir -p "$(dirname "$PLIST_PATH")"

  cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${RUN_LOOP}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${BASE_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>${LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_PATH}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:${HOME}/.local/bin</string>
    </dict>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
PLIST

  # Load the service
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

  printf 'Companion started as a background service.\n'
  printf 'It will keep running when you lock your screen and restart automatically after reboots.\n'
  printf 'Watch for a Slack DM in the next few minutes.\n'
  printf '\nLog: tail -f %s\n' "$LOG_PATH"
  printf 'Stop: bash %s/scripts/start.sh stop\n' "$BASE_DIR"
  exit 0
fi

# ── Option 2: Background process with nohup (Linux fallback) ──
nohup bash -c 'trap "kill %1 2>/dev/null; exit" TERM INT; bash "'"$RUN_LOOP"'" >> "'"$LOG_PATH"'" 2>&1' &
bg_pid=$!
echo "$bg_pid" > "$PID_PATH"
printf 'Companion started in background (PID %s).\n' "$bg_pid"
printf 'Watch for a Slack DM in the next few minutes.\n'
printf 'Log: tail -f %s\n' "$LOG_PATH"
