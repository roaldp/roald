"""Tests for the token usage report generator.

Covers JSONL loading with time filtering, aggregation by operation,
parse_since, and print_report.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from token_report import (
    _normalize_entry,
    aggregate_by_model,
    aggregate_by_operation,
    aggregate_by_timeline,
    load_usage_log,
    OperationSummary,
    TimelineBucket,
    TokenReport,
    parse_since,
    print_detail_report,
    print_model_report,
    print_report,
    print_timeline_report,
)


# ============================================================================
# HELPERS
# ============================================================================

def _make_entry(
    operation: str,
    timestamp: str,
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_creation: int = 0,
    cache_read: int = 1000,
    cost_usd: float = 0.01,
    model: str = "unknown",
    rid: str = "20260313T120000",
) -> dict:
    """Build a token usage log entry dict using lean keys."""
    return {
        "ts": timestamp,
        "op": operation,
        "model": model,
        "in": input_tokens,
        "out": output_tokens,
        "cache_in": cache_creation,
        "cache_read": cache_read,
        "cost": cost_usd,
        "dur": 2.0,
        "rid": rid,
    }


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    """Write a list of dicts as JSONL to a file."""
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ============================================================================
# TESTS
# ============================================================================

class TestLoadUsageLog:
    """Tests for load_usage_log."""

    def test_filters_by_since(self, tmp_path: Path) -> None:
        """Entries older than the since cutoff are excluded."""
        now = datetime.now()
        old_ts = (now - timedelta(hours=2)).isoformat(timespec="seconds")
        recent_ts = (now - timedelta(minutes=10)).isoformat(timespec="seconds")

        entries = [
            _make_entry("old_op", old_ts, cost_usd=0.05),
            _make_entry("recent_op", recent_ts, cost_usd=0.01),
        ]
        log_file = tmp_path / "usage.jsonl"
        _write_jsonl(log_file, entries)

        since = now - timedelta(hours=1)
        result = load_usage_log(log_file, since)

        assert len(result) == 1
        assert result[0]["op"] == "recent_op"

    def test_loads_all_without_since(self, tmp_path: Path) -> None:
        """All entries are returned when since is None."""
        now = datetime.now()
        entries = [
            _make_entry("op_a", (now - timedelta(days=5)).isoformat(timespec="seconds")),
            _make_entry("op_b", now.isoformat(timespec="seconds")),
        ]
        log_file = tmp_path / "usage.jsonl"
        _write_jsonl(log_file, entries)

        result = load_usage_log(log_file, None)
        assert len(result) == 2

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        """Malformed JSON lines are skipped without error."""
        log_file = tmp_path / "usage.jsonl"
        with open(log_file, "w") as f:
            f.write("not valid json\n")
            f.write(json.dumps(_make_entry("good_op", datetime.now().isoformat(timespec="seconds"))) + "\n")

        result = load_usage_log(log_file, None)
        assert len(result) == 1
        assert result[0]["op"] == "good_op"

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """Returns empty list if the log file does not exist."""
        result = load_usage_log(tmp_path / "nonexistent.jsonl", None)
        assert result == []


class TestAggregateByOperation:
    """Tests for aggregate_by_operation."""

    def test_groups_and_sums(self) -> None:
        """Entries with the same operation are grouped and summed correctly."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = [
            _make_entry("poll_slack", now, input_tokens=100, output_tokens=50, cache_read=1000, cost_usd=0.01),
            _make_entry("poll_slack", now, input_tokens=200, output_tokens=60, cache_read=2000, cost_usd=0.02),
            _make_entry("run_pulse", now, input_tokens=500, output_tokens=100, cache_read=5000, cost_usd=0.10),
        ]

        result = aggregate_by_operation(entries)

        by_op = {s.operation: s for s in result}
        assert len(by_op) == 2

        slack = by_op["poll_slack"]
        assert slack.call_count == 2
        assert slack.total_input_tokens == 300
        assert slack.total_output_tokens == 110
        assert slack.total_cache_tokens == 3000
        assert abs(slack.total_cost_usd - 0.03) < 1e-9
        assert abs(slack.avg_cost_per_call - 0.015) < 1e-9

        pulse = by_op["run_pulse"]
        assert pulse.call_count == 1
        assert pulse.total_input_tokens == 500
        assert abs(pulse.total_cost_usd - 0.10) < 1e-9

    def test_empty_entries(self) -> None:
        """Empty input returns an empty list."""
        result = aggregate_by_operation([])
        assert result == []


class TestParseSince:
    """Tests for parse_since."""

    def test_30m_returns_roughly_30_minutes_ago(self) -> None:
        before = datetime.now() - timedelta(minutes=30, seconds=2)
        result = parse_since("30m")
        after = datetime.now() - timedelta(minutes=30)
        assert before <= result <= after

    def test_1h_returns_roughly_1_hour_ago(self) -> None:
        before = datetime.now() - timedelta(hours=1, seconds=2)
        result = parse_since("1h")
        after = datetime.now() - timedelta(hours=1)
        assert before <= result <= after

    def test_7d_returns_roughly_7_days_ago(self) -> None:
        before = datetime.now() - timedelta(days=7, seconds=2)
        result = parse_since("7d")
        after = datetime.now() - timedelta(days=7)
        assert before <= result <= after

    def test_invalid_format_abc_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid --since format"):
            parse_since("abc")

    def test_invalid_format_10x_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid --since format"):
            parse_since("10x")


class TestPrintReport:
    """Tests for print_report."""

    def test_empty_operations_prints_no_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        report = TokenReport(period="last 1h", operations=[], grand_total_cost=0.0)
        print_report(report)
        output = capsys.readouterr().out
        assert "No data found" in output

    def test_with_operations_prints_table(self, capsys: pytest.CaptureFixture[str]) -> None:
        op = OperationSummary(
            operation="full_pulse",
            call_count=3,
            total_input_tokens=1000,
            total_output_tokens=500,
            total_cache_tokens=2000,
            total_cost_usd=0.15,
            avg_cost_per_call=0.05,
        )
        report = TokenReport(
            period="last 24h",
            operations=[op],
            grand_total_cost=0.15,
        )
        print_report(report)
        output = capsys.readouterr().out
        assert "full_pulse" in output
        assert "Calls" in output
        assert "Total Cost" in output
        assert "TOTAL" in output
        assert "0.15" in output


class TestPrintDetailReport:
    """Tests for print_detail_report."""

    def test_output_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Detail rows are printed with correct columns."""
        entries = [
            _make_entry("full_pulse", "2026-03-13T17:21:03", input_tokens=283,
                        output_tokens=2239, cache_creation=19358, cache_read=264788,
                        cost_usd=0.1865, model="sonnet"),
        ]
        # Patch dur for known output
        entries[0]["dur"] = 67.26

        print_detail_report(entries, grand_total=0.1865, limit=50, period="last 1h")
        output = capsys.readouterr().out

        assert "Token Usage Detail" in output
        assert "last 1h" in output
        assert "limit 50" in output
        assert "Timestamp" in output
        assert "Operation" in output
        assert "Model" in output
        assert "Cost" in output
        assert "Duration" in output
        assert "Tokens" in output
        assert "full_pulse" in output
        assert "sonnet" in output
        assert "0.1865" in output
        assert "67.3s" in output
        assert "286,668" in output
        assert "TOTAL (1 invocations)" in output

    def test_limit_caps_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--limit caps the number of detail rows shown."""
        now = datetime.now()
        entries = [
            _make_entry(f"op_{i}", (now - timedelta(minutes=i)).isoformat(timespec="seconds"),
                        cost_usd=0.01)
            for i in range(10)
        ]
        grand_total = sum(e["cost"] for e in entries)

        print_detail_report(entries, grand_total=grand_total, limit=3, period="all time")
        output = capsys.readouterr().out

        # Count data rows (lines between the two dashed separator lines)
        lines = output.strip().split("\n")
        separator_indices = [i for i, l in enumerate(lines) if l.startswith("---")]
        assert len(separator_indices) == 2
        data_lines = lines[separator_indices[0] + 1 : separator_indices[1]]
        assert len(data_lines) == 3

        # TOTAL line should still reflect all 10 entries
        assert "TOTAL (10 invocations)" in output

    def test_empty_entries(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty input prints no-data message."""
        print_detail_report([], grand_total=0.0, limit=50, period="last 1h")
        output = capsys.readouterr().out
        assert "No data found" in output

    def test_most_recent_first(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Entries are sorted most recent first."""
        entries = [
            _make_entry("older", "2026-03-13T10:00:00", cost_usd=0.01),
            _make_entry("newer", "2026-03-13T12:00:00", cost_usd=0.02),
        ]
        print_detail_report(entries, grand_total=0.03, limit=50, period="all time")
        output = capsys.readouterr().out
        # "newer" should appear before "older" in the output
        assert output.index("newer") < output.index("older")


class TestAggregateByModel:
    """Tests for aggregate_by_model."""

    def test_groups_by_model(self) -> None:
        """Entries with different models are grouped and summed correctly."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = [
            _make_entry("poll_slack", now, input_tokens=100, output_tokens=50, cache_read=1000, cost_usd=0.01, model="sonnet"),
            _make_entry("full_pulse", now, input_tokens=200, output_tokens=60, cache_read=2000, cost_usd=0.02, model="sonnet"),
            _make_entry("poll_slack", now, input_tokens=500, output_tokens=100, cache_read=5000, cost_usd=0.10, model="haiku"),
        ]

        result = aggregate_by_model(entries)

        by_model = {s.operation: s for s in result}
        assert len(by_model) == 2

        sonnet = by_model["sonnet"]
        assert sonnet.call_count == 2
        assert sonnet.total_input_tokens == 300
        assert sonnet.total_output_tokens == 110
        assert sonnet.total_cache_tokens == 3000
        assert abs(sonnet.total_cost_usd - 0.03) < 1e-9
        assert abs(sonnet.avg_cost_per_call - 0.015) < 1e-9

        haiku = by_model["haiku"]
        assert haiku.call_count == 1
        assert haiku.total_input_tokens == 500
        assert abs(haiku.total_cost_usd - 0.10) < 1e-9

    def test_missing_model_defaults_to_unknown(self) -> None:
        """Entries without a model field default to 'unknown' after normalization."""
        now = datetime.now().isoformat(timespec="seconds")
        # Build entry without model key, then normalize
        entry = {
            "ts": now,
            "op": "test_op",
            "in": 100,
            "out": 50,
            "cache_in": 0,
            "cache_read": 1000,
            "cost": 0.01,
            "dur": 2.0,
            "rid": "abc",
        }
        # Remove model if present, then normalize
        entry.pop("model", None)
        _normalize_entry(entry)

        result = aggregate_by_model([entry])
        assert len(result) == 1
        assert result[0].operation == "unknown"


class TestAggregateByTimeline:
    """Tests for aggregate_by_timeline."""

    def test_hourly_buckets(self) -> None:
        """Entries at different hours are bucketed correctly with correct labels."""
        entries = [
            _make_entry("poll_slack", "2026-03-13T14:10:00", cost_usd=0.10),
            _make_entry("poll_slack", "2026-03-13T14:45:00", cost_usd=0.20),
            _make_entry("full_pulse", "2026-03-13T15:30:00", cost_usd=0.50),
        ]

        result = aggregate_by_timeline(entries, "hourly")

        assert len(result) == 2
        assert result[0].period_label == "14:00-15:00"
        assert result[0].call_count == 2
        assert abs(result[0].total_cost_usd - 0.30) < 1e-9
        assert result[1].period_label == "15:00-16:00"
        assert result[1].call_count == 1
        assert abs(result[1].total_cost_usd - 0.50) < 1e-9

    def test_daily_buckets(self) -> None:
        """Entries on different days are bucketed correctly."""
        entries = [
            _make_entry("poll_slack", "2026-03-12T10:00:00", cost_usd=0.10),
            _make_entry("full_pulse", "2026-03-12T14:00:00", cost_usd=0.20),
            _make_entry("poll_slack", "2026-03-13T09:00:00", cost_usd=0.30),
        ]

        result = aggregate_by_timeline(entries, "daily")

        assert len(result) == 2
        assert result[0].period_label == "2026-03-12"
        assert result[0].call_count == 2
        assert abs(result[0].total_cost_usd - 0.30) < 1e-9
        assert result[1].period_label == "2026-03-13"
        assert result[1].call_count == 1
        assert abs(result[1].total_cost_usd - 0.30) < 1e-9

    def test_invalid_bucket_size_raises(self) -> None:
        """Invalid bucket_size raises ValueError."""
        with pytest.raises(ValueError, match="Invalid bucket_size"):
            aggregate_by_timeline([], "weekly")

    def test_top_operation(self) -> None:
        """top_operation is the most expensive operation in each bucket."""
        entries = [
            _make_entry("cheap_op", "2026-03-13T14:00:00", cost_usd=0.05),
            _make_entry("expensive_op", "2026-03-13T14:30:00", cost_usd=0.50),
            _make_entry("medium_op", "2026-03-13T14:45:00", cost_usd=0.20),
        ]

        result = aggregate_by_timeline(entries, "hourly")

        assert len(result) == 1
        assert result[0].top_operation == "expensive_op"


class TestNormalizeEntry:
    """Tests for _normalize_entry and old-format backward compatibility."""

    def test_normalizes_verbose_keys_to_lean(self) -> None:
        """Old verbose-key entries are normalized to lean keys."""
        old_entry = {
            "timestamp": "2026-03-13T10:00:00",
            "operation": "full_pulse",
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 8000,
            "cost_usd": 0.05,
            "elapsed_s": 3.0,
            "tool_starts": 1,
        }
        result = _normalize_entry(old_entry)
        assert result["ts"] == "2026-03-13T10:00:00"
        assert result["op"] == "full_pulse"
        assert result["in"] == 100
        assert result["out"] == 50
        assert result["cache_in"] == 0
        assert result["cache_read"] == 8000
        assert result["cost"] == 0.05
        assert result["dur"] == 3.0
        assert result["model"] == "unknown"
        assert result["rid"] == "unknown"

    def test_lean_keys_unchanged(self) -> None:
        """Already-lean entries pass through without modification."""
        lean_entry = _make_entry("test_op", "2026-03-13T10:00:00", model="sonnet")
        result = _normalize_entry(lean_entry)
        assert result["op"] == "test_op"
        assert result["model"] == "sonnet"

    def test_old_format_entries_load_correctly(self, tmp_path: Path) -> None:
        """Old-format JSONL entries are normalized when loaded."""
        old_entry = {
            "timestamp": "2026-03-13T10:00:00",
            "operation": "full_pulse",
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 8000,
            "cost_usd": 0.05,
            "elapsed_s": 3.0,
            "tool_starts": 1,
        }
        log_file = tmp_path / "usage.jsonl"
        _write_jsonl(log_file, [old_entry])

        result = load_usage_log(log_file, None)
        assert len(result) == 1
        assert result[0]["op"] == "full_pulse"
        assert result[0]["ts"] == "2026-03-13T10:00:00"
        assert result[0]["model"] == "unknown"
        assert result[0]["rid"] == "unknown"
