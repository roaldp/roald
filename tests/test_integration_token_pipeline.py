"""Integration tests for the full token metrics pipeline.

Tests the chain: stream-json parsing -> metric collection -> detail record writing -> report reading.
"""

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, "/Users/roaldp/conductor/workspaces/roald/missoula")
sys.path.insert(0, "/Users/roaldp/conductor/workspaces/roald/missoula/scripts")

import pulse
import token_report


# ============================================================================
# FIXTURES & HELPERS
# ============================================================================

def make_stream_json_stdout():
    """Build realistic stream-json output simulating a pulse with tool calls."""
    events = [
        # System init
        {"type": "system", "subtype": "init", "model": "claude-sonnet-4-20250514", "tools": [
            {"name": "Read"}, {"name": "Edit"}, {"name": "mcp__claude_ai_Slack__slack_read_channel"}
        ], "mcp_servers": [{"name": "slack", "status": "connected"}]},

        # Assistant turn 1: makes a Read tool call
        {"type": "assistant", "message": {
            "content": [
                {"type": "text", "text": "Let me read the file."},
                {"type": "tool_use", "id": "tool_1", "name": "Read", "input": {"file_path": "/tmp/test.md"}}
            ],
            "usage": {"input_tokens": 5000, "output_tokens": 200,
                      "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 3000}
        }},

        # User turn 1: tool result for Read
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "tool_1",
             "content": "File content here with some text that is 50 chars.",
             "is_error": False}
        ]}},

        # Assistant turn 2: makes a Slack tool call
        {"type": "assistant", "message": {
            "content": [
                {"type": "text", "text": "Now sending a message."},
                {"type": "tool_use", "id": "tool_2", "name": "mcp__claude_ai_Slack__slack_send_message",
                 "input": {"channel_id": "C123", "text": "Hello Roald"}}
            ],
            "usage": {"input_tokens": 5500, "output_tokens": 350,
                      "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 3500}
        }},

        # User turn 2: tool result for Slack
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "tool_2",
             "content": "Message sent successfully", "is_error": False}
        ]}},

        # Assistant turn 3: final text response
        {"type": "assistant", "message": {
            "content": [{"type": "text", "text": "Done! I've read the file and sent the message."}],
            "usage": {"input_tokens": 6000, "output_tokens": 400,
                      "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 4000}
        }},

        # Result event
        {"type": "result", "result": "Done! I've read the file and sent the message.",
         "cost_usd": 0.0234, "duration_ms": 15000, "num_turns": 5,
         "usage": {"input_tokens": 6000, "output_tokens": 400,
                   "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 4000},
         "modelUsage": {
             "claude-sonnet-4-20250514": {
                 "inputTokens": 6000, "outputTokens": 400,
                 "cacheReadInputTokens": 4000, "cacheCreationInputTokens": 1000,
                 "costUSD": 0.0234
             }
         }
        }
    ]
    return "\n".join(json.dumps(e) for e in events)


def make_subagent_stream_json_stdout():
    """Build stream-json output with a sub-agent (Agent tool) session."""
    events = [
        # 1. System init (parent)
        {"type": "system", "subtype": "init", "model": "claude-sonnet-4-20250514", "tools": [
            {"name": "Read"}, {"name": "Agent"}, {"name": "Glob"}
        ], "mcp_servers": []},

        # 2. Assistant turn with Agent tool_use
        {"type": "assistant", "message": {
            "content": [
                {"type": "text", "text": "I'll use a subagent to find files."},
                {"type": "tool_use", "id": "agent_1", "name": "Agent",
                 "input": {"type": "Explore", "description": "Find files", "prompt": "Search for config files"}}
            ],
            "usage": {"input_tokens": 3000, "output_tokens": 100,
                      "cache_creation_input_tokens": 500, "cache_read_input_tokens": 2000}
        }},

        # 3. System init (sub-agent, model=None)
        {"type": "system", "subtype": "init", "model": None, "tools": [
            {"name": "Glob"}, {"name": "Read"}
        ], "mcp_servers": []},

        # 4. Assistant turn inside subagent with Glob tool_use
        {"type": "assistant", "message": {
            "content": [
                {"type": "text", "text": "Searching for config files."},
                {"type": "tool_use", "id": "tool_sub_1", "name": "Glob",
                 "input": {"pattern": "**/*.yaml"}}
            ],
            "usage": {"input_tokens": 3500, "output_tokens": 150,
                      "cache_creation_input_tokens": 500, "cache_read_input_tokens": 2500}
        }},

        # 5. User turn with tool_result for Glob
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "tool_sub_1",
             "content": "config.yaml\nconfig.template.yaml", "is_error": False}
        ]}},

        # 6. User turn with tool_result for agent_1 (closes subagent)
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "agent_1",
             "content": "Found 2 config files: config.yaml, config.template.yaml",
             "is_error": False}
        ]}},

        # 7. Assistant final turn
        {"type": "assistant", "message": {
            "content": [{"type": "text", "text": "Found the config files via subagent."}],
            "usage": {"input_tokens": 4000, "output_tokens": 200,
                      "cache_creation_input_tokens": 500, "cache_read_input_tokens": 3000}
        }},

        # 8. Result event
        {"type": "result", "result": "Found the config files via subagent.",
         "cost_usd": 0.015, "duration_ms": 8000, "num_turns": 6,
         "usage": {"input_tokens": 4000, "output_tokens": 200,
                   "cache_creation_input_tokens": 500, "cache_read_input_tokens": 3000},
         "modelUsage": {
             "claude-sonnet-4-20250514": {
                 "inputTokens": 4000, "outputTokens": 200,
                 "cacheReadInputTokens": 3000, "cacheCreationInputTokens": 500,
                 "costUSD": 0.015
             }
         }
        }
    ]
    return "\n".join(json.dumps(e) for e in events)


def _base_config():
    """Minimal config dict for tests."""
    return {
        "claude_command": "claude",
        "detail_logging": True,
        "claude_timeout_seconds": 300,
    }


def _patch_paths(monkeypatch, tmp_path):
    """Monkeypatch pulse log paths to tmp_path locations."""
    detail_path = tmp_path / "pulse_detail.jsonl"
    log_path = tmp_path / "pulse.log"
    monkeypatch.setattr(pulse, "DETAIL_LOG_PATH", detail_path)
    monkeypatch.setattr(pulse, "LOG_PATH", log_path)
    return detail_path, log_path


def _read_detail_record(detail_path: Path) -> dict:
    """Read the first JSONL record from the detail log."""
    lines = detail_path.read_text().strip().splitlines()
    assert len(lines) >= 1, f"Expected at least 1 JSONL line, got {len(lines)}"
    return json.loads(lines[0])


# ============================================================================
# TEST 1: run_claude parses a realistic stream-json session correctly
# ============================================================================

class TestRunClaudeRealisticSession:
    def test_parses_stream_json_correctly(self, monkeypatch, tmp_path):
        detail_path, _ = _patch_paths(monkeypatch, tmp_path)
        config = _base_config()
        stream_json = make_stream_json_stdout()

        mock_result = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stream_json, stderr=""
        )
        with patch("pulse.subprocess.run", return_value=mock_result):
            result_text = pulse.run_claude("test prompt", config, operation="test_op")

        # Return value is the result text
        assert result_text == "Done! I've read the file and sent the message."

        # Detail record was written
        assert detail_path.exists()
        record = _read_detail_record(detail_path)

        # Core fields
        assert record["model"] == "claude-sonnet-4-20250514"
        assert record["total_cost_usd"] == 0.0234
        assert record["num_turns"] == 5

        # Usage
        assert record["usage"]["input_tokens"] == 6000
        assert record["usage"]["output_tokens"] == 400
        assert record["usage"]["cache_creation"] == 1000
        assert record["usage"]["cache_read"] == 4000

        # Model usage
        assert "claude-sonnet-4-20250514" in record["model_usage"]
        mu = record["model_usage"]["claude-sonnet-4-20250514"]
        assert mu["input_tokens"] == 6000
        assert mu["output_tokens"] == 400
        assert mu["cache_read"] == 4000
        assert mu["cache_creation"] == 1000
        assert mu["cost_usd"] == 0.0234

        # Tools summary
        tool_names = {t["tool_name"] for t in record["tools_summary"]}
        assert "Read" in tool_names
        assert "mcp__claude_ai_Slack__slack_send_message" in tool_names

        read_summary = next(t for t in record["tools_summary"] if t["tool_name"] == "Read")
        assert read_summary["call_count"] == 1

        # Turns: 3 assistant + 2 user = 5
        assert record["turns"] is not None
        assert len(record["turns"]) == 5

        # System info
        assert record["system_tools_count"] == 3
        assert "slack:connected" in record["system_mcp_servers"]


# ============================================================================
# TEST 2: run_claude with subagent events
# ============================================================================

class TestRunClaudeSubagent:
    def test_subagent_tracking(self, monkeypatch, tmp_path):
        detail_path, _ = _patch_paths(monkeypatch, tmp_path)
        config = _base_config()
        stream_json = make_subagent_stream_json_stdout()

        mock_result = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stream_json, stderr=""
        )
        with patch("pulse.subprocess.run", return_value=mock_result):
            result_text = pulse.run_claude("test prompt", config, operation="test_subagent")

        assert result_text == "Found the config files via subagent."

        record = _read_detail_record(detail_path)

        # Subagents list should have the completed subagent
        assert len(record["subagents"]) == 1
        sa = record["subagents"][0]
        assert sa["tool_id"] == "agent_1"
        assert sa["subagent_type"] == "Explore"
        assert sa["model"] is None

        # Subagent's tool_calls should include Glob
        assert "Glob" in sa["tool_calls"]

        # result_chars should measure the agent tool_result content
        expected_content = "Found 2 config files: config.yaml, config.template.yaml"
        assert sa["result_chars"] == len(expected_content)


# ============================================================================
# TEST 3: run_claude error handling
# ============================================================================

class TestRunClaudeErrors:
    def test_nonzero_exit_code_raises(self, monkeypatch, tmp_path):
        _patch_paths(monkeypatch, tmp_path)
        config = _base_config()

        mock_result = subprocess.CompletedProcess(
            args=["claude"], returncode=1, stdout="", stderr="Something went wrong"
        )
        with patch("pulse.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="claude exited 1"):
                pulse.run_claude("test", config)

    def test_timeout_raises(self, monkeypatch, tmp_path):
        _patch_paths(monkeypatch, tmp_path)
        config = _base_config()

        with patch("pulse.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=300)):
            with pytest.raises(RuntimeError, match="claude timed out"):
                pulse.run_claude("test", config)


# ============================================================================
# TEST 4: run_claude with detail_logging disabled
# ============================================================================

class TestRunClaudeDetailLoggingDisabled:
    def test_turns_is_none_when_disabled(self, monkeypatch, tmp_path):
        detail_path, _ = _patch_paths(monkeypatch, tmp_path)
        config = _base_config()
        config["detail_logging"] = False
        stream_json = make_stream_json_stdout()

        mock_result = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stream_json, stderr=""
        )
        with patch("pulse.subprocess.run", return_value=mock_result):
            pulse.run_claude("test prompt", config, operation="test_no_detail")

        # Detail record is still written
        assert detail_path.exists()
        record = _read_detail_record(detail_path)

        # turns field should be None
        assert record["turns"] is None

        # Other fields should still be populated
        assert record["model"] == "claude-sonnet-4-20250514"
        assert record["total_cost_usd"] == 0.0234


# ============================================================================
# TEST 5: End-to-end pipeline — run_claude writes JSONL, token_report reads it
# ============================================================================

class TestEndToEndPipeline:
    def test_report_reads_detail_record(self, monkeypatch, tmp_path, capsys):
        detail_path, _ = _patch_paths(monkeypatch, tmp_path)
        config = _base_config()
        stream_json = make_stream_json_stdout()

        mock_result = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stream_json, stderr=""
        )
        with patch("pulse.subprocess.run", return_value=mock_result):
            pulse.run_claude("test prompt", config, operation="test_e2e")

        # Point token_report at the same file
        monkeypatch.setattr(token_report, "LOG_FILE", detail_path)

        # load_records should find our record
        records = token_report.load_records()
        assert len(records) == 1
        r = records[0]
        assert r["total_cost_usd"] == 0.0234
        assert r["usage"]["input_tokens"] == 6000

        # cmd_summary should produce output containing cost and tokens
        mock_args = Namespace(since=None, limit=None)
        token_report.cmd_summary(mock_args)
        captured = capsys.readouterr()
        assert "0.0234" in captured.out
        assert "6.0K" in captured.out
        assert "test_e2e" in captured.out


# ============================================================================
# TEST 6: Slack outbound logging
# ============================================================================

class TestSlackOutboundLogging:
    def test_slack_outbound_logged(self, monkeypatch, tmp_path):
        detail_path, _ = _patch_paths(monkeypatch, tmp_path)
        config = _base_config()
        stream_json = make_stream_json_stdout()

        mock_result = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stream_json, stderr=""
        )
        with patch("pulse.subprocess.run", return_value=mock_result), \
             patch("pulse.log") as mock_log:
            pulse.run_claude("test prompt", config, operation="test_slack")

        # Collect all log call args
        log_calls = [str(call) for call in mock_log.call_args_list]
        log_messages = [call[0][0] for call in mock_log.call_args_list]

        # Should have SLACK OUTBOUND START and END messages with channel ID
        start_msgs = [m for m in log_messages if "SLACK OUTBOUND START" in m]
        end_msgs = [m for m in log_messages if "SLACK OUTBOUND END" in m]
        assert len(start_msgs) >= 1, f"Expected SLACK OUTBOUND START log, got: {log_messages}"
        assert len(end_msgs) >= 1, f"Expected SLACK OUTBOUND END log, got: {log_messages}"

        # Channel ID should be in the messages
        assert "C123" in start_msgs[0]
        assert "C123" in end_msgs[0]
