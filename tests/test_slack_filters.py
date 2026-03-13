"""Unit tests for Slack self-reply prevention and debounce logic in pulse.py."""

import asyncio
import sys
import time
from collections import deque
from unittest import mock

import pytest

# Import pulse from the philadelphia workspace
sys.path.insert(0, "/Users/roaldp/conductor/workspaces/roald/philadelphia")
import pulse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_sent_messages():
    """Clear the module-global _sent_messages deque before and after each test."""
    pulse._sent_messages.clear()
    yield
    pulse._sent_messages.clear()


# ---------------------------------------------------------------------------
# 1. _normalize_slack_text
# ---------------------------------------------------------------------------

class TestNormalizeSlackText:
    def test_plain_text_lowered_and_stripped(self):
        assert pulse._normalize_slack_text("  Hello World  ") == "hello world"

    def test_strips_footer_with_display_name(self):
        text = "Hello there\nSent using <@U123|Claude>"
        assert pulse._normalize_slack_text(text) == "hello there"

    def test_strips_footer_without_display_name(self):
        text = "Hello there\nSent using <@U123>"
        assert pulse._normalize_slack_text(text) == "hello there"

    def test_strips_generic_sent_using_suffix(self):
        text = "Hi\n\nSent using some app"
        assert pulse._normalize_slack_text(text) == "hi"

    def test_empty_string(self):
        assert pulse._normalize_slack_text("") == ""

    def test_strips_mention_mid_text(self):
        text = "Hey <@U456> check this"
        result = pulse._normalize_slack_text(text)
        # Mention is removed; exact whitespace may vary
        assert "u456" not in result
        assert "check this" in result

    def test_no_sent_using_returned_as_is(self):
        text = "Just a normal message"
        assert pulse._normalize_slack_text(text) == "just a normal message"


# ---------------------------------------------------------------------------
# 2. _is_own_outbound
# ---------------------------------------------------------------------------

class TestIsOwnOutbound:
    def test_exact_match_within_ttl(self):
        pulse._sent_messages.append(("hello world", time.monotonic()))
        assert pulse._is_own_outbound("Hello World") is True

    def test_exact_match_expired(self):
        # Place a message 120 seconds in the past
        pulse._sent_messages.append(("hello world", time.monotonic() - 120))
        assert pulse._is_own_outbound("Hello World") is False

    def test_inbound_starts_with_stored_prefix_match(self):
        pulse._sent_messages.append(("hello", time.monotonic()))
        # Inbound "hello world" starts with stored "hello" -> True
        assert pulse._is_own_outbound("Hello World") is True

    def test_stored_starts_with_inbound_should_be_false(self):
        # Stored is longer than inbound -- only normalized.startswith(sent_text) direction
        pulse._sent_messages.append(("hello world longer", time.monotonic()))
        assert pulse._is_own_outbound("Hello World") is False

    def test_empty_text_after_normalization(self):
        # Text that becomes empty after normalization (pure echo)
        text = "\nSent using <@U123|Claude>"
        assert pulse._is_own_outbound(text) is True

    def test_no_stored_messages(self):
        assert pulse._is_own_outbound("Hello World") is False

    def test_multiple_stored_one_matches(self):
        pulse._sent_messages.append(("no match here", time.monotonic()))
        pulse._sent_messages.append(("hello world", time.monotonic()))
        pulse._sent_messages.append(("also no match", time.monotonic()))
        assert pulse._is_own_outbound("Hello World") is True

    def test_no_match_in_stored(self):
        pulse._sent_messages.append(("something else", time.monotonic()))
        pulse._sent_messages.append(("another thing", time.monotonic()))
        assert pulse._is_own_outbound("Hello World") is False

    def test_ttl_boundary_with_mocked_time(self):
        """Test TTL boundary precisely using mocked time.monotonic."""
        base_time = 1000.0
        pulse._sent_messages.append(("hello", base_time))

        # At exactly TTL seconds later -> should be expired (> TTL)
        with mock.patch("pulse.time") as mock_time:
            mock_time.monotonic.return_value = base_time + pulse._SENT_MSG_TTL + 0.001
            assert pulse._is_own_outbound("Hello") is False

        # Just under TTL -> should match
        with mock.patch("pulse.time") as mock_time:
            mock_time.monotonic.return_value = base_time + pulse._SENT_MSG_TTL - 0.001
            assert pulse._is_own_outbound("Hello") is True


# ---------------------------------------------------------------------------
# 3. is_claude_echo_message
# ---------------------------------------------------------------------------

class TestIsClaudeEchoMessage:
    def test_sent_using_claude_markup(self):
        assert pulse.is_claude_echo_message("Hello\nSent using <@U123|Claude>") is True

    def test_sent_using_without_claude(self):
        assert pulse.is_claude_echo_message("Hello\nSent using <@U123>") is False

    def test_plain_text(self):
        assert pulse.is_claude_echo_message("Hello there") is False

    def test_both_words_present_anywhere(self):
        assert pulse.is_claude_echo_message("I was sent using claude yesterday") is True

    def test_empty_string(self):
        assert pulse.is_claude_echo_message("") is False


# ---------------------------------------------------------------------------
# 4. Debounce logic in slack_loop (state machine tests)
# ---------------------------------------------------------------------------

class TestSlackLoopDebounce:
    """Test the debounce and filtering logic inside slack_loop.

    We mock poll_slack_messages to return controlled sequences, and mock
    run_reactive_pulse / handle_update_command to track calls.
    """

    def _make_msg(self, ts: str, user: str, text: str) -> dict:
        return {"ts": ts, "user": user, "text": text}

    def _run_loop(self, coro, timeout=5.0):
        """Run an async coroutine with a timeout to prevent hangs."""
        async def _with_timeout():
            return await asyncio.wait_for(coro, timeout=timeout)
        return asyncio.run(_with_timeout())

    def test_single_message_debounce_then_fire(self):
        """Single message -> debounce_remaining=2 -> 2 empty polls -> pulse fires."""
        config = {
            "slack_poll_interval_seconds": 0,
            "slack_user_id": "U_USER",
            "slack_channel_id": "D_CHAN",
        }

        poll_results = [
            # Poll 1: initial calibration (sets last_ts)
            [self._make_msg("1.0", "U_USER", "Hi there")],
            # Poll 2: new message arrives
            [
                self._make_msg("1.0", "U_USER", "Hi there"),
                self._make_msg("2.0", "U_USER", "Please help"),
            ],
            # Poll 3: no new messages (debounce tick 1)
            [self._make_msg("2.0", "U_USER", "Please help")],
            # Poll 4: no new messages (debounce tick 2 -> fires)
            [self._make_msg("2.0", "U_USER", "Please help")],
            # Poll 5: empty to let debounce fire
            [],
        ]
        poll_iter = iter(poll_results)
        call_count = 0

        async def fake_sleep(_):
            nonlocal call_count
            call_count += 1
            if call_count > len(poll_results):
                raise asyncio.CancelledError("stop loop")

        reactive_calls = []

        async def fake_reactive(cfg, text):
            reactive_calls.append(text)
            raise asyncio.CancelledError("stop after pulse")

        async def fake_handle_update(cfg, text):
            return False

        with mock.patch("pulse.poll_slack_messages", side_effect=lambda c, ch: next(poll_iter, [])), \
             mock.patch("pulse.asyncio.sleep", side_effect=fake_sleep), \
             mock.patch("pulse.run_reactive_pulse", side_effect=fake_reactive), \
             mock.patch("pulse.handle_update_command", side_effect=fake_handle_update), \
             mock.patch("pulse.is_valid_pollable_slack_channel", return_value=True), \
             mock.patch("pulse.slack_channel", return_value="D_CHAN"):
            with pytest.raises(asyncio.CancelledError):
                self._run_loop(pulse.slack_loop(config))

        assert len(reactive_calls) == 1
        assert "Please help" in reactive_calls[0]

    def test_burst_messages_batched(self):
        """Burst of messages across 2 polls -> all batched into one pulse call."""
        config = {
            "slack_poll_interval_seconds": 0,
            "slack_user_id": "U_USER",
            "slack_channel_id": "D_CHAN",
        }

        poll_results = [
            # Poll 1: calibration
            [self._make_msg("1.0", "U_USER", "old msg")],
            # Poll 2: two new messages
            [
                self._make_msg("1.0", "U_USER", "old msg"),
                self._make_msg("2.0", "U_USER", "msg A"),
                self._make_msg("3.0", "U_USER", "msg B"),
            ],
            # Poll 3: one more new message (burst continues)
            [
                self._make_msg("2.0", "U_USER", "msg A"),
                self._make_msg("3.0", "U_USER", "msg B"),
                self._make_msg("4.0", "U_USER", "msg C"),
            ],
            # Poll 4: no new messages (debounce tick 1)
            [self._make_msg("4.0", "U_USER", "msg C")],
            # Poll 5: no new messages (debounce tick 2 -> fires)
            [self._make_msg("4.0", "U_USER", "msg C")],
            # Poll 6: empty to flush
            [],
        ]
        poll_iter = iter(poll_results)
        call_count = 0

        async def fake_sleep(_):
            nonlocal call_count
            call_count += 1
            if call_count > len(poll_results):
                raise asyncio.CancelledError("stop loop")

        reactive_calls = []

        async def fake_reactive(cfg, text):
            reactive_calls.append(text)
            raise asyncio.CancelledError("stop after pulse")

        async def fake_handle_update(cfg, text):
            return False

        with mock.patch("pulse.poll_slack_messages", side_effect=lambda c, ch: next(poll_iter, [])), \
             mock.patch("pulse.asyncio.sleep", side_effect=fake_sleep), \
             mock.patch("pulse.run_reactive_pulse", side_effect=fake_reactive), \
             mock.patch("pulse.handle_update_command", side_effect=fake_handle_update), \
             mock.patch("pulse.is_valid_pollable_slack_channel", return_value=True), \
             mock.patch("pulse.slack_channel", return_value="D_CHAN"):
            with pytest.raises(asyncio.CancelledError):
                self._run_loop(pulse.slack_loop(config))

        assert len(reactive_calls) == 1
        combined = reactive_calls[0]
        assert "msg A" in combined
        assert "msg B" in combined
        assert "msg C" in combined

    def test_last_ts_advances_on_new_messages(self):
        """last_ts advances when messages are moved to pending, not when pulse fires."""
        config = {
            "slack_poll_interval_seconds": 0,
            "slack_user_id": "U_USER",
            "slack_channel_id": "D_CHAN",
        }

        # We track what messages are seen as "new" on each poll
        poll_results = [
            # Poll 1: calibration, last_ts = 1.0
            [self._make_msg("1.0", "U_USER", "init")],
            # Poll 2: new msg at ts=2.0, last_ts should advance to 2.0
            [
                self._make_msg("1.0", "U_USER", "init"),
                self._make_msg("2.0", "U_USER", "first"),
            ],
            # Poll 3: same ts=2.0 as newest -> no new messages
            # (proves last_ts was advanced to 2.0 during poll 2, not deferred)
            [self._make_msg("2.0", "U_USER", "first")],
            # Poll 4: no new -> debounce fires
            [self._make_msg("2.0", "U_USER", "first")],
            [],
        ]
        poll_iter = iter(poll_results)
        call_count = 0

        async def fake_sleep(_):
            nonlocal call_count
            call_count += 1
            if call_count > len(poll_results):
                raise asyncio.CancelledError("stop loop")

        reactive_calls = []

        async def fake_reactive(cfg, text):
            reactive_calls.append(text)
            raise asyncio.CancelledError("stop after pulse")

        async def fake_handle_update(cfg, text):
            return False

        with mock.patch("pulse.poll_slack_messages", side_effect=lambda c, ch: next(poll_iter, [])), \
             mock.patch("pulse.asyncio.sleep", side_effect=fake_sleep), \
             mock.patch("pulse.run_reactive_pulse", side_effect=fake_reactive), \
             mock.patch("pulse.handle_update_command", side_effect=fake_handle_update), \
             mock.patch("pulse.is_valid_pollable_slack_channel", return_value=True), \
             mock.patch("pulse.slack_channel", return_value="D_CHAN"):
            with pytest.raises(asyncio.CancelledError):
                self._run_loop(pulse.slack_loop(config))

        # Only "first" should appear (not duplicated)
        assert len(reactive_calls) == 1
        assert reactive_calls[0] == "first"

    def test_own_outbound_filtered(self):
        """Bot's own outbound messages are filtered and don't end up in pending_texts."""
        config = {
            "slack_poll_interval_seconds": 0,
            "slack_user_id": "U_USER",
            "slack_channel_id": "D_CHAN",
        }

        # Pre-populate _sent_messages so "bot reply" is recognized as own outbound
        pulse._sent_messages.append(
            (pulse._normalize_slack_text("Bot reply"), time.monotonic())
        )

        poll_results = [
            # Poll 1: calibration
            [self._make_msg("1.0", "U_USER", "init")],
            # Poll 2: a user message + a bot echo
            [
                self._make_msg("1.0", "U_USER", "init"),
                self._make_msg("2.0", "U_USER", "real question"),
                self._make_msg("3.0", "U_USER", "Bot reply"),
            ],
            # Poll 3-4: debounce
            [self._make_msg("3.0", "U_USER", "Bot reply")],
            [self._make_msg("3.0", "U_USER", "Bot reply")],
            [],
        ]
        poll_iter = iter(poll_results)
        call_count = 0

        async def fake_sleep(_):
            nonlocal call_count
            call_count += 1
            if call_count > len(poll_results):
                raise asyncio.CancelledError("stop loop")

        reactive_calls = []

        async def fake_reactive(cfg, text):
            reactive_calls.append(text)
            raise asyncio.CancelledError("stop after pulse")

        async def fake_handle_update(cfg, text):
            return False

        with mock.patch("pulse.poll_slack_messages", side_effect=lambda c, ch: next(poll_iter, [])), \
             mock.patch("pulse.asyncio.sleep", side_effect=fake_sleep), \
             mock.patch("pulse.run_reactive_pulse", side_effect=fake_reactive), \
             mock.patch("pulse.handle_update_command", side_effect=fake_handle_update), \
             mock.patch("pulse.is_valid_pollable_slack_channel", return_value=True), \
             mock.patch("pulse.slack_channel", return_value="D_CHAN"):
            with pytest.raises(asyncio.CancelledError):
                self._run_loop(pulse.slack_loop(config))

        # Only the real question should make it through
        assert len(reactive_calls) == 1
        assert "real question" in reactive_calls[0]
        assert "Bot reply" not in reactive_calls[0]
