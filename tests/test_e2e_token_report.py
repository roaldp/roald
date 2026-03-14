"""E2E tests for scripts/token_report.py CLI tool.

Invokes the script as a subprocess and verifies output for each subcommand.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path("/Users/roaldp/conductor/workspaces/roald/missoula")
PYTHON = "/opt/homebrew/bin/python3.12"
SCRIPT = "scripts/token_report.py"
LOG_FILE = PROJECT_ROOT / "logs" / "pulse_detail.jsonl"

SAMPLE_RECORDS = [
    {
        "v": 1, "rid": "20260314T100000", "ts": "2026-03-14T10:00:00",
        "op": "full_pulse", "model": "claude-sonnet-4-20250514",
        "dur_s": 45.2, "num_turns": 8, "total_cost_usd": 0.0523,
        "prompt_chars": 12000, "prompt_est_tokens": 3000,
        "system_tools_count": 5, "system_mcp_servers": ["slack:connected"],
        "usage": {"input_tokens": 15000, "output_tokens": 2000, "cache_creation": 500, "cache_read": 10000},
        "model_usage": {
            "claude-sonnet-4-20250514": {
                "input_tokens": 15000, "output_tokens": 2000,
                "cache_read": 10000, "cache_creation": 500, "cost_usd": 0.0523,
            }
        },
        "subagents": [],
        "tools_summary": [
            {"tool_name": "Read", "call_count": 3, "total_input_chars": 500, "total_result_chars": 8000, "total_result_est_tokens": 2000, "error_count": 0},
            {"tool_name": "mcp__claude_ai_Slack__slack_read_channel", "call_count": 1, "total_input_chars": 200, "total_result_chars": 3000, "total_result_est_tokens": 750, "error_count": 0},
        ],
        "turns": [
            {"turn": 1, "role": "assistant", "input_tokens": 15000, "input_tokens_delta": None, "output_tokens": 2000, "cache_creation": 500, "cache_read": 10000, "tool_calls": [{"tool_id": "t1", "tool_name": "Read", "input_chars": 100, "subagent_type": None, "subagent_description": None}], "tool_results": []},
            {"turn": 2, "role": "user", "input_tokens": 0, "input_tokens_delta": None, "output_tokens": 0, "cache_creation": 0, "cache_read": 0, "tool_calls": [], "tool_results": [{"tool_id": "t1", "tool_name": "Read", "result_chars": 8000, "result_est_tokens": 2000, "is_error": False}]},
        ],
    },
    {
        "v": 1, "rid": "20260314T103000", "ts": "2026-03-14T10:30:00",
        "op": "reactive_pulse", "model": "claude-sonnet-4-20250514",
        "dur_s": 12.8, "num_turns": 4, "total_cost_usd": 0.0187,
        "prompt_chars": 5000, "prompt_est_tokens": 1250,
        "system_tools_count": 5, "system_mcp_servers": ["slack:connected"],
        "usage": {"input_tokens": 8000, "output_tokens": 800, "cache_creation": 200, "cache_read": 6000},
        "model_usage": {
            "claude-sonnet-4-20250514": {
                "input_tokens": 8000, "output_tokens": 800,
                "cache_read": 6000, "cache_creation": 200, "cost_usd": 0.0187,
            }
        },
        "subagents": [],
        "tools_summary": [
            {"tool_name": "mcp__claude_ai_Slack__slack_send_message", "call_count": 1, "total_input_chars": 300, "total_result_chars": 100, "total_result_est_tokens": 25, "error_count": 0},
        ],
        "turns": [
            {"turn": 1, "role": "assistant", "input_tokens": 8000, "input_tokens_delta": None, "output_tokens": 800, "cache_creation": 200, "cache_read": 6000, "tool_calls": [], "tool_results": []},
        ],
    },
    {
        "v": 1, "rid": "20260314T110000", "ts": "2026-03-14T11:00:00",
        "op": "poll_slack_messages[D123]", "model": "claude-sonnet-4-20250514",
        "dur_s": 5.1, "num_turns": 2, "total_cost_usd": 0.0042,
        "prompt_chars": 1000, "prompt_est_tokens": 250,
        "system_tools_count": 1, "system_mcp_servers": ["slack:connected"],
        "usage": {"input_tokens": 2000, "output_tokens": 150, "cache_creation": 0, "cache_read": 1500},
        "model_usage": {
            "claude-sonnet-4-20250514": {
                "input_tokens": 2000, "output_tokens": 150,
                "cache_read": 1500, "cache_creation": 0, "cost_usd": 0.0042,
            }
        },
        "subagents": [],
        "tools_summary": [
            {"tool_name": "mcp__claude_ai_Slack__slack_read_channel", "call_count": 1, "total_input_chars": 150, "total_result_chars": 2000, "total_result_est_tokens": 500, "error_count": 1},
        ],
        "turns": [],
    },
]


def _run(subcommand: list[str]) -> subprocess.CompletedProcess:
    """Run token_report.py with the given subcommand args."""
    return subprocess.run(
        [PYTHON, SCRIPT] + subcommand,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )


@pytest.fixture(autouse=True)
def setup_test_log():
    """Write test JSONL data, backing up any existing file."""
    backup = None
    if LOG_FILE.exists():
        backup = LOG_FILE.read_text()

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        for record in SAMPLE_RECORDS:
            f.write(json.dumps(record) + "\n")

    yield

    if backup is not None:
        LOG_FILE.write_text(backup)
    elif LOG_FILE.exists():
        LOG_FILE.unlink()


# ---- summary ----


def test_summary_subcommand():
    result = _run(["summary"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = result.stdout

    # All three operations present
    assert "full_pulse" in out
    assert "reactive_pulse" in out
    assert "poll_slack_messages" in out

    # Cost values present
    assert "0.0523" in out
    assert "0.0187" in out
    assert "0.0042" in out

    # Out Chk column: records with turns show "ok", empty turns show "n/a"
    lines = out.strip().splitlines()
    # Find data lines (skip header + separator)
    data_lines = [l for l in lines if "full_pulse" in l or "reactive_pulse" in l or "poll_slack_messages" in l]
    assert len(data_lines) == 3

    full_pulse_line = [l for l in data_lines if "full_pulse" in l][0]
    reactive_line = [l for l in data_lines if "reactive_pulse" in l][0]
    poll_line = [l for l in data_lines if "poll_slack_messages" in l][0]

    assert "ok" in full_pulse_line
    assert "ok" in reactive_line
    assert "n/a" in poll_line


def test_summary_with_limit():
    result = _run(["summary", "--limit", "1"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = result.stdout

    # Only the last record (poll_slack_messages) should appear
    assert "poll_slack_messages" in out
    assert "full_pulse" not in out
    assert "reactive_pulse" not in out


# ---- tools ----


def test_tools_subcommand():
    result = _run(["tools"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = result.stdout

    assert "Read" in out
    assert "slack_read_channel" in out
    assert "slack_send_message" in out
    assert "TOTAL" in out

    # Read has call_count 3 across all records
    read_line = [l for l in out.splitlines() if l.startswith("Read")]
    assert len(read_line) == 1
    # The call count column should show 3
    assert "3" in read_line[0]


def test_tools_with_op_filter():
    result = _run(["tools", "--op", "full_pulse"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = result.stdout

    # Only full_pulse tools: Read and slack_read_channel
    assert "Read" in out
    assert "slack_read_channel" in out
    # slack_send_message is from reactive_pulse, should not appear
    assert "slack_send_message" not in out


# ---- biggest ----


def test_biggest_subcommand():
    result = _run(["biggest"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = result.stdout

    # The only tool_result entry is Read with 8000 chars / 2000 est tokens
    assert "Read" in out
    assert "20260314T100000" in out  # record ID
    # Turn 2 has the tool result
    assert "2" in out


# ---- models ----


def test_models_subcommand():
    result = _run(["models"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = result.stdout

    assert "claude-sonnet-4-20250514" in out
    assert "TOTAL" in out

    # Total cost: 0.0523 + 0.0187 + 0.0042 = 0.0752
    assert "0.0752" in out


# ---- error case ----


def test_no_log_file(setup_test_log):
    """When log file doesn't exist, script should exit non-zero."""
    # Remove the log file created by the fixture
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    result = _run(["summary"])
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "not found" in combined.lower()
