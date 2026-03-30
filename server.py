#!/usr/bin/env python3
"""Lightweight chat API server for workspace conversations.

Self-contained — does not import pulse.py (which requires Python 3.10+).
Includes its own run_claude() and config loading.

Usage:
    python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
    python3 server.py
"""

import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure dependencies
for pkg in ["fastapi", "uvicorn", "pyyaml"]:
    try:
        __import__(pkg.replace("pyyaml", "yaml"))
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg],
            stdout=subprocess.DEVNULL,
        )

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Paths & constants (mirrors pulse.py but self-contained)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
MIND_PATH = BASE_DIR / "mind.md"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
CONTEXTS_DIR = BASE_DIR / "contexts"
LOG_PATH = BASE_DIR / "logs" / "pulse.log"
CONVERSATIONS_DIR = BASE_DIR / "conversations"
PROMPTS_DIR = BASE_DIR / "prompts"

# Pre-approve all MCP tools so they execute without interactive prompts.
# Each entry is passed as a separate arg to --allowedTools (variadic flag).
ALLOWED_TOOLS = ["Read", "Edit", "MultiEdit", "Write", "Glob", "Grep", "mcp__*"]

WORKSPACE_PROMPTS = {
    "ws-dealflow": "prompts/dd.md",
    "ws-dc": "prompts/sourcing.md",
    "ws-fundops": "prompts/relations.md",
    "ws-portfolio": "prompts/relations.md",
    "ws-email": None,
    "ws-tasks": None,
}

# Workspace-specific context files (curated, workspace-scoped data)
WORKSPACE_CONTEXTS = {
    "ws-dealflow": "contexts/dealflow.md",
    "ws-dc": "contexts/dc.md",
    "ws-fundops": "contexts/fundops.md",
    "ws-portfolio": "contexts/portfolio.md",
    "ws-email": "contexts/email.md",
    "ws-tasks": "contexts/tasks.md",
}

WORKSPACE_KEYWORDS = {
    # Populate locally in config.yaml or override here.
    # Example: "ws-dealflow": ["company-a", "company-b", "term sheet", "due diligence"],
    "ws-dealflow": ["deal flow", "term sheet", "ic memo", "due diligence", "dd sync", "dd kickoff", "cla"],
    "ws-dc": ["server", "datacenter", "data center", "gpu", "node", "infrastructure"],
    "ws-fundops": ["spv", "fund", "lp", "quarterly", "ruling", "legal", "buyout", "asset purchase"],
    "ws-portfolio": ["portfolio", "founder", "sync", "board"],
    "ws-email": ["email", "inbox", "mail", "reply", "respond"],
}

WORKSPACE_NAMES = {
    "ws-dealflow": "Deal Flow",
    "ws-dc": "DC & Infrastructure",
    "ws-fundops": "Fund Operations",
    "ws-portfolio": "Portfolio & Relations",
    "ws-email": "Email Triage",
    "ws-tasks": "Tasks & Projects",
}

# ---------------------------------------------------------------------------
# Core functions (copied from pulse.py, Python 3.9 compatible)
# ---------------------------------------------------------------------------

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Log levels for filtering
_LOG_LEVELS = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
_MIN_LOG_LEVEL = os.environ.get("ROALD_LOG_LEVEL", "DEBUG").upper()


def log(msg, level="INFO"):
    if _LOG_LEVELS.get(level, 1) < _LOG_LEVELS.get(_MIN_LOG_LEVEL, 0):
        return
    line = "[%s] [%s] %s" % (now_str(), level, msg)
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        log("CONFIG loaded: model=%s, command=%s, timeout=%s" % (
            cfg.get("claude_model", "(default)"),
            cfg.get("claude_command", "claude"),
            cfg.get("claude_timeout_seconds", 300),
        ), "DEBUG")
        return cfg
    except FileNotFoundError:
        log("CONFIG not found at %s — using defaults" % CONFIG_PATH, "WARN")
        return {}


def run_claude(prompt, config, allowed_tools=None, operation="claude_run"):
    """Call claude CLI as subprocess and return the response text."""
    log("EXEC START: %s" % operation)
    log("EXEC prompt_len=%d chars" % len(prompt), "DEBUG")
    started = time.monotonic()
    cmd = [
        config.get("claude_command", "claude"),
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
    ]
    if allowed_tools:
        if isinstance(allowed_tools, list):
            cmd += ["--allowedTools"] + allowed_tools
        else:
            cmd += ["--allowedTools"] + allowed_tools.split(",")
    model = config.get("claude_model", "")
    if model:
        cmd += ["--model", model]

    # Log the exact CLI command (redact prompt for brevity)
    cmd_display = [c if c != prompt else "<PROMPT:%d chars>" % len(prompt) for c in cmd]
    log("EXEC cmd: %s" % " ".join(cmd_display), "DEBUG")

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
        log("EXEC TIMEOUT: %s after %ds" % (operation, timeout_seconds), "ERROR")
        raise RuntimeError("claude timed out after %ds" % timeout_seconds) from e

    log("EXEC exitcode=%d stdout_len=%d stderr_len=%d" % (
        result.returncode, len(result.stdout or ""), len(result.stderr or "")
    ), "DEBUG")

    # Parse stream-json output — log every event type
    result_text = ""
    event_counts = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            log("EXEC non-json line: %s" % line[:200], "DEBUG")
            continue
        etype = event.get("type", "unknown")
        event_counts[etype] = event_counts.get(etype, 0) + 1
        if etype == "result":
            result_text = str(event.get("result", ""))
            denials = event.get("permission_denials", [])
            if denials:
                log("EXEC PERMISSION_DENIALS: %s" % json.dumps(denials, default=str), "WARN")
            log("EXEC result: text_len=%d denials=%d" % (len(result_text), len(denials)), "DEBUG")

    log("EXEC event_counts: %s" % json.dumps(event_counts), "DEBUG")

    # If we got a result, return it even if exitcode was non-zero
    if result_text:
        elapsed = time.monotonic() - started
        log("EXEC END: %s (%.1fs, %d chars)" % (operation, elapsed, len(result_text)))
        return result_text

    # No result found — check for errors
    if result.returncode != 0:
        stderr_text = (result.stderr or "").strip()
        if stderr_text:
            log("EXEC STDERR: %s" % stderr_text[:500], "ERROR")
        stdout_preview = (result.stdout or "")[:400]
        if stdout_preview:
            log("EXEC STDOUT (no result found): %s" % stdout_preview, "ERROR")
        error_detail = stderr_text[:400] if stderr_text else stdout_preview
        raise RuntimeError("claude exited %d: %s" % (result.returncode, error_detail))

    elapsed = time.monotonic() - started
    log("EXEC END: %s (%.1fs, empty response)" % (operation, elapsed), "WARN")
    return result_text


def run_claude_streaming(prompt, config, allowed_tools=None, operation="claude_stream"):
    """Stream claude CLI output via subprocess.Popen, yielding parsed SSE events.

    Yields dicts: {"event": "<type>", "data": {...}}
    Event types: text_delta, tool_use, tool_result, done, error
    """
    log("STREAM START: %s" % operation)
    log("STREAM prompt_len=%d chars" % len(prompt), "DEBUG")
    started = time.monotonic()
    cmd = [
        config.get("claude_command", "claude"),
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
    ]
    if allowed_tools:
        if isinstance(allowed_tools, list):
            cmd += ["--allowedTools"] + allowed_tools
        else:
            cmd += ["--allowedTools"] + allowed_tools.split(",")
    model = config.get("claude_model", "")
    if model:
        cmd += ["--model", model]

    # Log the exact CLI command (redact prompt for brevity)
    cmd_display = [c if c != prompt else "<PROMPT:%d chars>" % len(prompt) for c in cmd]
    log("STREAM cmd: %s" % " ".join(cmd_display), "DEBUG")

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    timeout_seconds = int(config.get("claude_timeout_seconds", 300))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(BASE_DIR),
            env=env,
        )
        _active_procs.add(proc)
        log("STREAM pid=%d" % proc.pid, "DEBUG")
    except Exception as e:
        log("STREAM failed to spawn: %s" % e, "ERROR")
        yield {"event": "error", "data": {"message": str(e)}}
        return

    # Collect stderr in background thread
    stderr_lines = []
    def read_stderr():
        for line in proc.stderr:
            stderr_lines.append(line)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()

    result_text = ""
    full_text_parts = []
    tool_calls = []
    event_counts = {}
    available_tools = []  # tools reported in system event

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                log("STREAM non-json: %s" % line[:200], "DEBUG")
                continue

            event_type = event.get("type", "")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            if event_type == "system":
                # Log system event — contains available tools list
                tools = event.get("tools", [])
                available_tools = [t.get("name", "") for t in tools] if isinstance(tools, list) else []
                log("STREAM SYSTEM: %d tools available: %s" % (
                    len(available_tools),
                    ", ".join(available_tools[:20]) + ("..." if len(available_tools) > 20 else "")
                ))
                mcp_tools = [t for t in available_tools if t.startswith("mcp__")]
                if mcp_tools:
                    log("STREAM MCP tools: %s" % ", ".join(mcp_tools), "DEBUG")
                # Log allowed vs available
                if allowed_tools:
                    tools_arg = allowed_tools if isinstance(allowed_tools, list) else allowed_tools.split(",")
                    log("STREAM allowedTools passed: %s" % tools_arg, "DEBUG")

            elif event_type == "assistant":
                message = event.get("message", {})
                content_blocks = message.get("content", [])
                log("STREAM assistant: %d content blocks" % len(content_blocks), "DEBUG")
                for block in content_blocks:
                    block_type = block.get("type", "")
                    if block_type == "text":
                        text = block.get("text", "")
                        full_text_parts.append(text)
                        yield {"event": "text_delta", "data": {"content": text}}
                    elif block_type == "tool_use":
                        tool_call = {
                            "id": block.get("id", "tu-%s" % uuid.uuid4().hex[:8]),
                            "name": block.get("name", ""),
                            "input": block.get("input", {}),
                            "status": "proposed",
                        }
                        tool_calls.append(tool_call)
                        log("STREAM TOOL_USE: %s → %s" % (tool_call["id"], tool_call["name"]))
                        log("STREAM TOOL_USE input: %s" % json.dumps(tool_call["input"], default=str)[:500], "DEBUG")
                        yield {"event": "tool_use", "data": tool_call}
                    elif block_type == "tool_result":
                        content = str(block.get("content", ""))
                        is_error = block.get("is_error", False)
                        tool_use_id = block.get("tool_use_id", "")
                        log("STREAM TOOL_RESULT: id=%s is_error=%s len=%d" % (
                            tool_use_id, is_error, len(content)
                        ))
                        log("STREAM TOOL_RESULT preview: %s" % content[:300], "DEBUG")
                        # Detect errors from content even if is_error is False
                        content_lower = content.lower()
                        detected_error = is_error or any(err in content_lower for err in [
                            "error", "permission denied", "unauthorized", "forbidden",
                            "auth", "token expired", "not authenticated", "access denied",
                        ])
                        if detected_error and not is_error:
                            log("STREAM TOOL_RESULT content-based error detected (is_error was False)", "WARN")
                        # Update the matching tool call status
                        for tc in tool_calls:
                            if tc["id"] == tool_use_id:
                                tc["status"] = "error" if detected_error else "executed"
                                tc["result"] = content
                                log("STREAM TOOL_STATUS: %s → %s" % (tc["name"], tc["status"]))
                        yield {"event": "tool_result", "data": {
                            "tool_use_id": tool_use_id,
                            "content": content,
                            "is_error": detected_error,
                        }}

            elif event_type == "result":
                result_text = str(event.get("result", ""))
                # Check for permission denials
                denials = event.get("permission_denials", [])
                if denials:
                    log("STREAM PERMISSION_DENIALS: %s" % json.dumps(denials, default=str), "WARN")
                    for d in denials:
                        log("STREAM DENIED tool=%s id=%s" % (
                            d.get("tool_name", "?"), d.get("tool_use_id", "?")
                        ), "WARN")
                for denial in denials:
                    tool_call = {
                        "id": "denied-%s" % uuid.uuid4().hex[:8],
                        "name": denial.get("tool_name", "unknown"),
                        "input": denial.get("tool_input", {}),
                        "status": "needs_approval",
                    }
                    tool_calls.append(tool_call)
                    yield {"event": "tool_use", "data": tool_call}
                log("STREAM RESULT: text_len=%d denials=%d tool_calls=%d" % (
                    len(result_text), len(denials), len(tool_calls)
                ))

            elif event_type == "rate_limit_event":
                log("STREAM RATE_LIMIT: %s" % json.dumps(event, default=str)[:300], "WARN")

            elif event_type not in ("stream_event",):
                # Log any other unexpected event types
                log("STREAM event type=%s: %s" % (event_type, json.dumps(event, default=str)[:300]), "DEBUG")

    except Exception as e:
        log("STREAM exception during read: %s" % e, "ERROR")
        yield {"event": "error", "data": {"message": str(e)}}

    # Wait for process to finish
    try:
        proc.wait(timeout=timeout_seconds)
        log("STREAM proc exited code=%d" % proc.returncode, "DEBUG")
    except subprocess.TimeoutExpired:
        proc.kill()
        log("STREAM TIMEOUT: killed after %ds" % timeout_seconds, "ERROR")
        yield {"event": "error", "data": {"message": "claude timed out"}}
        _active_procs.discard(proc)
        return

    _active_procs.discard(proc)
    stderr_thread.join(timeout=2)
    if stderr_lines:
        stderr_text = "".join(stderr_lines)[:1000]
        log("STREAM STDERR: %s" % stderr_text, "WARN" if "error" in stderr_text.lower() else "DEBUG")

    # Use result_text if available, otherwise join text parts
    final_text = result_text if result_text else "".join(full_text_parts)

    elapsed = time.monotonic() - started
    log("STREAM END: %s (%.1fs, text=%d chars, tools=%d, events=%s)" % (
        operation, elapsed, len(final_text), len(tool_calls), json.dumps(event_counts)
    ))

    yield {"event": "done", "data": {
        "text": final_text,
        "toolCalls": tool_calls,
    }}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return ""


def parse_sections(text):
    """Split markdown by ## headers into {section_name: content}."""
    sections = {}
    current = None
    lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def filter_lines_by_keywords(text, keywords):
    """Filter text lines, keeping only those matching at least one keyword.
    Returns empty string if no keywords or no matches."""
    if not keywords or not text.strip():
        return ""
    lines = text.splitlines()
    matching = [l for l in lines if any(kw in l.lower() for kw in keywords)]
    return "\n".join(matching)


def get_workspace_context(workspace_id):
    """Build workspace-specific context from context files, mind.md, and knowledge."""
    log("CONTEXT building for ws=%s" % workspace_id, "DEBUG")
    keywords = WORKSPACE_KEYWORDS.get(workspace_id, [])
    log("CONTEXT keywords=%s" % keywords, "DEBUG")
    context_parts = []
    sources = []  # track where context came from

    # 1. Workspace-specific context file (primary source of workspace data)
    context_file = WORKSPACE_CONTEXTS.get(workspace_id)
    if context_file:
        context_path = BASE_DIR / context_file
        context_content = read_file(context_path)
        if context_content.strip():
            context_parts.append(context_content.strip())
            sources.append("context_file:%s (%d chars)" % (context_file, len(context_content)))
        else:
            log("CONTEXT file empty or missing: %s" % context_path, "DEBUG")

    # 2. Workspace prompt/playbook (agent behavior)
    prompt_file = WORKSPACE_PROMPTS.get(workspace_id)
    if prompt_file:
        prompt_path = BASE_DIR / prompt_file
        prompt_content = read_file(prompt_path)
        if prompt_content.strip():
            context_parts.append("## Agent Playbook\n%s" % prompt_content.strip())
            sources.append("playbook:%s (%d chars)" % (prompt_file, len(prompt_content)))

    # 3. mind.md — filter ALL sections by workspace keywords
    mind_text = read_file(MIND_PATH)
    if mind_text.strip() and keywords:
        sections = parse_sections(mind_text)
        log("CONTEXT mind.md sections: %s" % list(sections.keys()), "DEBUG")
        mind_matches = 0
        for section_name in [
            "Last Pulse", "Active Context", "Pending Tasks",
            "Recent Events", "Inbox Zero Tracker",
        ]:
            if section_name in sections:
                content = sections[section_name].strip()
                if not content or content.startswith("_No "):
                    continue
                filtered = filter_lines_by_keywords(content, keywords)
                if filtered:
                    context_parts.append("## %s\n%s" % (section_name, filtered))
                    mind_matches += 1
        if mind_matches:
            sources.append("mind.md (%d sections matched)" % mind_matches)

        # Preferences are generic — only include if no workspace context file
        if not context_file and "Preferences" in sections:
            pref = sections["Preferences"].strip()
            if pref and not pref.startswith("_No "):
                context_parts.append("## Preferences\n%s" % pref)
    elif not keywords:
        log("CONTEXT no keywords for ws=%s, skipping mind.md filtering" % workspace_id, "DEBUG")

    # 4. Knowledge index entries matching keywords
    knowledge_index = read_file(KNOWLEDGE_DIR / "index.md")
    if knowledge_index.strip() and keywords:
        index_lines = knowledge_index.splitlines()
        relevant = [l for l in index_lines if any(kw in l.lower() for kw in keywords)]
        if relevant:
            context_parts.append("## Relevant Knowledge\n%s" % "\n".join(relevant[:20]))
            sources.append("knowledge (%d entries)" % len(relevant))

    total_len = sum(len(p) for p in context_parts)
    log("CONTEXT result: %d parts, %d chars, sources=[%s]" % (
        len(context_parts), total_len, ", ".join(sources) if sources else "none"
    ))

    if not context_parts:
        log("CONTEXT empty for ws=%s" % workspace_id, "WARN")
        return "(No context available for this workspace. Check contexts/%s)" % workspace_id

    return "\n\n".join(context_parts)


def format_conversation_history(messages):
    """Format conversation history for prompt inclusion."""
    if not messages:
        return ""
    parts = []
    for msg in messages[-20:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        parts.append("%s: %s" % (role, msg["content"]))
    return "\n\n".join(parts)


def load_conversation(ws_id, thread_id):
    path = CONVERSATIONS_DIR / ws_id / ("%s.jsonl" % thread_id)
    if not path.exists():
        log("CONV load %s/%s: file not found" % (ws_id, thread_id), "DEBUG")
        return []
    messages = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if line.strip():
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError as e:
                log("CONV load %s/%s: bad json line: %s" % (ws_id, thread_id, e), "WARN")
    log("CONV load %s/%s: %d messages" % (ws_id, thread_id, len(messages)), "DEBUG")
    return messages


def append_message(ws_id, thread_id, message):
    dir_path = CONVERSATIONS_DIR / ws_id
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / ("%s.jsonl" % thread_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")
    role = message.get("role", "?")
    content_len = len(message.get("content", ""))
    tool_count = len(message.get("toolCalls", []))
    log("CONV append %s/%s: role=%s content=%d chars tools=%d" % (
        ws_id, thread_id, role, content_len, tool_count
    ), "DEBUG")


def list_threads(ws_id):
    dir_path = CONVERSATIONS_DIR / ws_id
    if not dir_path.is_dir():
        return [{"threadId": "main", "label": "Main", "messageCount": 0}]

    threads = []
    for f in sorted(dir_path.glob("*.jsonl")):
        thread_id = f.stem
        line_count = sum(1 for line in f.open(encoding="utf-8") if line.strip())
        label = "Main" if thread_id == "main" else thread_id.replace("thread-", "").replace("-", " ").title()
        threads.append({
            "threadId": thread_id,
            "label": label,
            "messageCount": line_count,
        })

    if not any(t["threadId"] == "main" for t in threads):
        threads.insert(0, {"threadId": "main", "label": "Main", "messageCount": 0})

    return threads


def make_message(role, content):
    return {
        "id": "msg-%s" % uuid.uuid4().hex[:12],
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(title="Workspace Chat API")

log("=" * 60)
log("SERVER starting — Workspace Chat API")
log("SERVER base_dir=%s" % BASE_DIR)
log("SERVER log_path=%s" % LOG_PATH)
log("SERVER log_level=%s" % _MIN_LOG_LEVEL)
log("SERVER workspaces: %s" % list(WORKSPACE_NAMES.keys()))
log("SERVER allowedTools: %s" % ALLOWED_TOOLS)
log("SERVER config_path=%s (exists=%s)" % (CONFIG_PATH, CONFIG_PATH.exists()))
log("=" * 60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    workspaceId: str
    threadId: str = "main"
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Send a message and get an agent response."""
    log("API POST /api/chat ws=%s thread=%s msg_len=%d" % (req.workspaceId, req.threadId, len(req.message)))
    config = load_config()

    history = load_conversation(req.workspaceId, req.threadId)
    log("API chat history: %d messages" % len(history), "DEBUG")

    ws_name = WORKSPACE_NAMES.get(req.workspaceId, req.workspaceId)
    context = get_workspace_context(req.workspaceId)
    history_text = format_conversation_history(history)

    prompt = (
        "You are the %s workspace agent — an AI companion for the user.\n"
        "You are having a conversation with the user. Be concise, professional, and action-oriented.\n"
        "You have access to tools (Slack, Gmail, Calendar, etc.) and they are PRE-APPROVED — use them directly when the user asks.\n"
        "Do NOT ask for permission or approval to use tools. Just use them and report the result.\n"
        "When reporting status, lead with the most impactful item.\n\n"
        "## Current Workspace Context\n%s\n\n"
        "## Conversation History\n%s\n\n"
        "## Current Message\nUser: %s\n\n"
        "Respond naturally as the workspace agent. Be brief — 2-4 sentences for simple questions, more for complex analysis."
    ) % (ws_name, context, history_text, req.message)

    log("API chat prompt_len=%d (context=%d, history=%d)" % (
        len(prompt), len(context), len(history_text)
    ), "DEBUG")

    user_msg = make_message("user", req.message)
    append_message(req.workspaceId, req.threadId, user_msg)

    try:
        response_text = run_claude(
            prompt, config,
            allowed_tools=ALLOWED_TOOLS,
            operation="chat_%s_%s" % (req.workspaceId, req.threadId),
        )
    except Exception as e:
        log("API chat ERROR: %s" % e, "ERROR")
        error_msg = make_message("assistant", "Error: %s" % str(e))
        append_message(req.workspaceId, req.threadId, error_msg)
        raise HTTPException(status_code=500, detail=str(e))

    assistant_msg = make_message("assistant", response_text)
    append_message(req.workspaceId, req.threadId, assistant_msg)

    log("API chat OK: response_len=%d" % len(response_text))
    return {"threadId": req.threadId, "message": assistant_msg}


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """SSE streaming endpoint: streams agent response events to frontend."""
    log("API POST /api/chat/stream ws=%s thread=%s msg_len=%d" % (req.workspaceId, req.threadId, len(req.message)))
    config = load_config()

    history = load_conversation(req.workspaceId, req.threadId)
    log("API stream history: %d messages" % len(history), "DEBUG")

    ws_name = WORKSPACE_NAMES.get(req.workspaceId, req.workspaceId)
    context = get_workspace_context(req.workspaceId)
    history_text = format_conversation_history(history)

    prompt = (
        "You are the %s workspace agent — an AI companion for the user.\n"
        "You are having a conversation with the user. Be concise, professional, and action-oriented.\n\n"
        "IMPORTANT — Tool Usage:\n"
        "You have access to tools (Slack, Gmail, Calendar, file operations, etc.) and they are PRE-APPROVED.\n"
        "When the user asks you to do something, JUST DO IT — do NOT ask for permission or confirmation.\n"
        "Use tools directly, then briefly report what you did and the result.\n"
        "If a tool returns an error, tell the user what went wrong (e.g. 'Gmail returned an auth error — you may need to re-authenticate'). "
        "NEVER ask the user to 'approve' or 'grant permission' — tools are already approved. Errors mean a config/auth issue, not a permission issue.\n"
        "Example: User says 'message someone on Slack about a deadline' → search for channel, send the message, report 'Done — sent a reminder in the channel.'\n\n"
        "## Current Workspace Context\n%s\n\n"
        "## Conversation History\n%s\n\n"
        "## Current Message\nUser: %s\n\n"
        "Respond naturally as the workspace agent. Be brief — 2-4 sentences for simple questions, more for complex analysis."
    ) % (ws_name, context, history_text, req.message)

    log("API stream prompt_len=%d (context=%d, history=%d)" % (
        len(prompt), len(context), len(history_text)
    ), "DEBUG")

    # Persist user message
    user_msg = make_message("user", req.message)
    append_message(req.workspaceId, req.threadId, user_msg)

    def generate():
        final_text = ""
        final_tool_calls = []

        for event in run_claude_streaming(
            prompt, config,
            allowed_tools=ALLOWED_TOOLS,
            operation="stream_%s_%s" % (req.workspaceId, req.threadId),
        ):
            event_name = event["event"]
            event_data = event["data"]

            if event_name == "done":
                final_text = event_data.get("text", "")
                final_tool_calls = event_data.get("toolCalls", [])

            # Yield SSE event
            yield "event: %s\ndata: %s\n\n" % (
                event_name,
                json.dumps(event_data, ensure_ascii=False),
            )

        # Persist assistant message after stream completes
        if final_text or final_tool_calls:
            log("API stream complete: text=%d chars, tools=%d" % (len(final_text), len(final_tool_calls)))
            assistant_msg = make_message("assistant", final_text)
            if final_tool_calls:
                assistant_msg["toolCalls"] = final_tool_calls
            append_message(req.workspaceId, req.threadId, assistant_msg)
        else:
            log("API stream complete: empty response (nothing to persist)", "WARN")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class ApproveRequest(BaseModel):
    workspaceId: str
    threadId: str = "main"
    toolName: str
    toolInput: dict = {}
    approved: bool = True


@app.post("/api/chat/approve")
def approve_tool(req: ApproveRequest):
    """Execute an approved tool action via a focused claude call with --allowedTools."""
    log("API POST /api/chat/approve ws=%s tool=%s approved=%s" % (req.workspaceId, req.toolName, req.approved))
    log("API approve input: %s" % json.dumps(req.toolInput, default=str)[:500], "DEBUG")
    if not req.approved:
        deny_msg = make_message("assistant", "Tool execution skipped.")
        deny_msg["toolCalls"] = [{
            "id": "deny-%s" % uuid.uuid4().hex[:8],
            "name": req.toolName,
            "input": req.toolInput,
            "status": "denied",
        }]
        append_message(req.workspaceId, req.threadId, deny_msg)
        return {"status": "denied", "message": deny_msg}

    config = load_config()
    ws_name = WORKSPACE_NAMES.get(req.workspaceId, req.workspaceId)
    context = get_workspace_context(req.workspaceId)
    history = load_conversation(req.workspaceId, req.threadId)
    history_text = format_conversation_history(history[-10:])

    # Focused prompt for tool execution
    prompt = (
        "You are the %s workspace agent — an AI companion for the user.\n"
        "The user has APPROVED the following tool action. Execute it NOW using the appropriate tool.\n\n"
        "Tool to use: %s\n"
        "Input parameters: %s\n\n"
        "## Recent Conversation Context\n%s\n\n"
        "## Workspace Context\n%s\n\n"
        "Execute the approved tool action immediately. After execution, briefly report what happened (1-2 sentences)."
    ) % (ws_name, req.toolName, json.dumps(req.toolInput), history_text, context[:2000])

    # Build allowedTools — allow the specific tool + read-only tools
    allowed = "%s,Read,Glob,Grep" % req.toolName
    # Also allow wildcard patterns for MCP tools
    tool_base = req.toolName.rsplit("__", 1)[0] if "__" in req.toolName else req.toolName
    if tool_base != req.toolName:
        allowed = "%s,%s__*,Read,Glob,Grep" % (req.toolName, tool_base)
    log("API approve allowedTools: %s" % allowed, "DEBUG")

    try:
        result_text = run_claude(
            prompt, config,
            allowed_tools=allowed,
            operation="approve_%s" % req.toolName,
        )
    except Exception as e:
        log("API approve ERROR: %s → %s" % (req.toolName, e), "ERROR")
        error_msg = make_message("assistant", "Failed to execute tool: %s" % str(e))
        error_msg["toolCalls"] = [{
            "id": "error-%s" % uuid.uuid4().hex[:8],
            "name": req.toolName,
            "input": req.toolInput,
            "status": "error",
            "result": str(e),
        }]
        append_message(req.workspaceId, req.threadId, error_msg)
        return {"status": "error", "message": error_msg}

    log("API approve OK: %s → %d chars" % (req.toolName, len(result_text)))
    assistant_msg = make_message("assistant", result_text)
    assistant_msg["toolCalls"] = [{
        "id": "exec-%s" % uuid.uuid4().hex[:8],
        "name": req.toolName,
        "input": req.toolInput,
        "status": "executed",
        "result": result_text,
    }]
    append_message(req.workspaceId, req.threadId, assistant_msg)

    return {"status": "executed", "message": assistant_msg}


@app.get("/api/conversations/{ws_id}")
def get_threads(ws_id: str):
    threads = list_threads(ws_id)
    log("API GET /api/conversations/%s → %d threads" % (ws_id, len(threads)), "DEBUG")
    return {"threads": threads}


@app.get("/api/conversations/{ws_id}/{thread_id}")
def get_conversation(ws_id: str, thread_id: str):
    messages = load_conversation(ws_id, thread_id)
    log("API GET /api/conversations/%s/%s → %d messages" % (ws_id, thread_id, len(messages)), "DEBUG")
    return {"messages": messages}


@app.post("/api/conversations/{ws_id}/{thread_id}/init")
def init_conversation(ws_id: str, thread_id: str):
    """Generate an agent greeting for a new workspace conversation."""
    log("API POST /api/conversations/%s/%s/init" % (ws_id, thread_id))
    existing = load_conversation(ws_id, thread_id)
    if existing:
        log("API init: already initialized (%d messages), returning last assistant msg" % len(existing))
        last_assistant = None
        for msg in reversed(existing):
            if msg["role"] == "assistant":
                last_assistant = msg
                break
        return {"message": last_assistant, "alreadyInitialized": True}

    config = load_config()
    ws_name = WORKSPACE_NAMES.get(ws_id, ws_id)
    context = get_workspace_context(ws_id)

    prompt = (
        "You are the %s workspace agent — an AI companion for the user.\n"
        "The user just opened this workspace. Provide a brief status summary (2-3 sentences max) "
        "of the most important items you can see in the context below. Then propose the single most "
        "impactful action you could take right now, OR suggest 1-2 quick wins you can handle immediately.\n"
        "End with a brief question like 'Want me to start?' or 'Which should I tackle first?'\n\n"
        "Be concise. No bullet lists. Conversational tone, like a sharp analyst briefing their boss.\n\n"
        "## Workspace Context\n%s"
    ) % (ws_name, context)

    log("API init prompt_len=%d context_len=%d" % (len(prompt), len(context)), "DEBUG")

    try:
        response_text = run_claude(
            prompt, config,
            allowed_tools=ALLOWED_TOOLS,
            operation="init_%s_%s" % (ws_id, thread_id),
        )
    except Exception as e:
        log("API init ERROR: %s" % e, "ERROR")
        response_text = "I'm having trouble loading context for this workspace. Error: %s" % str(e)

    assistant_msg = make_message("assistant", response_text)
    append_message(ws_id, thread_id, assistant_msg)

    log("API init OK: %s/%s → %d chars" % (ws_id, thread_id, len(response_text)))
    return {"message": assistant_msg}


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------

# Track active subprocesses for clean shutdown
_active_procs = set()


def _shutdown(signum, frame):
    """Kill all active claude subprocesses and exit."""
    for proc in list(_active_procs):
        try:
            proc.kill()
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


if __name__ == "__main__":
    import uvicorn
    print("Starting Workspace Chat API on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
