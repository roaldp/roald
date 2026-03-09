#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_TEMPLATE="$BASE_DIR/config.template.yaml"
CONFIG_FILE="$BASE_DIR/config.yaml"

BLOCKERS=0
ACTIONS=0
WARNINGS=0
CONFIG_HELPERS_READY=1

ok() {
  printf '[OK] %s\n' "$1"
}

action_needed() {
  ACTIONS=$((ACTIONS + 1))
  printf '[ACTION NEEDED] %s\n' "$1"
}

blocked() {
  BLOCKERS=$((BLOCKERS + 1))
  printf '[BLOCKED] %s\n' "$1"
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf '[WARN] %s\n' "$1"
}

exit_blocked_setup() {
  printf '\nSummary: %d blocked, %d action needed, %d warnings\n' "$BLOCKERS" "$ACTIONS" "$WARNINGS"
  printf 'Setup cannot continue until blocked items are fixed.\n'
  exit 2
}

set_config_value() {
  local key="$1"
  local value="$2"
  python3 - "$CONFIG_FILE" "$key" "$value" <<'PY'
import sys
import yaml

config_path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
with open(config_path, encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

data[key] = value

with open(config_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, sort_keys=False)
PY
}

get_config_value() {
  local key="$1"
  python3 - "$CONFIG_FILE" "$key" <<'PY'
import sys
import yaml

config_path, key = sys.argv[1], sys.argv[2]
with open(config_path, encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
print(str(data.get(key, "")))
PY
}

is_valid_slack_channel_id() {
  local value="${1:-}"
  [[ "$value" =~ ^[DCG][A-Z0-9]+$ ]]
}

normalize_slack_channel_id() {
  local current_channel_id
  current_channel_id="$(get_config_value slack_channel_id)"

  if [[ -z "${current_channel_id// }" ]]; then
    return 1
  fi

  if is_valid_slack_channel_id "$current_channel_id"; then
    return 0
  fi

  warn "config.yaml: slack_channel_id '$current_channel_id' is invalid for polling; clearing it until a real D..., C..., or G... ID is resolved."
  set_config_value slack_channel_id ""
  return 1
}

printf 'Local Claude Companion setup\n'
printf 'Project: %s\n\n' "$BASE_DIR"

if command -v claude >/dev/null 2>&1; then
  ok "Claude CLI found: $(command -v claude)"
else
  blocked "Claude CLI not found. Install Claude Code CLI and ensure 'claude' is on PATH."
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
  then
    ok "Python version is >= 3.9"
  else
    blocked "Python 3.9+ is required."
    CONFIG_HELPERS_READY=0
  fi
else
  blocked "python3 not found."
  CONFIG_HELPERS_READY=0
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 - <<'PY' >/dev/null 2>&1
import yaml
PY
  then
    ok "PyYAML installed"
  else
    blocked "PyYAML missing. Run: python3 -m pip install pyyaml"
    CONFIG_HELPERS_READY=0
  fi
fi

if [[ ! -f "$CONFIG_TEMPLATE" ]]; then
  blocked "Missing config template: $CONFIG_TEMPLATE"
else
  ok "Found config template"
fi

if [[ "$CONFIG_HELPERS_READY" -ne 1 ]]; then
  exit_blocked_setup
fi

if [[ ! -f "$CONFIG_TEMPLATE" && ! -f "$CONFIG_FILE" ]]; then
  exit_blocked_setup
fi

if [[ -f "$CONFIG_FILE" ]]; then
  ok "config.yaml already exists"
else
  cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
  ok "Created config.yaml from template"
fi

try_slack_resolve() {
  local current_uid
  current_uid="$(get_config_value slack_user_id)"
  if [[ -n "${current_uid// }" ]]; then
    return 0  # already set
  fi
  if ! command -v claude >/dev/null 2>&1; then
    return 1
  fi
  printf 'Attempting to auto-resolve Slack identity...\n'
  local result
  result="$(claude -p "Use slack_read_user_profile with no arguments to get the current user's profile. Return ONLY a JSON object with exactly these fields: user_id (the Slack U... ID), display_name. No other text, no markdown." \
    --allowedTools "mcp__claude_ai_Slack__slack_read_user_profile" \
    --output-format json 2>/dev/null || true)"
  if [[ -z "${result// }" ]]; then
    return 1
  fi
  local resolved_id
  resolved_id="$(printf '%s' "$result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list): data = data[-1]
    uid = data.get('user_id','') or data.get('result','')
    # try to extract U... from result string
    import re
    if not uid.startswith('U'):
        m = re.search(r'U[A-Z0-9]{6,}', str(data))
        if m: uid = m.group()
    print(uid.strip())
except Exception:
    pass
" 2>/dev/null || true)"
  local display_name
  display_name="$(printf '%s' "$result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list): data = data[-1]
    print(data.get('display_name','') or data.get('real_name',''))
except Exception:
    pass
" 2>/dev/null || true)"
  if [[ -n "${resolved_id// }" ]] && [[ "$resolved_id" == U* ]]; then
    set_config_value slack_user_id "$resolved_id"
    ok "Auto-resolved slack_user_id: $resolved_id${display_name:+ ($display_name)}"
    return 0
  fi
  return 1
}

try_slack_channel_resolve() {
  local current_channel_id
  current_channel_id="$(get_config_value slack_channel_id)"
  if is_valid_slack_channel_id "$current_channel_id"; then
    return 0
  fi
  if [[ -n "${current_channel_id// }" ]]; then
    warn "config.yaml: slack_channel_id '$current_channel_id' is invalid for polling; treating it as unresolved."
    set_config_value slack_channel_id ""
  fi

  local current_uid
  current_uid="$(get_config_value slack_user_id)"
  if [[ -z "${current_uid// }" ]]; then
    return 1
  fi
  if ! command -v claude >/dev/null 2>&1; then
    return 1
  fi

  printf 'Attempting to auto-resolve Slack self-DM channel...\n'
  local result
  result="$(claude -p "Use slack_send_message to send this exact message to Slack user ID ${current_uid}: Companion setup: resolving self-DM channel ID. Then return ONLY a JSON object with exactly this field: channel_id. The value must be the real Slack conversation ID used for the send (D..., C..., or G...). No markdown, no extra text." \
    --allowedTools "mcp__claude_ai_Slack__slack_send_message" \
    --output-format json 2>/dev/null || true)"
  if [[ -z "${result// }" ]]; then
    return 1
  fi

  local resolved_channel_id
  resolved_channel_id="$(printf '%s' "$result" | python3 -c "
import json
import re
import sys

pattern = re.compile(r'^[DCG][A-Z0-9]+$')

def walk(value):
    if isinstance(value, dict):
        channel_id = value.get('channel_id')
        if isinstance(channel_id, str):
            channel_id = channel_id.strip()
            if pattern.match(channel_id):
                return channel_id
        for nested in value.values():
            found = walk(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in reversed(value):
            found = walk(nested)
            if found:
                return found
    elif isinstance(value, str):
        match = re.search(r'\\b([DCG][A-Z0-9]{6,})\\b', value)
        if match:
            return match.group(1)
    return ''

raw = sys.stdin.read()
found = ''
try:
    found = walk(json.loads(raw))
except Exception:
    match = re.search(r'\\b([DCG][A-Z0-9]{6,})\\b', raw)
    if match:
        found = match.group(1)

if found and pattern.match(found):
    print(found)
" 2>/dev/null || true)"

  if is_valid_slack_channel_id "$resolved_channel_id"; then
    set_config_value slack_channel_id "$resolved_channel_id"
    ok "Auto-resolved slack_channel_id: $resolved_channel_id"
    return 0
  fi

  return 1
}

parse_slack_url() {
  local url="$1"
  # Extract D... channel ID from URLs like https://app.slack.com/client/TXXXX/DXXXX
  local channel_id
  channel_id="$(printf '%s' "$url" | grep -oE 'D[A-Z0-9]{6,}' | head -1 || true)"
  printf '%s' "$channel_id"
}

if [[ -f "$CONFIG_FILE" ]]; then
  normalize_slack_channel_id || true

  timezone_value="$(get_config_value timezone)"
  if [[ -z "${timezone_value// }" ]]; then
    set_config_value timezone "UTC"
    ok "Set default timezone to UTC"
  fi

  # Try to auto-resolve Slack identity before interactive prompts
  try_slack_resolve || true
  try_slack_channel_resolve || true

  if [[ -t 0 ]]; then
    current_timezone="$(get_config_value timezone)"
    printf '\nTimezone [%s]: ' "$current_timezone"
    read -r input_timezone || true
    if [[ -n "${input_timezone// }" ]]; then
      set_config_value timezone "$input_timezone"
      ok "Updated timezone"
    fi

    current_slack_user_id="$(get_config_value slack_user_id)"
    if [[ -z "${current_slack_user_id// }" ]]; then
      printf 'Slack user ID (U...) or paste a Slack DM URL to extract IDs automatically [leave blank to fill later]: '
      read -r input_slack_user_id || true
      if [[ -n "${input_slack_user_id// }" ]]; then
        if [[ "$input_slack_user_id" == http* ]]; then
          # URL paste: extract channel ID
          extracted_channel="$(parse_slack_url "$input_slack_user_id")"
          if [[ -n "${extracted_channel// }" ]]; then
            set_config_value slack_channel_id "$extracted_channel"
            ok "Extracted slack_channel_id from URL: $extracted_channel"
          fi
          printf 'Slack user ID (U...) [still needed — your personal user ID, not the channel]: '
          read -r input_slack_user_id || true
        fi
        if [[ -n "${input_slack_user_id// }" ]] && [[ "$input_slack_user_id" != http* ]]; then
          set_config_value slack_user_id "$input_slack_user_id"
          ok "Stored slack_user_id"
          try_slack_channel_resolve || true
        fi
      fi
    fi

    current_channel_id="$(get_config_value slack_channel_id)"
    if [[ -z "${current_channel_id// }" ]]; then
      printf 'Slack channel ID for polling (D..., C..., or G...) [leave blank to auto-resolve self-DM]: '
      read -r input_channel_id || true
      if [[ -n "${input_channel_id// }" ]]; then
        if is_valid_slack_channel_id "$input_channel_id"; then
          set_config_value slack_channel_id "$input_channel_id"
          ok "Stored slack_channel_id"
        else
          warn "Ignoring invalid slack_channel_id '$input_channel_id'. Slack polling requires a real D..., C..., or G... channel ID."
        fi
      fi
    fi
  fi

  normalize_slack_channel_id || true
  try_slack_channel_resolve || true

  slack_user_id="$(get_config_value slack_user_id)"
  slack_channel_id="$(get_config_value slack_channel_id)"
  timezone_final="$(get_config_value timezone)"

  if [[ -z "${slack_user_id// }" ]]; then
    action_needed "config.yaml: slack_user_id is empty. Claude can usually resolve this via Slack tools."
  else
    ok "config.yaml: slack_user_id present"
  fi

  if is_valid_slack_channel_id "$slack_channel_id"; then
    ok "config.yaml: slack_channel_id present and pollable"
  else
    action_needed "config.yaml: slack_channel_id is unresolved. Slack polling will not work until setup stores a real D..., C..., or G... channel ID. Sending may still work with slack_user_id."
  fi

  if [[ -z "${timezone_final// }" ]]; then
    action_needed "config.yaml: timezone is empty. Set an IANA timezone like America/Edmonton."
  else
    ok "config.yaml: timezone set to $timezone_final"
  fi
fi

if command -v claude >/dev/null 2>&1; then
  mcp_list_output="$(claude mcp list 2>/dev/null || true)"
  if [[ -z "${mcp_list_output// }" ]]; then
    warn "Could not query MCP integrations automatically (claude mcp list unavailable or empty output)."
    action_needed "Confirm these integrations are enabled in Claude: Slack, Gmail, Fireflies, Google Calendar, Google Drive. Open Claude Code settings > MCP Integrations to enable them."
  else
    check_mcp() {
      local label="$1"
      local pattern="$2"
      if printf '%s' "$mcp_list_output" | grep -Eiq "$pattern"; then
        ok "MCP integration detected: $label"
      else
        action_needed "Enable MCP integration: $label — Open Claude Code settings > MCP Integrations"
      fi
    }

    check_mcp "Slack" "(claude_ai_Slack|Slack)"
    check_mcp "Gmail" "(claude_ai_Gmail|Gmail)"
    check_mcp "Fireflies" "(claude_ai_Fireflies|Fireflies)"
    check_mcp "Google Calendar" "(claude_ai_Google_Calendar|Google.Calendar|Calendar)"
    check_mcp "Google Drive" "(claude_ai_Google_Drive|Google.Drive|Drive)"
  fi
fi

# MCP tool inventory snapshot
if command -v python3 >/dev/null 2>&1 && [[ -f "$BASE_DIR/scripts/mcp_inventory.py" ]]; then
  python3 "$BASE_DIR/scripts/mcp_inventory.py" 2>/dev/null \
    && ok "MCP tool inventory saved to .context/mcp_tools.json" \
    || warn "Could not snapshot MCP tools (non-fatal)"
fi

printf '\nSummary: %d blocked, %d action needed, %d warnings\n' "$BLOCKERS" "$ACTIONS" "$WARNINGS"

if [[ "$BLOCKERS" -gt 0 ]]; then
  printf 'Setup cannot continue until blocked items are fixed.\n'
  exit 2
fi

if [[ "$ACTIONS" -gt 0 ]]; then
  cat <<'TXT'
Setup is partially complete.
Next: ask Claude Code to finish unresolved items, for example:
"Finish setup for this project. Resolve Slack IDs if possible and tell me exactly what is still missing."
TXT
  exit 1
fi

printf 'Setup checks passed. Start the agent with: python3 pulse.py\n'
