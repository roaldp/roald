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
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
MIND_PATH = BASE_DIR / "mind.md"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
KNOWLEDGE_INDEX_PATH = KNOWLEDGE_DIR / "index.md"
LOCK_PATH = BASE_DIR / "logs" / ".pulse_lock"
LOG_PATH = BASE_DIR / "logs" / "pulse.log"
PROMPT_FULL = BASE_DIR / "prompts" / "pulse_full.md"
PROMPT_REACTIVE = BASE_DIR / "prompts" / "pulse_reactive.md"
TEMPLATES_DIR = BASE_DIR / "templates"
MIND_TEMPLATE_PATH = TEMPLATES_DIR / "mind.template.md"
KNOWLEDGE_INDEX_TEMPLATE_PATH = TEMPLATES_DIR / "knowledge_index.template.md"

ALLOWED_TOOLS = (
    "Read,Edit,MultiEdit,Write,Glob,Grep,"
    "mcp__claude_ai_Slack__*,"
    "mcp__claude_ai_Gmail__*,"
    "mcp__claude_ai_Fireflies__*,"
    "mcp__claude_ai_Google_Calendar__*"
)

SLACK_OUTBOUND_TOOLS = {
    "mcp__claude_ai_Slack__slack_send_message",
    "mcp__claude_ai_Slack__slack_schedule_message",
}


def is_claude_echo_message(text: str) -> bool:
    lowered = text.lower()
    # In this workspace, Slack messages sent by Claude are echoed back in the DM
    # and often include "Sent using <@...|Claude>" markup.
    return "sent using" in lowered and "claude" in lowered


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


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
    log(f"EXEC START: {operation}")
    started = time.monotonic()
    cmd = [
        config.get("claude_command", "claude"),
        "-p", prompt,
        "--allowedTools", allowed_tools,
        "--output-format", "stream-json",
        "--verbose",
    ]
    model = config.get("claude_model", "")
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
    channel_id = config.get("slack_dm_channel_id", "")
    user_id = str(config.get("slack_user_id", "")).strip()
    if not channel_id:
        log("slack_dm_channel_id not set — skipping Slack listener")
        return

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
            .replace("{{SLACK_DM_CHANNEL_ID}}", config.get("slack_dm_channel_id", ""))
        )
        output = run_claude(prompt, config, operation="reactive_pulse")
        log(f"Reactive pulse complete. Output length: {len(output)} chars")
    except Exception as e:
        log(f"Reactive pulse error: {e}")
    finally:
        release_lock()


async def run_full_pulse(config: dict) -> None:
    if not acquire_lock():
        log("Full pulse skipped — another pulse is running")
        return
    try:
        log("Running full pulse...")
        template = PROMPT_FULL.read_text()
        prompt = (
            template
            .replace("{{CURRENT_TIME}}", current_time_iso(config))
            .replace("{{SLACK_DM_CHANNEL_ID}}", config.get("slack_dm_channel_id", ""))
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


async def main(args: argparse.Namespace) -> None:
    ensure_runtime_files()
    config = load_config()
    log("Pulse starting up")

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
    )


if __name__ == "__main__":
    try:
        asyncio.run(main(parse_args()))
    except KeyboardInterrupt:
        log("Pulse stopped")
        release_lock()
        sys.exit(0)
