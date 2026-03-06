#!/usr/bin/env bash
# Launch the Roald Companion Dashboard.
# Usage: ./scripts/dashboard.sh [port]
#
# Opens http://localhost:7888 (or custom port) in your browser.

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-7888}"

export DASHBOARD_PORT="$PORT"

echo "Starting Roald Dashboard on http://localhost:$PORT"
echo "Press Ctrl+C to stop."
echo ""

# Try to open browser (best effort)
if command -v open >/dev/null 2>&1; then
  (sleep 1 && open "http://localhost:$PORT") &
elif command -v xdg-open >/dev/null 2>&1; then
  (sleep 1 && xdg-open "http://localhost:$PORT") &
fi

exec python3 "$BASE_DIR/dashboard/server.py"
