"""Unit tests for token monitoring helpers in pulse.py.

- Tests for _extract_usage (TokenUsage extraction from stream-json events)
- Tests for _log_token_usage (JSONL logging)
- Tests for _short_text, _short_json, is_claude_echo_message
- Tests for _token_totals accumulation
"""

import json
from unittest.mock import patch

import pytest

import pulse
from pulse import (
    TokenUsage,
    _extract_usage,
    _log_token_usage,
    _short_text,
    _short_json,
    is_claude_echo_message,
)


class TestExtractUsage:
    """Tests for _extract_usage."""

    def test_valid_result_event(self) -> None:
        event = {
            "type": "result",
            "total_cost_usd": 0.0081575,
            "duration_ms": 2209,
            "usage": {
                "input_tokens": 3,
                "output_tokens": 5,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 16035,
            },
        }
        usage = _extract_usage(event)
        assert usage.input_tokens == 3
        assert usage.output_tokens == 5
        assert usage.cache_creation_input_tokens == 0
        assert usage.cache_read_input_tokens == 16035
        assert usage.cost_usd == pytest.approx(0.0081575)

    def test_missing_usage_field(self) -> None:
        event = {"type": "result", "total_cost_usd": 0.01}
        usage = _extract_usage(event)
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.cache_creation_input_tokens == 0
        assert usage.cache_read_input_tokens == 0
        assert usage.cost_usd == pytest.approx(0.01)

    def test_partial_usage_field(self) -> None:
        event = {
            "type": "result",
            "usage": {"input_tokens": 10},
        }
        usage = _extract_usage(event)
        assert usage.input_tokens == 10
        assert usage.output_tokens == 0
        assert usage.cache_creation_input_tokens == 0
        assert usage.cache_read_input_tokens == 0
        assert usage.cost_usd == 0.0

    def test_malformed_event(self) -> None:
        usage = _extract_usage("not a dict")  # type: ignore[arg-type]
        assert usage == TokenUsage(0, 0, 0, 0, 0.0)


class TestLogTokenUsage:
    """Tests for _log_token_usage."""

    def test_writes_valid_jsonl(self, tmp_path: "pytest.TempPathFactory") -> None:
        log_file = tmp_path / "token_usage.jsonl"
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=8000,
            cost_usd=0.005,
        )
        with patch("pulse.TOKEN_USAGE_LOG_PATH", log_file):
            _log_token_usage("test_op", usage, elapsed=2.5, model="test_model")

        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["op"] == "test_op"
        assert record["model"] == "test_model"
        assert record["in"] == 100
        assert record["out"] == 50
        assert record["cache_read"] == 8000
        assert record["cost"] == pytest.approx(0.005)
        assert record["dur"] == pytest.approx(2.5)
        assert "ts" in record
        assert "rid" in record

    def test_handles_write_error(self) -> None:
        usage = TokenUsage(0, 0, 0, 0, 0.0)
        with patch("builtins.open", side_effect=OSError("disk full")):
            # Should not raise
            _log_token_usage("test_op", usage, elapsed=1.0)

    def test_includes_model_and_run_id(self, tmp_path: "pytest.TempPathFactory") -> None:
        log_file = tmp_path / "token_usage.jsonl"
        usage = TokenUsage(10, 5, 0, 100, 0.01)
        with patch("pulse.TOKEN_USAGE_LOG_PATH", log_file):
            _log_token_usage("test_op", usage, elapsed=1.0, model="sonnet")

        record = json.loads(log_file.read_text().strip())
        assert record["model"] == "sonnet"
        assert "rid" in record
        import re
        assert re.match(r"^\d{8}T\d{6}$", record["rid"])

    def test_default_model_when_not_provided(self, tmp_path: "pytest.TempPathFactory") -> None:
        log_file = tmp_path / "token_usage.jsonl"
        usage = TokenUsage(10, 5, 0, 100, 0.01)
        with patch("pulse.TOKEN_USAGE_LOG_PATH", log_file):
            _log_token_usage("test_op", usage, elapsed=1.0)

        record = json.loads(log_file.read_text().strip())
        assert record["model"] == "unknown"


class TestShortText:
    """Tests for _short_text."""

    def test_short_text_unchanged(self) -> None:
        assert _short_text("hello", limit=10) == "hello"

    def test_text_at_limit_unchanged(self) -> None:
        text = "a" * 10
        assert _short_text(text, limit=10) == text

    def test_text_longer_than_limit_truncated(self) -> None:
        text = "a" * 20
        result = _short_text(text, limit=10)
        assert result == "a" * 10 + "..."

    def test_none_input(self) -> None:
        assert _short_text(None) == ""

    def test_empty_input(self) -> None:
        assert _short_text("") == ""

    def test_newlines_replaced_with_spaces(self) -> None:
        result = _short_text("line1\nline2\nline3")
        assert "\n" not in result
        assert "line1 line2 line3" == result


class TestShortJson:
    """Tests for _short_json."""

    def test_dict_serialized_to_compact_json(self) -> None:
        result = _short_json({"key": "value"})
        assert result == '{"key":"value"}'

    def test_non_serializable_falls_back_to_str(self) -> None:
        obj = object()
        result = _short_json(obj)
        # Falls back to str(obj), which starts with "<object object at"
        assert result.startswith("<object object at")

    def test_truncation_at_limit(self) -> None:
        big = {"k": "v" * 300}
        result = _short_json(big, limit=20)
        assert len(result) == 20 + len("...")
        assert result.endswith("...")


class TestIsClaudeEchoMessage:
    """Tests for is_claude_echo_message."""

    def test_sent_using_claude_returns_true(self) -> None:
        assert is_claude_echo_message("Sent using <@U123|Claude>") is True

    def test_plain_text_returns_false(self) -> None:
        assert is_claude_echo_message("Hey, how are you?") is False

    def test_empty_string_returns_false(self) -> None:
        assert is_claude_echo_message("") is False


class TestTokenTotalsAccumulation:
    """Tests for _token_totals accumulation via _log_token_usage."""

    @pytest.fixture(autouse=True)
    def reset_token_totals(self) -> None:
        pulse._token_totals.clear()

    def test_accumulates_cost_across_calls(self, tmp_path: "pytest.TempPathFactory") -> None:
        log_file = tmp_path / "token_usage.jsonl"
        usage1 = TokenUsage(10, 5, 0, 100, 0.01)
        usage2 = TokenUsage(20, 10, 0, 200, 0.02)

        with patch("pulse.TOKEN_USAGE_LOG_PATH", log_file):
            _log_token_usage("my_op", usage1, elapsed=1.0)
            _log_token_usage("my_op", usage2, elapsed=1.0)

        assert pulse._token_totals["my_op"] == pytest.approx(0.03)

    def test_separate_operations_tracked_independently(self, tmp_path: "pytest.TempPathFactory") -> None:
        log_file = tmp_path / "token_usage.jsonl"
        usage_a = TokenUsage(10, 5, 0, 100, 0.01)
        usage_b = TokenUsage(20, 10, 0, 200, 0.05)

        with patch("pulse.TOKEN_USAGE_LOG_PATH", log_file):
            _log_token_usage("op_a", usage_a, elapsed=1.0)
            _log_token_usage("op_b", usage_b, elapsed=1.0)

        assert pulse._token_totals["op_a"] == pytest.approx(0.01)
        assert pulse._token_totals["op_b"] == pytest.approx(0.05)
