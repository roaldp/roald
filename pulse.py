#!/usr/bin/env python3
"""pulse.py — Event loop for a personal AI companion."""

import argparse
import asyncio
import collections
import json
import os
import re
import secrets
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import yaml
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pyyaml"],
        stdout=subprocess.DEVNULL,
    )
    import yaml

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
MIND_PATH = BASE_DIR / "mind.md"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
KNOWLEDGE_INDEX_PATH = KNOWLEDGE_DIR / "index.md"
LOCK_PATH = BASE_DIR / "logs" / ".pulse_lock"
UPDATE_PENDING_PATH = BASE_DIR / "logs" / ".update_pending"
SKIP_MARKER_PATH = BASE_DIR / "logs" / ".update_skipped_at"
LAST_GOOD_COMMIT_PATH = BASE_DIR / "logs" / ".last_good_commit"
SLACK_LAST_TS_PATH = BASE_DIR / "logs" / ".slack_last_ts"
LOG_PATH = BASE_DIR / "logs" / "pulse.log"
RESTART_EXIT_CODE = 42
PROMPT_FULL = BASE_DIR / "prompts" / "pulse_full.md"
PROMPT_CHECK = BASE_DIR / "prompts" / "pulse_check.md"
PROMPT_ONBOARDING = BASE_DIR / "prompts" / "pulse_onboarding.md"
PROMPT_REACTIVE = BASE_DIR / "prompts" / "pulse_reactive.md"
UPDATES_JSONL_PATH = BASE_DIR / "logs" / "pulse_updates.jsonl"
TEMPLATES_DIR = BASE_DIR / "templates"
MIND_TEMPLATE_PATH = TEMPLATES_DIR / "mind.template.md"
KNOWLEDGE_INDEX_TEMPLATE_PATH = TEMPLATES_DIR / "knowledge_index.template.md"

ALLOWED_TOOLS = (
    "Read,Edit,MultiEdit,Write,Glob,Grep,"
    "mcp__claude_ai_Slack__*,"
    "mcp__claude_ai_Gmail__*,"
    "mcp__claude_ai_Fireflies__*,"
    "mcp__claude_ai_Google_Calendar__*,"
    "mcp__claude_ai_Google_Drive__*"
)

SLACK_OUTBOUND_TOOLS = {
    "mcp__claude_ai_Slack__slack_send_message",
    "mcp__claude_ai_Slack__slack_schedule_message",
}

# Sliding-window rate limiter for outbound Slack messages.
# _record_slack_send() is called at TOOL START inside run_claude (authoritative).
# _slack_at_limit() is checked BEFORE initiating any send operation so we can
# abort early. Together they form a hard circuit breaker against feedback loops.
SLACK_SEND_WINDOW = 60       # seconds
SLACK_SEND_LIMIT  = 5        # max messages per window
_slack_send_times: collections.deque = collections.deque()


def _record_slack_send() -> None:
    """Record that an outbound Slack message was just sent."""
    _slack_send_times.append(time.monotonic())


def _slack_at_limit() -> bool:
    """Return True if the send rate limit is currently exceeded."""
    now = time.monotonic()
    while _slack_send_times and now - _slack_send_times[0] > SLACK_SEND_WINDOW:
        _slack_send_times.popleft()
    exceeded = len(_slack_send_times) >= SLACK_SEND_LIMIT
    if exceeded:
        log(
            f"SLACK RATE LIMIT: {len(_slack_send_times)} messages in {SLACK_SEND_WINDOW}s "
            "— send blocked to prevent feedback loop"
        )
    return exceeded


def is_claude_echo_message(text: str) -> bool:
    lowered = text.lower()
    # In this workspace, Slack messages sent by Claude are echoed back in the DM
    # and often include "Sent using <@...|Claude>" markup.
    return "sent using" in lowered and "claude" in lowered


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG_KEY_RENAMES = {
    "slack_dm_channel_id": "slack_channel_id",
}

TEMPLATE_PATH = BASE_DIR / "config.template.yaml"


def migrate_config(config: dict) -> dict:
    """Ensure user config has all keys from template, preserving user values."""
    if not TEMPLATE_PATH.exists():
        return config

    template = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))
    changed = False

    # Handle key renames
    for old_key, new_key in CONFIG_KEY_RENAMES.items():
        if old_key in config and new_key not in config:
            config[new_key] = config.pop(old_key)
            changed = True
            log(f"Config migrated: renamed '{old_key}' -> '{new_key}'")

    # Merge missing keys from template (non-destructive)
    for key, default_value in template.items():
        if key not in config:
            config[key] = default_value
            changed = True
            log(f"Config migrated: added '{key}' with default value")
        elif isinstance(default_value, dict) and isinstance(config.get(key), dict):
            for sub_key, sub_default in default_value.items():
                if sub_key not in config[key]:
                    config[key][sub_key] = sub_default
                    changed = True
                    log(f"Config migrated: added '{key}.{sub_key}' with default value")

    if changed:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, sort_keys=False)
        log("Config migration complete — config.yaml updated")

    return config


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    line = f"[{now_str()}] {msg}"
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[{now_str()}] LOGGING ERROR: {e}", flush=True)


def current_time_iso(config: Optional[dict] = None) -> str:
    if config and config.get("timezone"):
        tz_name = str(config["timezone"]).strip()
        try:
            return datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M:%S %Z")
        except ZoneInfoNotFoundError:
            log(f"Unknown timezone '{tz_name}' in config; falling back to local timezone")
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def acquire_lock() -> bool:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        return False
    LOCK_PATH.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    if LOCK_PATH.exists():
        LOCK_PATH.unlink()


def is_first_run() -> bool:
    """Returns True if mind.md has never been pulsed (no timestamp in Last Pulse section)."""
    if not MIND_PATH.exists():
        return True
    text = MIND_PATH.read_text(encoding="utf-8")
    # Template default — no pulse has completed yet
    return "_No pulses yet._" in text


def ensure_runtime_files() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    (KNOWLEDGE_DIR / "meetings").mkdir(parents=True, exist_ok=True)
    (KNOWLEDGE_DIR / "emails").mkdir(parents=True, exist_ok=True)
    (KNOWLEDGE_DIR / "notes").mkdir(parents=True, exist_ok=True)

    if not MIND_PATH.exists():
        if MIND_TEMPLATE_PATH.exists():
            MIND_PATH.write_text(MIND_TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            MIND_PATH.write_text("# Mind\n\n## Last Pulse\n_Not set._\n", encoding="utf-8")
        log("Initialized mind.md from template")

    if not KNOWLEDGE_INDEX_PATH.exists():
        if KNOWLEDGE_INDEX_TEMPLATE_PATH.exists():
            KNOWLEDGE_INDEX_PATH.write_text(
                KNOWLEDGE_INDEX_TEMPLATE_PATH.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        else:
            KNOWLEDGE_INDEX_PATH.write_text("# Knowledge Index\n", encoding="utf-8")
        log("Initialized knowledge/index.md from template")


# ---------------------------------------------------------------------------
# Two-phase pulse helpers: extract context from files without LLM calls
# ---------------------------------------------------------------------------

def get_connected_sources(config: dict) -> list[str]:
    """Determine which sources are actually connected and enabled (no LLM call)."""
    sources_config = config.get("sources", {})
    mcp_path = BASE_DIR / ".context" / "mcp_tools.json"
    connected_servers: set[str] = set()
    if mcp_path.exists():
        try:
            inventory = json.loads(mcp_path.read_text(encoding="utf-8"))
            for server in inventory.get("servers", []):
                if "Connected" in str(server):
                    connected_servers.add(str(server).lower())
        except Exception:
            pass

    source_mcp_keywords = {
        "slack": "slack",
        "gmail": "gmail",
        "calendar": "calendar",
        "fireflies": "fireflies",
        "google_drive": "drive",
    }
    connected = []
    for source, keyword in source_mcp_keywords.items():
        if not sources_config.get(source, False):
            continue
        if any(keyword in s for s in connected_servers):
            connected.append(source)
    return connected


def get_last_pulse_time() -> str:
    """Extract Last Pulse timestamp from mind.md (no LLM call)."""
    if not MIND_PATH.exists():
        return "_No pulses yet._"
    text = MIND_PATH.read_text(encoding="utf-8")
    match = re.search(r"## Last Pulse\n(.+)", text)
    if match:
        return match.group(1).strip()
    return "_No pulses yet._"


def get_next_pulse_instructions() -> str:
    """Extract Next Pulse Instructions section from mind.md (no LLM call)."""
    if not MIND_PATH.exists():
        return "_No instructions._"
    text = MIND_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"## Next Pulse Instructions\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    if match:
        instructions = match.group(1).strip()
        return instructions if instructions else "_No instructions._"
    return "_No instructions._"


def update_last_pulse_time(config: dict) -> None:
    """Update the Last Pulse timestamp in mind.md directly (no LLM call)."""
    if not MIND_PATH.exists():
        return
    text = MIND_PATH.read_text(encoding="utf-8")
    new_time = current_time_iso(config)
    updated = re.sub(r"(## Last Pulse\n).*", rf"\g<1>{new_time}", text)
    if updated != text:
        MIND_PATH.write_text(updated, encoding="utf-8")


def append_pulse_update(update: dict) -> None:
    """Append a structured event to the JSONL log (no LLM call)."""
    UPDATES_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    update["timestamp"] = datetime.now().isoformat()
    with open(UPDATES_JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(update, ensure_ascii=False) + "\n")


def run_consolidation() -> None:
    """Run the consolidation script to merge JSONL updates into mind.md."""
    script = BASE_DIR / "scripts" / "consolidate.py"
    if not script.exists():
        return
    if not UPDATES_JSONL_PATH.exists():
        return
    # Skip if JSONL is empty
    content = UPDATES_JSONL_PATH.read_text(encoding="utf-8").strip()
    if not content:
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(BASE_DIR),
            timeout=30,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log(f"CONSOLIDATION OK: {result.stdout.strip()}")
        else:
            log(f"CONSOLIDATION FAIL: {result.stderr.strip()}")
    except Exception as e:
        log(f"CONSOLIDATION ERROR: {e}")


def _short_text(value: object, limit: int = 160) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _short_json(value: object, limit: int = 240) -> str:
    try:
        text = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    except TypeError:
        text = str(value)
    return _short_text(text, limit=limit)


def run_claude(
    prompt: str,
    config: dict,
    allowed_tools: str = ALLOWED_TOOLS,
    operation: str = "claude_run",
    system_prompt: Optional[str] = None,
    model_override: Optional[str] = None,
) -> str:
    log(f"EXEC START: {operation}")
    started = time.monotonic()
    cmd = [
        config.get("claude_command", "claude"),
        "-p", prompt,
        "--allowedTools", allowed_tools,
        "--output-format", "stream-json",
        "--verbose",
    ]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]
    model = model_override or config.get("claude_model", "")
    if model:
        cmd += ["--model", model]
    # Clear CLAUDECODE env var to allow spawning Claude from within a Claude session
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    timeout_seconds = int(config.get("claude_timeout_seconds", 300))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            env=env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"claude timed out after {timeout_seconds}s") from e
    if result.returncode != 0:
        error_tail = _short_text(result.stderr or result.stdout, limit=400)
        raise RuntimeError(f"claude exited {result.returncode}: {error_tail}")

    result_text = ""
    tool_calls: dict[str, dict] = {}
    tool_starts = 0
    tool_ends = 0
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")
        if event_type == "assistant":
            message = event.get("message", {})
            for block in message.get("content", []):
                if block.get("type") != "tool_use":
                    continue
                tool_name = str(block.get("name", "unknown_tool"))
                tool_id = str(block.get("id", ""))
                tool_input = block.get("input", {})
                tool_calls[tool_id] = {"name": tool_name, "input": tool_input}
                tool_starts += 1
                log(f"TOOL START: {tool_name} input={_short_json(tool_input)}")
                if tool_name in SLACK_OUTBOUND_TOOLS:
                    channel = tool_input.get("channel_id", "?")
                    text_preview = tool_input.get("text") or tool_input.get("message") or ""
                    _record_slack_send()
                    log(
                        "SLACK OUTBOUND START: "
                        f"channel={channel} tool={tool_name} text={_short_text(text_preview)}"
                    )

        elif event_type == "user":
            message = event.get("message", {})
            for block in message.get("content", []):
                if block.get("type") != "tool_result":
                    continue
                tool_id = str(block.get("tool_use_id", ""))
                info = tool_calls.get(tool_id, {})
                tool_name = str(info.get("name", "unknown_tool"))
                tool_input = info.get("input", {})
                is_error = bool(block.get("is_error"))
                status = "ERROR" if is_error else "OK"
                tool_ends += 1
                log(f"TOOL END: {tool_name} status={status}")
                if tool_name in SLACK_OUTBOUND_TOOLS:
                    channel = tool_input.get("channel_id", "?")
                    log(f"SLACK OUTBOUND END: channel={channel} tool={tool_name} status={status}")

        elif event_type == "result":
            result_text = str(event.get("result", ""))

    elapsed = time.monotonic() - started
    log(f"EXEC END: {operation} ({elapsed:.1f}s, tools started={tool_starts}, tools ended={tool_ends})")
    return result_text


def poll_slack_messages(
    config: dict,
    channel_id: str,
    ack_after_ts: Optional[str] = None,
    ack_user_id: str = "",
) -> list[dict]:
    """Read recent messages from a Slack channel.

    If ack_after_ts and ack_user_id are set, the model will also send a brief
    acknowledgment for any message from that user newer than ack_after_ts —
    all within the same subprocess, so no extra startup cost.
    """
    fast_model = config.get("slack_poll_model", "haiku")

    if ack_after_ts and ack_user_id:
        ack_clause = (
            f" If any message has ts > {ack_after_ts} and user == '{ack_user_id}',"
            f" send a brief 1-sentence ack to channel {channel_id} BEFORE the JSON"
            f" (e.g. 'On it!' or 'Got it, looking into that now')."
            f" Then output the JSON."
        )
        allowed = (
            "mcp__claude_ai_Slack__slack_read_channel,"
            "mcp__claude_ai_Slack__slack_send_message"
        )
    else:
        ack_clause = ""
        allowed = "mcp__claude_ai_Slack__slack_read_channel"

    prompt = (
        f"Read channel {channel_id} (last 5).{ack_clause} "
        "Reply with JSON: [{\"ts\":\"...\",\"user\":\"...\",\"text\":\"...\"}]"
    )
    text = run_claude(
        prompt,
        config,
        allowed_tools=allowed,
        operation=f"poll[{channel_id}]",
        model_override=fast_model,
    )
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return []


async def slack_loop(config: dict) -> None:
    interval = config.get("slack_poll_interval_seconds", 1)
    user_id = str(config.get("slack_user_id", "")).strip()
    channel_id = slack_channel(config)

    # Load last_ts from disk so restarts don't replay old messages
    last_ts: Optional[str] = None
    try:
        if SLACK_LAST_TS_PATH.exists():
            last_ts = SLACK_LAST_TS_PATH.read_text().strip() or None
    except Exception:
        pass

    active_pulse: Optional[asyncio.Task] = None
    pending_queue: collections.deque[str] = collections.deque(maxlen=5)
    log(f"Slack listener started (channel={channel_id}, interval={interval}s, last_ts={last_ts})")

    while True:
        await asyncio.sleep(interval)
        try:
            # Clean up finished pulse task and drain queue
            if active_pulse and active_pulse.done():
                exc = active_pulse.exception() if not active_pulse.cancelled() else None
                if exc:
                    log(f"PULSE REACTIVE ERROR: background task: {exc}")
                active_pulse = None

                # Advance watermark to now. Pulse just finished so its response_ts
                # < time.time(). +1s absorbs local/Slack clock skew.
                last_ts = f"{time.time() + 1:.6f}"
                try:
                    SLACK_LAST_TS_PATH.parent.mkdir(parents=True, exist_ok=True)
                    SLACK_LAST_TS_PATH.write_text(last_ts)
                except Exception:
                    pass
                log(f"SLACK WATERMARK ADVANCED: last_ts={last_ts}")

                # Start next queued message if any
                if pending_queue:
                    queued_text = pending_queue.popleft()
                    log(f"PULSE REACTIVE DEQUEUE: remaining={len(pending_queue)} text={_short_text(queued_text, 80)}")
                    active_pulse = asyncio.create_task(
                        run_reactive_pulse(config, queued_text, channel_id=channel_id)
                    )

            # Disable inline ack if rate limit is already exceeded
            ack_ts   = last_ts  if not _slack_at_limit() else None
            ack_user = user_id  if not _slack_at_limit() else ""
            messages = poll_slack_messages(
                config, channel_id,
                ack_after_ts=ack_ts,
                ack_user_id=ack_user,
            )
            if not messages:
                continue

            newest = max(messages, key=lambda m: float(m.get("ts", 0)))
            newest_ts = newest.get("ts", "")

            if last_ts is None:
                last_ts = newest_ts
                continue

            new_messages = [m for m in messages if float(m.get("ts", 0)) > float(last_ts)]
            if not new_messages:
                continue

            for msg in sorted(new_messages, key=lambda m: float(m.get("ts", 0))):
                msg_user = str(msg.get("user", "")).strip()
                if user_id and msg_user != user_id:
                    continue
                user_text = msg.get("text", "").strip()
                if is_claude_echo_message(user_text):
                    log(
                        "SLACK INBOUND SKIP: "
                        f"channel={channel_id} reason=claude_echo ts={msg.get('ts', '?')} "
                        f"text={_short_text(user_text)}"
                    )
                    continue
                log(
                    "SLACK INBOUND: "
                    f"channel={channel_id} user={msg_user or '?'} ts={msg.get('ts', '?')} "
                    f"text={_short_text(user_text)}"
                )
                if await handle_update_command(config, user_text):
                    continue

                # Ack was already sent inline by the poll subprocess above.
                # Start full reactive pulse (non-blocking background task).
                if active_pulse and not active_pulse.done():
                    pending_queue.append(user_text)
                    log(f"PULSE REACTIVE QUEUED: queue_size={len(pending_queue)} text={_short_text(user_text, 80)}")
                else:
                    active_pulse = asyncio.create_task(
                        run_reactive_pulse(config, user_text, channel_id=channel_id)
                    )

            # Use current time as watermark when new messages were processed.
            # This ensures any acks/responses Claude just sent (which have a ts
            # slightly after the user's message) are already behind the watermark
            # on the next poll, preventing echo loops.
            if new_messages:
                # Watermark = now. We set this AFTER the ack was already sent,
                # so ack_ts < time.time(). +1s absorbs any local/Slack clock skew.
                last_ts = f"{time.time() + 1:.6f}"
            else:
                last_ts = newest_ts
            try:
                SLACK_LAST_TS_PATH.parent.mkdir(parents=True, exist_ok=True)
                SLACK_LAST_TS_PATH.write_text(last_ts)
            except Exception:
                pass

        except Exception as e:
            log(f"Slack loop error: {e}")


MAX_USER_MESSAGE_LENGTH = 2000
MESSAGE_TOO_LONG_REPLY = (
    "Your message is too long for me to process safely. "
    "If you want to share file context, just point me to the file — "
    "drop a link or file path and I'll read it directly."
)


def send_slack_message(config: dict, channel_id: str, text: str) -> None:
    """Send an exact message to Slack using the fast model."""
    if _slack_at_limit():
        return
    fast_model = config.get("slack_poll_model", "haiku")
    prompt = f'Send this exact message to channel {channel_id}: "{text}"'
    try:
        run_claude(
            prompt, config,
            allowed_tools="mcp__claude_ai_Slack__slack_send_message",
            operation="slack_msg",
            model_override=fast_model,
        )
        log(f"SLACK OUTBOUND DIRECT: channel={channel_id} text={_short_text(text)}")
    except Exception as e:
        log(f"SLACK OUTBOUND FAIL: channel={channel_id} error={e}")



def _datamark(text: str, marker: str = "^") -> str:
    """Apply datamarking: replace whitespace with a marker token.

    This is a spotlighting technique (Microsoft Research) that helps the LLM
    distinguish untrusted data from system instructions by making the data
    visually distinct.  ASR drops from ~50% to <3% with this technique.
    """
    return re.sub(r"\s+", marker, text)


async def run_reactive_pulse(config: dict, user_message: str, channel_id: str = "") -> None:
    if not acquire_lock():
        log("PULSE REACTIVE SKIP: locked")
        return
    try:
        log("PULSE REACTIVE START")
        if len(user_message) > MAX_USER_MESSAGE_LENGTH:
            log(f"PULSE REACTIVE REJECT: length={len(user_message)} max={MAX_USER_MESSAGE_LENGTH}")
            if channel_id:
                send_slack_message(config, channel_id, MESSAGE_TOO_LONG_REPLY)
            return
        template = PROMPT_REACTIVE.read_text()

        # Generate a per-invocation salt for XML tag boundaries.
        # This prevents attackers from guessing/spoofing the delimiter tags.
        salt = secrets.token_hex(4)

        system = (
            template
            .replace("{{CURRENT_TIME}}", current_time_iso(config))
            .replace("{{SLACK_CHANNEL_ID}}", slack_channel(config))
            .replace("{{SALT}}", salt)
        )

        # Datamark the user message: replace whitespace with ^ so the model
        # can visually distinguish it from system instructions.
        marked_message = _datamark(user_message)
        prompt = f"<user-message-{salt}>\n{marked_message}\n</user-message-{salt}>"

        output = run_claude(prompt, config, operation="reactive_pulse", system_prompt=system)
        log(f"PULSE REACTIVE END: output_len={len(output)}")

        append_pulse_update({
            "type": "reactive",
            "message_preview": _short_text(user_message, 80),
            "output_len": len(output),
        })
    except Exception as e:
        log(f"PULSE REACTIVE ERROR: {e}")
    finally:
        release_lock()


def refresh_mcp_inventory() -> None:
    """Refresh .context/mcp_tools.json before each full pulse."""
    inventory_script = BASE_DIR / "scripts" / "mcp_inventory.py"
    if not inventory_script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(inventory_script)],
            cwd=str(BASE_DIR),
            timeout=30,
            capture_output=True,
        )
    except Exception as e:
        log(f"MCP inventory refresh skipped: {e}")


# ---------------------------------------------------------------------------
# Auto-update helpers
# ---------------------------------------------------------------------------

def check_for_updates(config: dict) -> Optional[dict]:
    """Check upstream for new commits. Returns info dict or None if up-to-date."""
    branch = config.get("auto_update", {}).get("branch", "main")
    try:
        subprocess.run(
            ["git", "fetch", "origin", branch],
            capture_output=True, text=True,
            cwd=str(BASE_DIR), timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log("Update check: git fetch failed (no network?)")
        return None

    try:
        result = subprocess.run(
            ["git", "rev-list", f"HEAD..origin/{branch}", "--count"],
            capture_output=True, text=True,
            cwd=str(BASE_DIR), timeout=10,
        )
        count = int(result.stdout.strip())
        if count == 0:
            return None
    except Exception:
        return None

    try:
        result = subprocess.run(
            ["git", "log", f"HEAD..origin/{branch}", "--oneline", "--no-decorate"],
            capture_output=True, text=True,
            cwd=str(BASE_DIR), timeout=10,
        )
        commits = result.stdout.strip()
    except Exception:
        commits = ""

    return {"count": count, "branch": branch, "commits": commits}


def apply_update(config: dict, force: bool = False) -> str:
    """Pull latest changes. Returns 'ok', 'dirty', 'diverged', or 'error'."""
    branch = config.get("auto_update", {}).get("branch", "main")

    if not force:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True,
                cwd=str(BASE_DIR), timeout=10,
            )
            dirty = [l for l in result.stdout.strip().splitlines() if l and not l.startswith("??")]
            if dirty:
                log(f"Update aborted: uncommitted tracked changes: {dirty}")
                return "dirty"
        except Exception as e:
            log(f"Update aborted: could not check git status: {e}")
            return "error"

    if force:
        try:
            subprocess.run(
                ["git", "fetch", "origin", branch],
                capture_output=True, text=True,
                cwd=str(BASE_DIR), timeout=30,
            )
            result = subprocess.run(
                ["git", "reset", "--hard", f"origin/{branch}"],
                capture_output=True, text=True,
                cwd=str(BASE_DIR), timeout=30,
            )
            if result.returncode != 0:
                log(f"Force update failed: {result.stderr.strip()}")
                return "error"
        except subprocess.TimeoutExpired:
            log("Force update failed: timed out")
            return "error"
    else:
        try:
            result = subprocess.run(
                ["git", "pull", "origin", branch, "--ff-only"],
                capture_output=True, text=True,
                cwd=str(BASE_DIR), timeout=60,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip().lower()
                if "not possible to fast-forward" in stderr or "non-fast-forward" in stderr:
                    log(f"Update failed: branch has diverged from origin/{branch}")
                    return "diverged"
                log(f"Update failed: {result.stderr.strip()}")
                return "error"
        except subprocess.TimeoutExpired:
            log("Update failed: git pull timed out")
            return "error"

    log(f"Update applied from origin/{branch}")
    SKIP_MARKER_PATH.unlink(missing_ok=True)
    return "ok"


def _send_slack_message(config: dict, message: str) -> None:
    """Send a simple Slack message to the configured channel."""
    if _slack_at_limit():
        return
    channel = slack_channel(config)
    prompt = f"Send this exact message to Slack channel {channel}:\n\n{message}"
    try:
        run_claude(
            prompt, config,
            allowed_tools="mcp__claude_ai_Slack__slack_send_message",
            operation="update_slack_message",
        )
    except Exception as e:
        log(f"Failed to send update Slack message: {e}")


def notify_update_available(config: dict, info: dict) -> None:
    """Send a friendly, non-technical Slack DM about available updates."""
    count = info["count"]
    commits = info.get("commits", "")

    # Try to extract a headline from the first commit message
    headline = ""
    if commits:
        first_line = commits.splitlines()[0]
        # Strip the short hash prefix (e.g. "a1b2c3d Fix something" -> "Fix something")
        parts = first_line.split(" ", 1)
        if len(parts) == 2:
            headline = parts[1]

    msg = (
        f"Hey — there's a new version available"
        f" ({count} update{'s' if count != 1 else ''})."
        f" Want me to update? Just say *update* when you're ready, or *skip* to ignore."
    )
    if headline:
        msg += f"\n\n_Main change: {headline}_"

    _send_slack_message(config, msg)


def _signal_restart() -> None:
    """Exit with restart code so start.sh relaunches with new code."""
    log("Restart signal: exiting for relaunch")
    release_lock()
    UPDATE_PENDING_PATH.unlink(missing_ok=True)
    sys.exit(RESTART_EXIT_CODE)


async def handle_update_command(config: dict, user_text: str) -> bool:
    """Handle update-related Slack commands. Returns True if handled."""
    lowered = user_text.lower().strip()

    is_force = lowered in ("force update", "force-update", "yes force update")

    if is_force or lowered in ("update", "yes update", "apply update", "yes, update"):
        if not UPDATE_PENDING_PATH.exists() and not is_force:
            return False  # no pending update, pass through to reactive pulse

        if LOCK_PATH.exists():
            log("Update deferred: pulse is running")
            _send_slack_message(config, "I'll apply the update once the current pulse finishes.")
            return True

        status = apply_update(config, force=is_force)
        if status == "ok":
            _send_slack_message(config, "Update applied! Restarting now — I'll be back in a moment.")
            _signal_restart()
        elif status == "diverged":
            _send_slack_message(
                config,
                "Your local code has diverged from the main branch — a normal update can't apply cleanly. "
                "If you haven't made intentional local changes, say *force update* to reset to the latest version.",
            )
        elif status == "dirty":
            _send_slack_message(
                config,
                "There are uncommitted changes to tracked files blocking the update. "
                "Commit or stash them, then try again.",
            )
        else:
            _send_slack_message(config, "Something went wrong with the update — check the logs for details.")
        return True

    elif lowered in ("skip", "skip update", "dismiss update", "not now"):
        if UPDATE_PENDING_PATH.exists():
            UPDATE_PENDING_PATH.unlink(missing_ok=True)
            # Record which remote commit was skipped so we don't re-notify
            branch = config.get("auto_update", {}).get("branch", "main")
            try:
                result = subprocess.run(
                    ["git", "rev-parse", f"origin/{branch}"],
                    capture_output=True, text=True,
                    cwd=str(BASE_DIR), timeout=5,
                )
                if result.returncode == 0:
                    SKIP_MARKER_PATH.write_text(result.stdout.strip())
            except Exception:
                pass
            _send_slack_message(config, "Got it, skipped. I'll let you know when there's something new.")
            return True

    return False


async def update_loop(config: dict) -> None:
    """Periodically check for updates and notify the user."""
    update_cfg = config.get("auto_update", {})
    if not update_cfg.get("enabled", True):
        log("Auto-update disabled in config")
        return

    interval_hours = update_cfg.get("check_interval_hours", 12)
    interval_seconds = interval_hours * 3600

    log(f"Update loop started (interval={interval_hours}h)")

    # Wait before first check so the initial full pulse can complete
    await asyncio.sleep(min(interval_seconds, 300))

    while True:
        try:
            info = check_for_updates(config)
            if info:
                # Check if user already skipped this exact version
                branch = info["branch"]
                skipped = False
                if SKIP_MARKER_PATH.exists():
                    skipped_hash = SKIP_MARKER_PATH.read_text().strip()
                    try:
                        result = subprocess.run(
                            ["git", "rev-parse", f"origin/{branch}"],
                            capture_output=True, text=True,
                            cwd=str(BASE_DIR), timeout=5,
                        )
                        if result.returncode == 0 and result.stdout.strip() == skipped_hash:
                            skipped = True
                    except Exception:
                        pass

                if skipped:
                    log("Update check: skipped (user dismissed this version)")
                else:
                    log(f"Update available: {info['count']} commits on {info['branch']}")
                    UPDATE_PENDING_PATH.write_text(json.dumps(info), encoding="utf-8")
                    notify_update_available(config, info)
            else:
                log("Update check: up to date")
        except Exception as e:
            log(f"Update loop error: {e}")

        await asyncio.sleep(interval_seconds)


async def run_check_pulse(config: dict) -> Optional[dict]:
    """Lightweight check: scan sources for new items using the cheap model.

    Returns the parsed check result dict, or None if check failed.
    The result contains 'recommended_action': 'deep_pulse' or 'none'.
    """
    if not acquire_lock():
        log("PULSE CHECK SKIP: locked")
        return None
    try:
        log("PULSE CHECK START")

        if not PROMPT_CHECK.exists():
            log("PULSE CHECK SKIP: prompt file missing, falling back to deep pulse")
            return {"recommended_action": "deep_pulse"}

        # Pre-compute context so the LLM doesn't need to read any files
        connected = get_connected_sources(config)
        last_pulse = get_last_pulse_time()
        instructions = get_next_pulse_instructions()

        template = PROMPT_CHECK.read_text(encoding="utf-8")
        prompt = (
            template
            .replace("{{CURRENT_TIME}}", current_time_iso(config))
            .replace("{{SLACK_CHANNEL_ID}}", slack_channel(config))
            .replace("{{CONNECTED_SOURCES}}", ", ".join(connected) if connected else "none")
            .replace("{{LAST_PULSE_TIME}}", last_pulse)
            .replace("{{NEXT_PULSE_INSTRUCTIONS}}", instructions)
        )

        check_model = config.get("check_pulse_model", config.get("slack_poll_model", "haiku"))
        output = run_claude(
            prompt, config,
            operation="check_pulse",
            model_override=check_model,
        )

        # Parse JSON from output
        start = output.find("{")
        end = output.rfind("}") + 1
        if start == -1 or end == 0:
            log("PULSE CHECK WARN: no JSON in output, defaulting to deep pulse")
            return {"recommended_action": "deep_pulse"}

        try:
            result = json.loads(output[start:end])
        except json.JSONDecodeError:
            log("PULSE CHECK WARN: invalid JSON, defaulting to deep pulse")
            return {"recommended_action": "deep_pulse"}

        action = result.get("recommended_action", "none")
        new_items = result.get("new_items_total", 0)
        log(f"PULSE CHECK END: new_items={new_items} action={action}")

        # Update Last Pulse timestamp directly — no LLM needed
        update_last_pulse_time(config)

        # Log the check result to JSONL
        append_pulse_update({
            "type": "check",
            "new_items": new_items,
            "action": action,
            "sources": result.get("sources", {}),
            "instruction_results": result.get("instruction_results", []),
        })

        return result

    except Exception as e:
        log(f"PULSE CHECK ERROR: {e}")
        return None
    finally:
        release_lock()


async def run_deep_pulse(config: dict, check_context: Optional[dict] = None) -> None:
    """Full processing pulse — scans sources, updates mind.md, notifies user.

    Called when run_check_pulse finds items to process, or on first run (onboarding).
    If check_context is provided, it's appended to the prompt so the deep pulse
    knows what was already found and can skip re-scanning empty sources.
    """
    if not acquire_lock():
        log("PULSE DEEP SKIP: locked")
        return
    try:
        refresh_mcp_inventory()
        first_run = is_first_run()
        prompt_path = PROMPT_ONBOARDING if (first_run and PROMPT_ONBOARDING.exists()) else PROMPT_FULL
        pulse_type = "onboarding" if first_run and PROMPT_ONBOARDING.exists() else "deep"
        log(f"PULSE DEEP START: type={pulse_type}")
        template = prompt_path.read_text()
        prompt = (
            template
            .replace("{{CURRENT_TIME}}", current_time_iso(config))
            .replace("{{SLACK_CHANNEL_ID}}", slack_channel(config))
        )
        # Inject check results so the deep pulse skips re-scanning empty sources
        if check_context and not first_run:
            prompt += (
                "\n\n## Pre-scan Results (from check pulse)\n"
                "The check pulse already scanned sources and found:\n"
                f"```json\n{json.dumps(check_context, indent=2)}\n```\n"
                "Focus on processing the sources with new items. "
                "Skip re-scanning sources that showed 0 new items.\n"
            )
        output = run_claude(prompt, config, operation="deep_pulse")
        log(f"PULSE DEEP END: output_len={len(output)}")

        append_pulse_update({"type": "deep", "output_len": len(output)})

    except Exception as e:
        log(f"PULSE DEEP ERROR: {e}")
    finally:
        release_lock()


async def run_full_pulse(config: dict) -> None:
    """Backwards-compatible wrapper: runs check → deep two-phase pulse.

    On first run (onboarding), skips check and runs deep pulse directly.
    Used by --once-full CLI flag.
    """
    if is_first_run():
        await run_deep_pulse(config)
        return

    check_result = await run_check_pulse(config)
    if check_result and check_result.get("recommended_action") == "deep_pulse":
        await run_deep_pulse(config, check_result)


async def timer_loop(config: dict) -> None:
    interval_minutes = config.get("full_pulse_interval_minutes", 30)
    interval_seconds = interval_minutes * 60
    log(f"Timer loop started (interval={interval_minutes}min, two-phase: check → deep)")

    # Run immediately on startup
    await run_full_pulse(config)

    while True:
        await asyncio.sleep(interval_seconds)
        await run_full_pulse(config)


HEARTBEAT_PATH = BASE_DIR / "logs" / ".heartbeat"


async def heartbeat_loop() -> None:
    """Write a heartbeat timestamp every 60s so external tools can detect if pulse is alive."""
    while True:
        try:
            HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
            HEARTBEAT_PATH.write_text(datetime.now().isoformat())
        except Exception:
            pass
        await asyncio.sleep(60)


async def consolidation_loop(config: dict) -> None:
    """Periodically merge JSONL pulse updates into mind.md (every 6h)."""
    interval_hours = config.get("consolidation_interval_hours", 6)
    interval_seconds = interval_hours * 3600
    log(f"Consolidation loop started (interval={interval_hours}h)")

    # Wait before first consolidation
    await asyncio.sleep(interval_seconds)

    while True:
        try:
            run_consolidation()
        except Exception as e:
            log(f"Consolidation loop error: {e}")
        await asyncio.sleep(interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personal companion pulse scheduler")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once-full", action="store_true", help="Run one full pulse and exit.")
    mode.add_argument(
        "--once-reactive",
        metavar="MESSAGE",
        help="Run one reactive pulse with MESSAGE and exit.",
    )
    return parser.parse_args()


def validate_config(config: dict) -> None:
    user_id = str(config.get("slack_user_id", "")).strip()
    if not user_id:
        print("ERROR: slack_user_id is not set in config.yaml. Set it to your Slack user ID (e.g. U01XXXXXXX).", flush=True)
        sys.exit(1)
    # Warn if timezone is UTC but system timezone differs
    tz = str(config.get("timezone", "")).strip()
    if tz == "UTC" or not tz:
        try:
            link = os.readlink("/etc/localtime")
            detected = link.split("zoneinfo/")[-1] if "zoneinfo/" in link else ""
            if detected and detected != "UTC":
                log(f"WARNING: timezone is UTC but your system timezone is {detected}. "
                    f"Update config.yaml timezone to '{detected}' for accurate scheduling.")
        except Exception:
            pass


def slack_channel(config: dict) -> str:
    """Returns the channel to post to and listen on. Defaults to slack_user_id."""
    return str(config.get("slack_channel_id", "")).strip() or str(config.get("slack_user_id", "")).strip()


async def main(args: argparse.Namespace) -> None:
    ensure_runtime_files()
    config = load_config()
    config = migrate_config(config)
    validate_config(config)
    log("Pulse starting up")

    # Record current commit for rollback safety
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True,
            cwd=str(BASE_DIR), timeout=5,
        )
        if result.returncode == 0:
            LAST_GOOD_COMMIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            LAST_GOOD_COMMIT_PATH.write_text(result.stdout.strip())
    except Exception:
        pass

    # Ensure lock is clear on startup (stale lock from previous crash)
    if LOCK_PATH.exists():
        log("Clearing stale lock file")
        release_lock()

    if args.once_full:
        await run_full_pulse(config)
        return

    if args.once_reactive is not None:
        await run_reactive_pulse(config, args.once_reactive)
        return

    await asyncio.gather(
        timer_loop(config),
        slack_loop(config),
        update_loop(config),
        heartbeat_loop(),
        consolidation_loop(config),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main(parse_args()))
    except KeyboardInterrupt:
        log("Pulse stopped")
        release_lock()
        sys.exit(0)
