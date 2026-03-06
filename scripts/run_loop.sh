#!/usr/bin/env bash
# Run pulse.py in a restart loop. Handles:
# - Exit code 42: restart with new code (auto-update)
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

  if [ $rc -ne 42 ]; then
    # Not an update restart — check for startup crash
    elapsed=$(( $(date +%s) - start_time ))
    if [ "$elapsed" -lt 10 ] && [ -f "$LAST_GOOD" ]; then
      last_good=$(cat "$LAST_GOOD")
      echo "[ROLLBACK] Startup crash detected (exited in ${elapsed}s). Rolling back to $last_good" | tee -a "$LOG_PATH"
      git -C "$BASE_DIR" checkout "$last_good" 2>/dev/null
      # Try once more with rolled-back code
      python3 -u "$BASE_DIR/pulse.py"
      rc=$?
      if [ $rc -ne 42 ]; then
        echo "[ERROR] Rollback did not help. Stopping." | tee -a "$LOG_PATH"
        break
      fi
    else
      break
    fi
  fi

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
    break
  fi

  echo "[UPDATE] Restarting with new code..."
  sleep 2
done
