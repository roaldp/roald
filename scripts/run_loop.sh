#!/usr/bin/env bash
# Run pulse.py in a restart loop. Handles:
# - Exit code 42: restart with new code (auto-update)
# - Exit code 0: clean shutdown — stop the loop and exit 0
# - Rapid crash detection: rollback to last known good commit
# - Restart counter: break after 3 restarts in 60 seconds

set -uo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_PATH="$BASE_DIR/logs/pulse.log"
LAST_GOOD="$BASE_DIR/logs/.last_good_commit"

restart_count=0
last_restart_time=0

while true; do
  start_time=$(date +%s)
  python3 -u "$BASE_DIR/pulse.py"
  rc=$?

  # Clean shutdown (exit 0) — stop the loop, don't let launchd restart
  if [ $rc -eq 0 ]; then
    echo "[INFO] Pulse exited cleanly. Stopping." | tee -a "$LOG_PATH"
    exit 0
  fi

  # Update restart (exit 42) — restart immediately with new code
  if [ $rc -eq 42 ]; then
    # Restart counter: prevent infinite loop
    now=$(date +%s)
    if [ $(( now - last_restart_time )) -lt 60 ]; then
      restart_count=$(( restart_count + 1 ))
    else
      restart_count=1
    fi
    last_restart_time=$now

    if [ "$restart_count" -ge 3 ]; then
      echo "[ERROR] Too many restarts in 60s. Stopping." | tee -a "$LOG_PATH"
      exit 1
    fi

    echo "[UPDATE] Restarting with new code..." | tee -a "$LOG_PATH"
    sleep 2
    continue
  fi

  # Non-zero, non-42 exit — check for startup crash
  elapsed=$(( $(date +%s) - start_time ))
  if [ "$elapsed" -lt 10 ] && [ -f "$LAST_GOOD" ]; then
    last_good=$(cat "$LAST_GOOD")
    echo "[ROLLBACK] Startup crash detected (exited in ${elapsed}s with code $rc). Rolling back to $last_good" | tee -a "$LOG_PATH"
    git -C "$BASE_DIR" checkout "$last_good" 2>/dev/null
    # Try once more with rolled-back code
    python3 -u "$BASE_DIR/pulse.py"
    rc2=$?
    if [ $rc2 -eq 0 ]; then
      echo "[INFO] Pulse exited cleanly after rollback. Stopping." | tee -a "$LOG_PATH"
      exit 0
    elif [ $rc2 -eq 42 ]; then
      echo "[UPDATE] Restarting with new code after rollback..." | tee -a "$LOG_PATH"
      sleep 2
      continue
    else
      echo "[ERROR] Rollback did not help (exit code $rc2). Stopping." | tee -a "$LOG_PATH"
      exit 1
    fi
  fi

  # Unexpected exit after running for >10 seconds — exit non-zero so launchd can restart
  echo "[ERROR] Pulse exited with code $rc after ${elapsed}s. Stopping loop." | tee -a "$LOG_PATH"
  exit 1
done
