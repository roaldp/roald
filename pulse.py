#!/usr/bin/env python3
"""pulse.py — Event loop for a personal AI companion."""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, TypedDict
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
LOG_PATH = BASE_DIR / "logs" / "pulse.log"
DETAIL_LOG_PATH = BASE_DIR / "logs" / "pulse_detail.jsonl"
RESTART_EXIT_CODE = 42
PROMPT_FULL = BASE_DIR / "prompts" / "pulse_full.md"
PROMPT_ONBOARDING = BASE_DIR / "prompts" / "pulse_onboarding.md"
PROMPT_REACTIVE = BASE_DIR / "prompts" / "pulse_reactive.md"
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


# ============================================================================
# DETAIL LOGGING TYPES
# ============================================================================

class ToolCallMetrics(TypedDict):
    tool_id: str
    tool_name: str
    input_chars: int
    subagent_type: Optional[str]
    subagent_description: Optional[str]


class ToolResultMetrics(TypedDict):
    tool_id: str
    tool_name: str
    result_chars: int
    result_est_tokens: int
    is_error: bool


class TurnMetrics(TypedDict):
    turn: int
    role: str
    input_tokens: int
    input_tokens_delta: Optional[int]
    output_tokens: int
    cache_creation: int
    cache_read: int
    tool_calls: list[ToolCallMetrics]
    tool_results: list[ToolResultMetrics]


class SubAgentMetrics(TypedDict):
    tool_id: str
    subagent_type: str
    model: Optional[str]
    turns: int
    tool_calls: list[str]
    result_chars: int


class PulseDetailRecord(TypedDict):
    v: int
    rid: str
    ts: str
    op: str
    model: str
    dur_s: float
    num_turns: int
    total_cost_usd: float
    prompt_chars: int
    prompt_est_tokens: int
    system_tools_count: int
    system_mcp_servers: list[str]
    usage: dict
    model_usage: dict
    subagents: list[SubAgentMetrics]
    tools_summary: list[dict]
    turns: Optional[list[TurnMetrics]]


# ============================================================================
# DETAIL LOGGING HELPERS
# ============================================================================

def _estimate_tokens(text: str) -> int:
    """Estimate token count from text using chars/4 heuristic.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Approximate token count.
    """
    return len(text) // 4


def _build_tools_summary(
    tool_calls_map: dict[str, dict],
    tool_results_list: list[ToolResultMetrics],
) -> list[dict]:
    """Aggregate per-tool metrics from collected tool calls and results.

    Args:
        tool_calls_map: Dict of tool_id -> {name, input, input_chars}.
        tool_results_list: List of all ToolResultMetrics collected.

    Returns:
        List of per-tool summary dicts sorted by total_result_chars descending.
    """
    summary: dict[str, dict] = {}
    for tc in tool_calls_map.values():
        name = tc.get("name", "unknown_tool")
        if name not in summary:
            summary[name] = {
                "tool_name": name,
                "call_count": 0,
                "total_input_chars": 0,
                "total_result_chars": 0,
                "total_result_est_tokens": 0,
                "error_count": 0,
            }
        summary[name]["call_count"] += 1
        summary[name]["total_input_chars"] += tc.get("input_chars", 0)

    for tr in tool_results_list:
        name = tr["tool_name"]
        if name not in summary:
            summary[name] = {
                "tool_name": name,
                "call_count": 0,
                "total_input_chars": 0,
                "total_result_chars": 0,
                "total_result_est_tokens": 0,
                "error_count": 0,
            }
        summary[name]["total_result_chars"] += tr["result_chars"]
        summary[name]["total_result_est_tokens"] += tr["result_est_tokens"]
        if tr["is_error"]:
            summary[name]["error_count"] += 1

    return sorted(summary.values(), key=lambda s: s["total_result_chars"], reverse=True)


def _write_detail_record(record: PulseDetailRecord) -> None:
    """Append a detail record as a JSON line to pulse_detail.jsonl.

    Args:
        record: The PulseDetailRecord to write.
    """
    try:
        DETAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DETAIL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception as e:
        print(f"[{now_str()}] DETAIL LOG ERROR: {e}", flush=True)


def _measure_content_chars(content: object) -> int:
    """Measure the character size of tool result content.

    Args:
        content: Content from a tool_result block (string or list of blocks).

    Returns:
        Total character count.
    """
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, str):
                total += len(block)
            elif isinstance(block, dict) and "text" in block:
                total += len(block["text"])
        return total
    return 0


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
) -> str:
    """Run a Claude CLI invocation, parse stream-json events, and log detail metrics.

    Args:
        prompt: The prompt text to send to Claude.
        config: Configuration dictionary.
        allowed_tools: Comma-separated list of allowed tool patterns.
        operation: Name of the operation (for logging).

    Returns:
        The result text from Claude's response.
    """
    log(f"EXEC START: {operation}")
    started = time.monotonic()
    prompt_chars = len(prompt)
    cmd = [
        config.get("claude_command", "claude"),
        "-p", prompt,
        "--allowedTools", allowed_tools,
        "--output-format", "stream-json",
        "--verbose",
    ]
    model_config = config.get("claude_model", "")
    if model_config:
        cmd += ["--model", model_config]
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

    # --- Parse stream-json events ---
    result_text = ""
    tool_calls: dict[str, dict] = {}
    tool_starts = 0
    tool_ends = 0

    # Detail metrics collectors
    turns_list: list[TurnMetrics] = []
    all_tool_results: list[ToolResultMetrics] = []
    system_tools_count = 0
    system_mcp_servers: list[str] = []
    system_model = ""
    result_cost_usd = 0.0
    result_duration_ms = 0
    result_num_turns = 0
    result_usage: dict = {}
    result_model_usage: dict = {}
    turn_counter = 0
    prev_assistant_input_tokens = 0

    # Sub-agent tracking
    subagent_stack: list[dict] = []  # stack of {tool_id, subagent_type, description, model, turns, tool_calls, result_chars}
    pending_agent_tool_ids: set[str] = set()  # Agent tool_use IDs awaiting system init
    completed_subagents: list[SubAgentMetrics] = []

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")

        if event_type == "system":
            subtype = event.get("subtype")
            if subtype == "init":
                event_model = event.get("model")
                if event_model is None and pending_agent_tool_ids:
                    # Sub-agent init — push onto stack
                    # Pick the most recent pending agent tool_id
                    agent_tid = next(iter(pending_agent_tool_ids))
                    pending_agent_tool_ids.discard(agent_tid)
                    agent_info = tool_calls.get(agent_tid, {})
                    agent_input = agent_info.get("input", {})
                    subagent_stack.append({
                        "tool_id": agent_tid,
                        "subagent_type": str(agent_input.get("type", agent_input.get("subagent_type", "unknown"))),
                        "description": str(agent_input.get("description", agent_input.get("prompt", "")))[:200],
                        "model": None,
                        "turns": 0,
                        "tool_calls": [],
                        "result_chars": 0,
                    })
                elif event_model is not None and not system_model:
                    # Parent init
                    system_model = str(event_model)
                    tools = event.get("tools", [])
                    system_tools_count = len(tools)
                    mcp_servers = event.get("mcp_servers", [])
                    system_mcp_servers = [
                        f"{s.get('name', '?')}:{s.get('status', '?')}"
                        for s in mcp_servers
                    ]

        elif event_type == "assistant":
            message = event.get("message", {})
            usage = message.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cache_creation = usage.get("cache_creation_input_tokens", 0)
            cache_read = usage.get("cache_read_input_tokens", 0)

            # Collect tool_use blocks
            turn_tool_calls: list[ToolCallMetrics] = []
            for block in message.get("content", []):
                if block.get("type") != "tool_use":
                    continue
                tool_name = str(block.get("name", "unknown_tool"))
                tool_id = str(block.get("id", ""))
                tool_input = block.get("input", {})
                input_json = json.dumps(tool_input, separators=(",", ":"))
                input_chars = len(input_json)
                tool_calls[tool_id] = {"name": tool_name, "input": tool_input, "input_chars": input_chars}
                tool_starts += 1
                log(f"TOOL START: {tool_name} input={_short_json(tool_input)}")
                if tool_name in SLACK_OUTBOUND_TOOLS:
                    channel = tool_input.get("channel_id", "?")
                    text_preview = tool_input.get("text") or tool_input.get("message") or ""
                    log(
                        "SLACK OUTBOUND START: "
                        f"channel={channel} tool={tool_name} text={_short_text(text_preview)}"
                    )

                subagent_type = None
                subagent_description = None
                if tool_name == "Agent":
                    subagent_type = str(tool_input.get("type", tool_input.get("subagent_type", "unknown")))
                    subagent_description = str(tool_input.get("description", tool_input.get("prompt", "")))[:200]
                    pending_agent_tool_ids.add(tool_id)

                turn_tool_calls.append(ToolCallMetrics(
                    tool_id=tool_id,
                    tool_name=tool_name,
                    input_chars=input_chars,
                    subagent_type=subagent_type,
                    subagent_description=subagent_description,
                ))

                # Track sub-agent tool calls
                if subagent_stack:
                    subagent_stack[-1]["tool_calls"].append(tool_name)

            # Track sub-agent turns
            if subagent_stack:
                subagent_stack[-1]["turns"] += 1

            turn_counter += 1
            input_delta = input_tokens - prev_assistant_input_tokens if prev_assistant_input_tokens > 0 else None
            prev_assistant_input_tokens = input_tokens

            turns_list.append(TurnMetrics(
                turn=turn_counter,
                role="assistant",
                input_tokens=input_tokens,
                input_tokens_delta=input_delta,
                output_tokens=output_tokens,
                cache_creation=cache_creation,
                cache_read=cache_read,
                tool_calls=turn_tool_calls,
                tool_results=[],
            ))

        elif event_type == "user":
            message = event.get("message", {})
            turn_tool_results: list[ToolResultMetrics] = []
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

                # Measure tool result content size
                content = block.get("content", "")
                result_chars = _measure_content_chars(content)

                tr = ToolResultMetrics(
                    tool_id=tool_id,
                    tool_name=tool_name,
                    result_chars=result_chars,
                    result_est_tokens=_estimate_tokens(str(content)),
                    is_error=is_error,
                )
                turn_tool_results.append(tr)
                all_tool_results.append(tr)

                # Check if this tool_result closes a sub-agent
                if subagent_stack and tool_id == subagent_stack[-1]["tool_id"]:
                    sa = subagent_stack.pop()
                    sa["result_chars"] = result_chars
                    completed_subagents.append(SubAgentMetrics(
                        tool_id=sa["tool_id"],
                        subagent_type=sa["subagent_type"],
                        model=sa["model"],
                        turns=sa["turns"],
                        tool_calls=sa["tool_calls"],
                        result_chars=sa["result_chars"],
                    ))

            turn_counter += 1
            turns_list.append(TurnMetrics(
                turn=turn_counter,
                role="user",
                input_tokens=0,
                input_tokens_delta=None,
                output_tokens=0,
                cache_creation=0,
                cache_read=0,
                tool_calls=[],
                tool_results=turn_tool_results,
            ))

        elif event_type == "result":
            result_text = str(event.get("result", ""))
            result_cost_usd = float(event.get("cost_usd", 0) or event.get("total_cost_usd", 0) or 0)
            result_duration_ms = int(event.get("duration_ms", 0) or 0)
            result_num_turns = int(event.get("num_turns", 0) or 0)
            result_usage = event.get("usage", {})
            # Build model_usage from result event
            raw_model_usage = event.get("modelUsage", {})
            result_model_usage = {}
            for m_name, m_data in raw_model_usage.items():
                result_model_usage[m_name] = {
                    "input_tokens": m_data.get("inputTokens", 0),
                    "output_tokens": m_data.get("outputTokens", 0),
                    "cache_read": m_data.get("cacheReadInputTokens", 0),
                    "cache_creation": m_data.get("cacheCreationInputTokens", 0),
                    "cost_usd": m_data.get("costUSD", 0.0),
                }

    elapsed = time.monotonic() - started
    log(f"EXEC END: {operation} ({elapsed:.1f}s, tools started={tool_starts}, tools ended={tool_ends})")

    # --- Write detail record ---
    detail_enabled = config.get("detail_logging", True)
    now = datetime.now()
    record = PulseDetailRecord(
        v=1,
        rid=now.strftime("%Y%m%dT%H%M%S"),
        ts=now.isoformat(),
        op=operation,
        model=system_model or str(model_config),
        dur_s=round(elapsed, 2),
        num_turns=result_num_turns or turn_counter,
        total_cost_usd=result_cost_usd,
        prompt_chars=prompt_chars,
        prompt_est_tokens=_estimate_tokens(prompt),
        system_tools_count=system_tools_count,
        system_mcp_servers=system_mcp_servers,
        usage={
            "input_tokens": result_usage.get("input_tokens", 0),
            "output_tokens": result_usage.get("output_tokens", 0),
            "cache_creation": result_usage.get("cache_creation_input_tokens", 0),
            "cache_read": result_usage.get("cache_read_input_tokens", 0),
        },
        model_usage=result_model_usage,
        subagents=completed_subagents,
        tools_summary=_build_tools_summary(tool_calls, all_tool_results),
        turns=turns_list if detail_enabled else None,
    )
    _write_detail_record(record)

    return result_text


def poll_slack_messages(config: dict, channel_id: str) -> list[dict]:
    prompt = (
        f"Use slack_read_channel to read the last 5 messages from channel {channel_id}. "
        "Return ONLY a JSON array of objects with fields: ts, user, text. No other text."
    )
    text = run_claude(
        prompt,
        config,
        allowed_tools="mcp__claude_ai_Slack__slack_read_channel",
        operation=f"poll_slack_messages[{channel_id}]",
    )
    # Extract JSON array from the response text
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return []


async def slack_loop(config: dict) -> None:
    interval = config.get("slack_poll_interval_seconds", 5)
    user_id = str(config.get("slack_user_id", "")).strip()
    channel_id = slack_channel(config)

    last_ts: Optional[str] = None
    log(f"Slack listener started (channel={channel_id}, interval={interval}s)")

    while True:
        await asyncio.sleep(interval)
        try:
            messages = poll_slack_messages(config, channel_id)
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
                    # Avoid triggering reactive pulses on bot/app messages.
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
                await run_reactive_pulse(config, user_text)

            last_ts = newest_ts

        except Exception as e:
            log(f"Slack loop error: {e}")


async def run_reactive_pulse(config: dict, user_message: str) -> None:
    if not acquire_lock():
        log("Reactive pulse skipped — another pulse is running")
        return
    try:
        log("Running reactive pulse...")
        template = PROMPT_REACTIVE.read_text()
        prompt = (
            template
            .replace("{{CURRENT_TIME}}", current_time_iso(config))
            .replace("{{USER_MESSAGE}}", user_message)
            .replace("{{SLACK_CHANNEL_ID}}", slack_channel(config))
        )
        output = run_claude(prompt, config, operation="reactive_pulse")
        log(f"Reactive pulse complete. Output length: {len(output)} chars")
    except Exception as e:
        log(f"Reactive pulse error: {e}")
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

def check_for_updates(config: dict) -> dict | None:
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


async def run_full_pulse(config: dict) -> None:
    if not acquire_lock():
        log("Full pulse skipped — another pulse is running")
        return
    try:
        refresh_mcp_inventory()
        first_run = is_first_run()
        prompt_path = PROMPT_ONBOARDING if (first_run and PROMPT_ONBOARDING.exists()) else PROMPT_FULL
        log(f"Running {'onboarding' if first_run and PROMPT_ONBOARDING.exists() else 'full'} pulse...")
        template = prompt_path.read_text()
        prompt = (
            template
            .replace("{{CURRENT_TIME}}", current_time_iso(config))
            .replace("{{SLACK_CHANNEL_ID}}", slack_channel(config))
        )
        output = run_claude(prompt, config, operation="full_pulse")
        log(f"Full pulse complete. Output length: {len(output)} chars")
    except Exception as e:
        log(f"Full pulse error: {e}")
    finally:
        release_lock()


async def timer_loop(config: dict) -> None:
    interval_minutes = config.get("full_pulse_interval_minutes", 30)
    interval_seconds = interval_minutes * 60
    log(f"Timer loop started (interval={interval_minutes}min)")

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
    )


if __name__ == "__main__":
    try:
        asyncio.run(main(parse_args()))
    except KeyboardInterrupt:
        log("Pulse stopped")
        release_lock()
        sys.exit(0)
