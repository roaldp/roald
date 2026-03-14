"""Unit tests for token consumption tracking and logging helpers in pulse.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/Users/roaldp/conductor/workspaces/roald/missoula")
import pulse


# ---------------------------------------------------------------------------
# 1. _estimate_tokens
# ---------------------------------------------------------------------------

class TestEstimateTokens:
    def test_empty_string(self):
        assert pulse._estimate_tokens("") == 0

    def test_four_chars(self):
        assert pulse._estimate_tokens("abcd") == 1

    def test_three_chars_integer_division(self):
        assert pulse._estimate_tokens("abc") == 0

    def test_longer_text(self):
        text = "a" * 100
        assert pulse._estimate_tokens(text) == 25

    def test_seven_chars(self):
        assert pulse._estimate_tokens("abcdefg") == 1


# ---------------------------------------------------------------------------
# 2. _measure_content_chars
# ---------------------------------------------------------------------------

class TestMeasureContentChars:
    def test_string_input(self):
        assert pulse._measure_content_chars("hello") == 5

    def test_list_of_strings(self):
        assert pulse._measure_content_chars(["abc", "de"]) == 5

    def test_list_of_dicts_with_text(self):
        content = [{"text": "hello"}, {"text": "world"}]
        assert pulse._measure_content_chars(content) == 10

    def test_mixed_list(self):
        content = ["abc", {"text": "de"}]
        assert pulse._measure_content_chars(content) == 5

    def test_empty_list(self):
        assert pulse._measure_content_chars([]) == 0

    def test_none(self):
        assert pulse._measure_content_chars(None) == 0

    def test_integer(self):
        assert pulse._measure_content_chars(42) == 0

    def test_dict_without_text_key(self):
        content = [{"other": "value"}]
        assert pulse._measure_content_chars(content) == 0

    def test_empty_string_input(self):
        assert pulse._measure_content_chars("") == 0


# ---------------------------------------------------------------------------
# 3. _build_tools_summary
# ---------------------------------------------------------------------------

class TestBuildToolsSummary:
    def test_single_tool_one_call_one_result(self):
        calls = {
            "id1": {"name": "Read", "input_chars": 50},
        }
        results = [
            pulse.ToolResultMetrics(
                tool_id="id1",
                tool_name="Read",
                result_chars=200,
                result_est_tokens=50,
                is_error=False,
            ),
        ]
        summary = pulse._build_tools_summary(calls, results)
        assert len(summary) == 1
        assert summary[0]["tool_name"] == "Read"
        assert summary[0]["call_count"] == 1
        assert summary[0]["total_input_chars"] == 50
        assert summary[0]["total_result_chars"] == 200
        assert summary[0]["total_result_est_tokens"] == 50
        assert summary[0]["error_count"] == 0

    def test_multiple_tools_aggregated(self):
        calls = {
            "id1": {"name": "Read", "input_chars": 10},
            "id2": {"name": "Read", "input_chars": 20},
            "id3": {"name": "Grep", "input_chars": 30},
        }
        results = [
            pulse.ToolResultMetrics(
                tool_id="id1", tool_name="Read",
                result_chars=100, result_est_tokens=25, is_error=False,
            ),
            pulse.ToolResultMetrics(
                tool_id="id2", tool_name="Read",
                result_chars=200, result_est_tokens=50, is_error=False,
            ),
            pulse.ToolResultMetrics(
                tool_id="id3", tool_name="Grep",
                result_chars=50, result_est_tokens=12, is_error=False,
            ),
        ]
        summary = pulse._build_tools_summary(calls, results)
        assert len(summary) == 2
        # Sorted by total_result_chars descending: Read(300) > Grep(50)
        assert summary[0]["tool_name"] == "Read"
        assert summary[0]["call_count"] == 2
        assert summary[0]["total_input_chars"] == 30
        assert summary[0]["total_result_chars"] == 300
        assert summary[1]["tool_name"] == "Grep"
        assert summary[1]["total_result_chars"] == 50

    def test_tool_in_results_not_in_calls(self):
        calls = {}
        results = [
            pulse.ToolResultMetrics(
                tool_id="id1", tool_name="Write",
                result_chars=100, result_est_tokens=25, is_error=False,
            ),
        ]
        summary = pulse._build_tools_summary(calls, results)
        assert len(summary) == 1
        assert summary[0]["tool_name"] == "Write"
        assert summary[0]["call_count"] == 0
        assert summary[0]["total_result_chars"] == 100

    def test_tool_in_calls_not_in_results(self):
        calls = {
            "id1": {"name": "Edit", "input_chars": 40},
        }
        results = []
        summary = pulse._build_tools_summary(calls, results)
        assert len(summary) == 1
        assert summary[0]["tool_name"] == "Edit"
        assert summary[0]["call_count"] == 1
        assert summary[0]["total_result_chars"] == 0

    def test_error_counting(self):
        calls = {
            "id1": {"name": "Read", "input_chars": 10},
        }
        results = [
            pulse.ToolResultMetrics(
                tool_id="id1", tool_name="Read",
                result_chars=0, result_est_tokens=0, is_error=True,
            ),
        ]
        summary = pulse._build_tools_summary(calls, results)
        assert summary[0]["error_count"] == 1

    def test_sorted_by_result_chars_descending(self):
        calls = {
            "id1": {"name": "A", "input_chars": 0},
            "id2": {"name": "B", "input_chars": 0},
            "id3": {"name": "C", "input_chars": 0},
        }
        results = [
            pulse.ToolResultMetrics(
                tool_id="id1", tool_name="A",
                result_chars=10, result_est_tokens=2, is_error=False,
            ),
            pulse.ToolResultMetrics(
                tool_id="id2", tool_name="B",
                result_chars=300, result_est_tokens=75, is_error=False,
            ),
            pulse.ToolResultMetrics(
                tool_id="id3", tool_name="C",
                result_chars=50, result_est_tokens=12, is_error=False,
            ),
        ]
        summary = pulse._build_tools_summary(calls, results)
        names = [s["tool_name"] for s in summary]
        assert names == ["B", "C", "A"]

    def test_empty_inputs(self):
        summary = pulse._build_tools_summary({}, [])
        assert summary == []


# ---------------------------------------------------------------------------
# 4. _write_detail_record
# ---------------------------------------------------------------------------

class TestWriteDetailRecord:
    def test_writes_valid_json_line(self, tmp_path, monkeypatch):
        log_file = tmp_path / "logs" / "detail.jsonl"
        monkeypatch.setattr(pulse, "DETAIL_LOG_PATH", log_file)

        record = {"v": 1, "rid": "test", "ts": "2026-03-14T10:00:00"}
        pulse._write_detail_record(record)

        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["rid"] == "test"

    def test_appends_not_overwrites(self, tmp_path, monkeypatch):
        log_file = tmp_path / "logs" / "detail.jsonl"
        monkeypatch.setattr(pulse, "DETAIL_LOG_PATH", log_file)

        pulse._write_detail_record({"v": 1, "rid": "first"})
        pulse._write_detail_record({"v": 1, "rid": "second"})

        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["rid"] == "first"
        assert json.loads(lines[1])["rid"] == "second"

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        log_file = tmp_path / "deep" / "nested" / "detail.jsonl"
        monkeypatch.setattr(pulse, "DETAIL_LOG_PATH", log_file)

        pulse._write_detail_record({"v": 1, "rid": "nested"})

        assert log_file.exists()
        parsed = json.loads(log_file.read_text().strip())
        assert parsed["rid"] == "nested"


# ---------------------------------------------------------------------------
# 5. _short_text
# ---------------------------------------------------------------------------

class TestShortText:
    def test_shorter_than_limit(self):
        assert pulse._short_text("hello", 10) == "hello"

    def test_longer_than_limit_truncated(self):
        result = pulse._short_text("a" * 20, 10)
        assert result == "a" * 10 + "..."

    def test_newlines_replaced_with_spaces(self):
        result = pulse._short_text("hello\nworld", 160)
        assert "\n" not in result
        assert "hello world" == result

    def test_none_value(self):
        result = pulse._short_text(None, 160)
        assert result == ""

    def test_default_limit_160(self):
        short_text = "a" * 100
        assert pulse._short_text(short_text) == short_text

        long_text = "a" * 200
        result = pulse._short_text(long_text)
        assert len(result) == 163  # 160 + "..."
        assert result.endswith("...")

    def test_exact_limit_length(self):
        text = "a" * 10
        assert pulse._short_text(text, 10) == text


# ---------------------------------------------------------------------------
# 6. _short_json
# ---------------------------------------------------------------------------

class TestShortJson:
    def test_dict_serialized_and_truncated(self):
        value = {"key": "a" * 300}
        result = pulse._short_json(value, 50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_dict_short_enough(self):
        value = {"k": "v"}
        result = pulse._short_json(value, 240)
        assert result == '{"k":"v"}'

    def test_non_serializable_falls_back_to_str(self):
        value = object()
        result = pulse._short_json(value, 240)
        # Should not raise; falls back to str()
        assert isinstance(result, str)

    def test_uses_short_text_internally(self):
        # Newlines in serialized JSON should be replaced
        value = {"text": "hello\nworld"}
        result = pulse._short_json(value, 240)
        assert "\n" not in result
