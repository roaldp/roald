#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_TEMPLATE="$BASE_DIR/config.template.yaml"
CONFIG_FILE="$BASE_DIR/config.yaml"

BLOCKERS=0
ACTIONS=0
ACTION_ITEMS=()
WARNINGS=0

ok() {
  printf '  \xe2\x9c\x93 %s\n' "$1"
}

action_needed() {
  ACTIONS=$((ACTIONS + 1))
  ACTION_ITEMS+=("$1")
  printf '  \xe2\x86\x92 %s\n' "$1"
}

blocked() {
  BLOCKERS=$((BLOCKERS + 1))
  printf '  \xe2\x9c\x97 %s\n' "$1"
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf '  ! %s\n' "$1"
}

# Pure-bash config helpers — no PyYAML needed for setup
get_config_value() {
  local key="$1"
  if [[ ! -f "$CONFIG_FILE" ]]; then
    return
  fi
  # Match top-level key: value (handles quoted and unquoted values)
  local raw
  raw="$(grep -E "^${key}:" "$CONFIG_FILE" | head -1 | sed 's/^[^:]*: *//')" || true
  # Strip inline YAML comments (# preceded by whitespace, outside quotes)
  # Handle quoted values: extract content between first pair of quotes
  if [[ "$raw" == \"*\"* ]]; then
    # Double-quoted: extract between first pair of "
    raw="${raw#\"}"
    raw="${raw%%\"*}"
  elif [[ "$raw" == \'*\'* ]]; then
    # Single-quoted: extract between first pair of '
    raw="${raw#\'}"
    raw="${raw%%\'*}"
  else
    # Unquoted: strip trailing comment
    raw="$(printf '%s' "$raw" | sed 's/  *#.*//')"
  fi
  printf '%s' "$raw"
}

set_config_value() {
  local key="$1"
  local value="$2"
  if grep -qE "^${key}:" "$CONFIG_FILE" 2>/dev/null; then
    # Replace existing key (macOS sed requires '' after -i)
    sed -i '' "s|^${key}:.*|${key}: \"${value}\"|" "$CONFIG_FILE"
  else
    echo "${key}: \"${value}\"" >> "$CONFIG_FILE"
  fi
}

# Auto-detect system timezone (macOS)
detect_timezone() {
  local tz=""
  # macOS: /etc/localtime is a symlink to zoneinfo
  if [[ -L /etc/localtime ]]; then
    tz="$(readlink /etc/localtime 2>/dev/null | sed 's|.*/zoneinfo/||')" || true
  fi
  # Fallback: Python
  if [[ -z "$tz" ]] && command -v python3 >/dev/null 2>&1; then
    tz="$(python3 -c "
try:
    from datetime import datetime, timezone
    import time
    lt = time.localtime()
    if hasattr(lt, 'tm_zone') and '/' in (time.tzname[0] or ''):
        print(time.tzname[0])
    else:
        from pathlib import Path
        p = Path('/etc/localtime').resolve()
        parts = p.parts
        if 'zoneinfo' in parts:
            idx = parts.index('zoneinfo')
            print('/'.join(parts[idx+1:]))
except Exception:
    pass
" 2>/dev/null || true)"
  fi
  printf '%s' "$tz"
}

# Fuzzy timezone mapping for common abbreviations
resolve_timezone_alias() {
  local input="$1"
  case "$(printf '%s' "$input" | tr '[:upper:]' '[:lower:]')" in
    est) printf 'America/New_York' ;;
    cst) printf 'America/Chicago' ;;
    mst) printf 'America/Denver' ;;
    pst) printf 'America/Los_Angeles' ;;
    cet) printf 'Europe/Paris' ;;
    eet) printf 'Europe/Bucharest' ;;
    gmt) printf 'Europe/London' ;;
    bst) printf 'Europe/London' ;;
    brussels) printf 'Europe/Brussels' ;;
    london) printf 'Europe/London' ;;
    paris) printf 'Europe/Paris' ;;
    amsterdam) printf 'Europe/Amsterdam' ;;
    berlin) printf 'Europe/Berlin' ;;
    *) printf '%s' "$input" ;;
  esac
}

printf '\nLocal Claude Companion — Setup\n\n'

# ── Prerequisites ──

printf 'Checking prerequisites...\n'

if command -v claude >/dev/null 2>&1; then
  ok "Claude Code found"
else
  blocked "Claude Code not found. Install it from https://claude.ai/download and make sure 'claude' is in your PATH."
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
  then
    ok "Python 3.9+ found"
  else
    blocked "Python 3.9+ is required. You have an older version. On Mac: brew install python3"
  fi
else
  blocked "Python 3 not found. On Mac: brew install python3 — or download from python.org"
fi

if [[ ! -f "$CONFIG_TEMPLATE" ]]; then
  blocked "Missing config template — the repo may be incomplete"
else
  ok "Config template found"
fi

# ── Config ──

printf '\nSetting up config...\n'

if [[ -f "$CONFIG_FILE" ]]; then
  ok "config.yaml exists"
else
  cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
  ok "Created config.yaml"
fi

# Auto-detect and set timezone
if [[ -f "$CONFIG_FILE" ]]; then
  timezone_value="$(get_config_value timezone)"
  if [[ -z "${timezone_value// }" ]] || [[ "$timezone_value" == "UTC" ]]; then
    detected_tz="$(detect_timezone)"
    if [[ -n "${detected_tz// }" ]] && [[ "$detected_tz" != "UTC" ]]; then
      set_config_value timezone "$detected_tz"
      ok "Timezone auto-detected: $detected_tz"
    elif [[ -z "${timezone_value// }" ]]; then
      set_config_value timezone "UTC"
      ok "Timezone set to UTC (update in config.yaml if needed)"
    fi
  else
    # Resolve common abbreviations
    resolved_tz="$(resolve_timezone_alias "$timezone_value")"
    if [[ "$resolved_tz" != "$timezone_value" ]]; then
      set_config_value timezone "$resolved_tz"
      ok "Timezone resolved: $timezone_value -> $resolved_tz"
    else
      ok "Timezone: $timezone_value"
    fi
  fi
fi

# ── Slack Identity ──

printf '\nResolving Slack identity...\n'

try_slack_resolve() {
  local current_uid
  current_uid="$(get_config_value slack_user_id)"
  if [[ -n "${current_uid// }" ]]; then
    return 0  # already set
  fi
  if ! command -v claude >/dev/null 2>&1; then
    return 1
  fi
  printf '  Attempting auto-resolve via Slack...\n'
  local result
  result="$(claude -p "Use slack_read_user_profile with no arguments to get the current user's profile. Return ONLY a JSON object with exactly these fields: user_id (the Slack U... ID), display_name. No other text, no markdown." \
    --allowedTools "mcp__claude_ai_Slack__slack_read_user_profile" \
    --output-format json 2>/dev/null || true)"
  if [[ -z "${result// }" ]]; then
    return 1
  fi
  local resolved_id
  resolved_id="$(printf '%s' "$result" | python3 -c "
import sys, json, re
try:
    data = json.load(sys.stdin)
    if isinstance(data, list): data = data[-1]
    uid = data.get('user_id','') or data.get('result','')
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
    ok "Slack identity resolved: $resolved_id${display_name:+ ($display_name)}"
    return 0
  fi
  return 1
}

try_slack_resolve || true

slack_user_id="$(get_config_value slack_user_id)"
if [[ -z "${slack_user_id// }" ]]; then
  action_needed "Slack user ID not set. Claude can usually resolve this automatically when the companion starts."
else
  ok "Slack user ID: $slack_user_id"
fi

slack_channel_id="$(get_config_value slack_channel_id)"
if [[ -z "${slack_channel_id// }" ]]; then
  ok "Slack channel: will use self-DM (default)"
else
  ok "Slack channel: $slack_channel_id"
fi

# ── Connected Apps ──

printf '\nChecking connected apps...\n'

if command -v claude >/dev/null 2>&1; then
  mcp_list_output="$(claude mcp list 2>/dev/null || true)"
  if [[ -z "${mcp_list_output// }" ]]; then
    warn "Could not check connected apps automatically."
    action_needed "Make sure Slack is connected in Claude Code. Type /integrations in Claude Code to check."
  else
    check_app() {
      local label="$1"
      local pattern="$2"
      local required="${3:-false}"
      if printf '%s' "$mcp_list_output" | grep -Eiq "$pattern"; then
        ok "$label connected"
      elif [[ "$required" == "true" ]]; then
        action_needed "$label not connected. In Claude Code, type /integrations and connect $label."
      else
        warn "$label not connected (optional). Connect it in Claude Code with /integrations if you want to use it."
      fi
    }

    check_app "Slack" "(claude_ai_Slack|Slack)" "true"
    check_app "Gmail" "(claude_ai_Gmail|Gmail)"
    check_app "Google Calendar" "(claude_ai_Google_Calendar|Google.Calendar|Calendar)"
    check_app "Fireflies" "(claude_ai_Fireflies|Fireflies)"
    check_app "Google Drive" "(claude_ai_Google_Drive|Google.Drive|Drive)"
  fi
fi

# MCP tool inventory snapshot
if command -v python3 >/dev/null 2>&1 && [[ -f "$BASE_DIR/scripts/mcp_inventory.py" ]]; then
  python3 "$BASE_DIR/scripts/mcp_inventory.py" 2>/dev/null \
    && ok "App inventory saved" \
    || true
fi

# ── Summary ──

printf '\n'

if [[ "$BLOCKERS" -gt 0 ]]; then
  printf 'A few things need fixing before we can start:\n'
  printf '  See the items marked with \xe2\x9c\x97 above.\n'
  exit 2
fi

if [[ "$ACTIONS" -gt 0 ]]; then
  printf 'Almost there! Here'"'"'s what'"'"'s left:\n'
  local_i=1
  for item in "${ACTION_ITEMS[@]}"; do
    printf '  %d. %s\n' "$local_i" "$item"
    local_i=$((local_i + 1))
  done
  printf '\nClaude can usually resolve these automatically. Start the companion and it will try.\n'
  exit 1
fi

printf 'All set! Ready to start your companion.\n'
