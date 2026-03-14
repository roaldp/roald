"""Unit tests for scripts/token_report.py — CLI token usage report tool."""

import argparse
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/Users/roaldp/conductor/workspaces/roald/missoula/scripts")
import token_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTINEL = object()


def _make_record(
    ts="2026-03-14T10:30:00",
    op="full_pulse",
    cost=0.05,
    in_tok=10000,
    out_tok=2000,
    dur_s=45.0,
    tools_summary=_SENTINEL,
    turns=_SENTINEL,
    model_usage=_SENTINEL,
):
    """Create a minimal PulseDetailRecord dict for testing."""
    if tools_summary is _SENTINEL:
        tools_summary = [
            {
                "tool_name": "Read",
                "call_count": 3,
                "total_input_chars": 100,
                "total_result_chars": 5000,
                "total_result_est_tokens": 1250,
                "error_count": 0,
            }
        ]
    if model_usage is _SENTINEL:
        model_usage = {
            "claude-sonnet-4-20250514": {
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cache_read": 5000,
                "cache_creation": 0,
                "cost_usd": cost,
            }
        }
    if turns is _SENTINEL:
        turns = [
            {
                "turn": 1,
                "role": "assistant",
                "input_tokens": 8000,
                "input_tokens_delta": None,
                "output_tokens": 1500,
                "cache_creation": 0,
                "cache_read": 5000,
                "tool_calls": [],
                "tool_results": [],
            },
            {
                "turn": 2,
                "role": "user",
                "input_tokens": 0,
                "input_tokens_delta": None,
                "output_tokens": 0,
                "cache_creation": 0,
                "cache_read": 0,
                "tool_calls": [],
                "tool_results": [
                    {
                        "tool_id": "t1",
                        "tool_name": "Read",
                        "result_chars": 5000,
                        "result_est_tokens": 1250,
                        "is_error": False,
                    }
                ],
            },
            {
                "turn": 3,
                "role": "assistant",
                "input_tokens": 10000,
                "input_tokens_delta": 2000,
                "output_tokens": 500,
                "cache_creation": 0,
                "cache_read": 5000,
                "tool_calls": [],
                "tool_results": [],
            },
        ]

    return {
        "v": 1,
        "rid": "20260314T103000",
        "ts": ts,
        "op": op,
        "model": "claude-sonnet-4-20250514",
        "dur_s": dur_s,
        "num_turns": 5,
        "total_cost_usd": cost,
        "prompt_chars": 4000,
        "prompt_est_tokens": 1000,
        "system_tools_count": 10,
        "system_mcp_servers": [],
        "usage": {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cache_creation": 0,
            "cache_read": 5000,
        },
        "model_usage": model_usage,
        "subagents": [],
        "tools_summary": tools_summary,
        "turns": turns,
    }


def _write_jsonl(path, records):
    """Write a list of dicts as JSONL to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# 1. load_records
# ---------------------------------------------------------------------------

class TestLoadRecords:
    def test_loads_valid_jsonl(self, tmp_path, monkeypatch):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(ts="2026-03-14T10:00:00"), _make_record(ts="2026-03-14T11:00:00")]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        result = token_report.load_records()
        assert len(result) == 2

    def test_filters_by_since(self, tmp_path, monkeypatch):
        log_file = tmp_path / "detail.jsonl"
        records = [
            _make_record(ts="2026-03-10T10:00:00"),
            _make_record(ts="2026-03-14T10:00:00"),
        ]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        result = token_report.load_records(since="2026-03-12")
        assert len(result) == 1
        assert result[0]["ts"] == "2026-03-14T10:00:00"

    def test_skips_malformed_lines(self, tmp_path, monkeypatch):
        log_file = tmp_path / "detail.jsonl"
        log_file.write_text(
            json.dumps(_make_record()) + "\n"
            "NOT VALID JSON\n"
            + json.dumps(_make_record(ts="2026-03-14T12:00:00")) + "\n"
        )
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        result = token_report.load_records()
        assert len(result) == 2

    def test_sorted_by_timestamp_ascending(self, tmp_path, monkeypatch):
        log_file = tmp_path / "detail.jsonl"
        records = [
            _make_record(ts="2026-03-14T12:00:00"),
            _make_record(ts="2026-03-14T08:00:00"),
            _make_record(ts="2026-03-14T10:00:00"),
        ]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        result = token_report.load_records()
        timestamps = [r["ts"] for r in result]
        assert timestamps == sorted(timestamps)

    def test_system_exit_if_file_not_found(self, tmp_path, monkeypatch):
        log_file = tmp_path / "nonexistent.jsonl"
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        with pytest.raises(SystemExit):
            token_report.load_records()

    def test_system_exit_if_no_records_match_since(self, tmp_path, monkeypatch):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(ts="2026-03-01T10:00:00")]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        with pytest.raises(SystemExit):
            token_report.load_records(since="2026-03-15")


# ---------------------------------------------------------------------------
# 2. _fmt_tokens
# ---------------------------------------------------------------------------

class TestFmtTokens:
    def test_below_1000(self):
        assert token_report._fmt_tokens(832) == "832"

    def test_above_1000(self):
        assert token_report._fmt_tokens(15200) == "15.2K"

    def test_exact_1000(self):
        assert token_report._fmt_tokens(1000) == "1.0K"

    def test_zero(self):
        assert token_report._fmt_tokens(0) == "0"

    def test_just_below_1000(self):
        assert token_report._fmt_tokens(999) == "999"


# ---------------------------------------------------------------------------
# 3. _fmt_cost
# ---------------------------------------------------------------------------

class TestFmtCost:
    def test_typical_cost(self):
        assert token_report._fmt_cost(0.0342) == "$0.0342"

    def test_zero(self):
        assert token_report._fmt_cost(0) == "$0.0000"

    def test_larger_cost(self):
        assert token_report._fmt_cost(1.5) == "$1.5000"


# ---------------------------------------------------------------------------
# 4. _short_ts
# ---------------------------------------------------------------------------

class TestShortTs:
    def test_typical_iso_timestamp(self):
        assert token_report._short_ts("2026-03-14T10:30:00") == "03-14 10:30"

    def test_different_date(self):
        assert token_report._short_ts("2026-01-05T23:45:00") == "01-05 23:45"


# ---------------------------------------------------------------------------
# 5. CLI commands
# ---------------------------------------------------------------------------

class TestCmdSummary:
    def test_output_contains_expected_values(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(op="full_pulse", cost=0.05, dur_s=45.0)]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, limit=None)
        token_report.cmd_summary(args)

        output = capsys.readouterr().out
        assert "full_pulse" in output
        assert "$0.0500" in output
        assert "45.0" in output

    def test_with_limit(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [
            _make_record(ts="2026-03-14T10:00:00", op="pulse_1"),
            _make_record(ts="2026-03-14T11:00:00", op="pulse_2"),
            _make_record(ts="2026-03-14T12:00:00", op="pulse_3"),
        ]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, limit=1)
        token_report.cmd_summary(args)

        output = capsys.readouterr().out
        assert "pulse_3" in output
        assert "pulse_1" not in output

    def test_empty_turns_shows_na(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(turns=[])]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, limit=None)
        token_report.cmd_summary(args)

        output = capsys.readouterr().out
        assert "n/a" in output


class TestCmdTools:
    def test_output_contains_tool_data(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record()]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, op=None)
        token_report.cmd_tools(args)

        output = capsys.readouterr().out
        assert "Read" in output
        assert "TOTAL" in output

    def test_empty_tools_summary(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(tools_summary=[])]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, op=None)
        with pytest.raises(SystemExit):
            token_report.cmd_tools(args)

    def test_filter_by_op(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [
            _make_record(op="full_pulse"),
            _make_record(op="reactive_pulse"),
        ]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, op="full_pulse")
        token_report.cmd_tools(args)

        output = capsys.readouterr().out
        assert "Read" in output


class TestCmdBiggest:
    def test_output_contains_tool_results(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record()]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, top=10)
        token_report.cmd_biggest(args)

        output = capsys.readouterr().out
        assert "Read" in output
        assert "5,000" in output

    def test_missing_turns_falls_back(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(turns=[])]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None, top=10, op=None)
        token_report.cmd_biggest(args)

        output = capsys.readouterr().out
        assert "No per-turn tool result data" in output


class TestCmdModels:
    def test_output_contains_model_data(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record()]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None)
        token_report.cmd_models(args)

        output = capsys.readouterr().out
        assert "claude-sonnet-4-20250514" in output
        assert "$0.0500" in output
        assert "TOTAL" in output

    def test_no_model_usage_exits(self, tmp_path, monkeypatch, capsys):
        log_file = tmp_path / "detail.jsonl"
        records = [_make_record(model_usage={})]
        _write_jsonl(log_file, records)
        monkeypatch.setattr(token_report, "LOG_FILE", log_file)

        args = argparse.Namespace(since=None)
        with pytest.raises(SystemExit):
            token_report.cmd_models(args)
