#!/usr/bin/env bash
set -euo pipefail

# Setup script for Local Claude Companion
# Requires: Python 3, pip, and Claude Code (claude CLI)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; exit 1; }

DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 1. Check Python 3 ────────────────────────────────────────────
info "Checking Python 3..."
if ! command -v python3 &>/dev/null; then
  error "python3 not found. Please install Python 3.9+ first."
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Found Python $PY_VERSION"

# ── 2. Check Claude Code CLI ─────────────────────────────────────
info "Checking Claude Code CLI..."
if ! command -v claude &>/dev/null; then
  error "Claude Code CLI not found. Install it first: https://docs.anthropic.com/en/docs/claude-code"
fi
info "Found claude CLI at $(command -v claude)"

# ── 3. Install PyYAML ────────────────────────────────────────────
info "Installing Python dependencies..."
python3 -m pip install --quiet PyYAML
info "PyYAML installed."

# ── 4. Create config.yaml from template ──────────────────────────
if [ -f "$DIR/config.yaml" ]; then
  warn "config.yaml already exists — skipping (delete it to regenerate)."
else
  cp "$DIR/config.template.yaml" "$DIR/config.yaml"
  info "Created config.yaml from template."
fi

# ── 5. Prompt for required Slack settings ─────────────────────────
echo ""
echo "To find your Slack IDs: DM yourself in Slack, then copy the URL."
echo "The URL looks like: .../messages/D0XXXXXXX/ (that's the DM channel ID)."
echo "Your user ID is in your Slack profile > … > Copy member ID."
echo ""

read -rp "Slack User ID (leave blank to skip): " SLACK_USER_ID
read -rp "Slack DM Channel ID (leave blank to skip): " SLACK_DM_ID
read -rp "Timezone (e.g. America/New_York) [UTC]: " TIMEZONE
TIMEZONE="${TIMEZONE:-UTC}"

if [ -n "$SLACK_USER_ID" ]; then
  sed -i "s/^slack_user_id: .*/slack_user_id: \"$SLACK_USER_ID\"/" "$DIR/config.yaml"
fi
if [ -n "$SLACK_DM_ID" ]; then
  sed -i "s/^slack_dm_channel_id: .*/slack_dm_channel_id: \"$SLACK_DM_ID\"/" "$DIR/config.yaml"
fi
sed -i "s/^timezone: .*/timezone: \"$TIMEZONE\"/" "$DIR/config.yaml"

info "config.yaml updated."

# ── 6. Create runtime directories ─────────────────────────────────
mkdir -p "$DIR/logs" "$DIR/knowledge/meetings" "$DIR/knowledge/emails" "$DIR/knowledge/notes"
info "Runtime directories created."

# ── 7. Summary ────────────────────────────────────────────────────
echo ""
info "Setup complete! To start the companion, run:"
echo ""
echo "    python3 pulse.py"
echo ""
echo "  Options:"
echo "    python3 pulse.py --once-full       Run a single full pulse"
echo "    python3 pulse.py --once-reactive    Run a single reactive pulse"
echo ""
warn "Review config.yaml to enable/disable data sources (Slack, Gmail, Fireflies, Calendar)."
