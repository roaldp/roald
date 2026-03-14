#!/usr/bin/env python3
"""CLI script to analyze pulse_detail.jsonl and produce token usage reports.

- Reads per-invocation detail records from logs/pulse_detail.jsonl
- Provides subcommands: summary, tools, biggest, models
- Uses plain formatted output (no external table libraries)
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================

LOG_FILE = Path(__file__).parent.parent / "logs" / "pulse_detail.jsonl"
CHARS_PER_TOKEN = 4  # rough approximation used throughout


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_records(since: str | None = None) -> list[dict]:
    """Load PulseDetailRecord entries from the JSONL log file.

    Args:
        since: Optional date string (YYYY-MM-DD). If provided, only records
            with ts >= that date are returned.

    Returns:
        List of parsed PulseDetailRecord dicts, sorted by timestamp ascending.

    Raises:
        SystemExit: If the log file does not exist or is empty.
    """
    if not LOG_FILE.exists():
        print(f"Error: log file not found: {LOG_FILE}")
        raise SystemExit(1)

    records: list[dict] = []
    with open(LOG_FILE) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed line {line_num}: {e}")

    if not records:
        print("No records found in log file.")
        raise SystemExit(1)

    if since:
        since_dt = _parse_date(since)
        records = [r for r in records if _record_ts(r) >= since_dt]
        if not records:
            print(f"No records found since {since}.")
            raise SystemExit(1)

    records.sort(key=lambda r: r.get("ts", ""))
    return records


def _parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime at midnight.

    Args:
        date_str: Date in YYYY-MM-DD format.

    Returns:
        datetime object at 00:00:00 of the given date.

    Raises:
        SystemExit: If the date string is not valid.
    """
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        print(f"Error: invalid date format '{date_str}', expected YYYY-MM-DD")
        raise SystemExit(1)


def _record_ts(record: dict) -> datetime:
    """Extract the timestamp from a record as a datetime.

    Args:
        record: A PulseDetailRecord dict.

    Returns:
        Parsed datetime from the record's ts field.
    """
    return datetime.fromisoformat(record["ts"])


def _fmt_tokens(n: int) -> str:
    """Format a token count with K suffix for readability.

    Args:
        n: Token count.

    Returns:
        Formatted string like '15.2K' or '832'.
    """
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def _fmt_cost(usd: float) -> str:
    """Format a USD cost value.

    Args:
        usd: Cost in USD.

    Returns:
        Formatted string like '$0.0342'.
    """
    return f"${usd:.4f}"


def _short_ts(ts_str: str) -> str:
    """Shorten an ISO timestamp to MM-DD HH:MM.

    Args:
        ts_str: ISO format timestamp string.

    Returns:
        Short timestamp string.
    """
    dt = datetime.fromisoformat(ts_str)
    return dt.strftime("%m-%d %H:%M")


# ============================================================================
# SUBCOMMAND FUNCTIONS
# ============================================================================

def cmd_summary(args: argparse.Namespace) -> None:
    """Show per-invocation summary table with sanity-check column.

    Displays: timestamp, operation, cost, total tokens (input+output),
    duration, tool count, and a delta between summed per-turn output_tokens
    vs the aggregate output_tokens from the result event.

    Args:
        args: Parsed CLI args with 'since' and 'limit' attributes.
    """
    records = load_records(since=args.since)
    if args.limit:
        records = records[-args.limit :]

    # Header
    header = (
        f"{'Timestamp':<14} {'Operation':<20} {'Cost':>9} "
        f"{'In Tok':>9} {'Out Tok':>9} {'Dur(s)':>7} "
        f"{'Tools':>6} {'Out Chk':>9}"
    )
    print(header)
    print("-" * len(header))

    for r in records:
        usage = r.get("usage", {})
        in_tok = usage.get("input_tokens", 0)
        out_tok = usage.get("output_tokens", 0)

        # Sanity check: sum per-turn output_tokens vs aggregate
        turns = r.get("turns", [])
        summed_out = sum(
            t.get("output_tokens", 0)
            for t in turns
            if t.get("role") == "assistant"
        )
        # Show delta; "n/a" if turns array is missing/empty
        if turns:
            delta = out_tok - summed_out
            chk = f"{delta:+d}" if delta != 0 else "ok"
        else:
            chk = "n/a"

        tools_summary = r.get("tools_summary", [])
        tool_count = sum(t.get("call_count", 0) for t in tools_summary)

        print(
            f"{_short_ts(r.get('ts', '')):<14} {r.get('op', '?'):<20} "
            f"{_fmt_cost(r.get('total_cost_usd', 0)):>9} "
            f"{_fmt_tokens(in_tok):>9} {_fmt_tokens(out_tok):>9} "
            f"{r.get('dur_s', 0):>7.1f} "
            f"{tool_count:>6} {chk:>9}"
        )


def cmd_tools(args: argparse.Namespace) -> None:
    """Show per-tool breakdown across all invocations.

    Aggregates by tool name: total calls, total result chars, estimated
    tokens, and error count.

    Args:
        args: Parsed CLI args with 'since' and 'op' attributes.
    """
    records = load_records(since=args.since)
    if args.op:
        records = [r for r in records if r.get("op") == args.op]
        if not records:
            print(f"No records found for operation '{args.op}'.")
            raise SystemExit(1)

    # Aggregate across all invocations
    agg: dict[str, dict] = {}
    for r in records:
        for ts in r.get("tools_summary", []):
            name = ts.get("tool_name", "?")
            if name not in agg:
                agg[name] = {
                    "call_count": 0,
                    "total_input_chars": 0,
                    "total_result_chars": 0,
                    "total_result_est_tokens": 0,
                    "error_count": 0,
                }
            agg[name]["call_count"] += ts.get("call_count", 0)
            agg[name]["total_input_chars"] += ts.get("total_input_chars", 0)
            agg[name]["total_result_chars"] += ts.get("total_result_chars", 0)
            agg[name]["total_result_est_tokens"] += ts.get("total_result_est_tokens", 0)
            agg[name]["error_count"] += ts.get("error_count", 0)

    if not agg:
        print("No tool data found.")
        raise SystemExit(1)

    # Sort by estimated tokens descending
    sorted_tools = sorted(agg.items(), key=lambda x: x[1]["total_result_est_tokens"], reverse=True)

    header = (
        f"{'Tool':<40} {'Calls':>6} {'Result Chars':>13} "
        f"{'Est Tokens':>11} {'Errors':>7}"
    )
    print(header)
    print("-" * len(header))

    for name, data in sorted_tools:
        print(
            f"{name:<40} {data['call_count']:>6} "
            f"{data['total_result_chars']:>13,} "
            f"{_fmt_tokens(data['total_result_est_tokens']):>11} "
            f"{data['error_count']:>7}"
        )

    # Totals
    total_calls = sum(d["call_count"] for d in agg.values())
    total_chars = sum(d["total_result_chars"] for d in agg.values())
    total_est = sum(d["total_result_est_tokens"] for d in agg.values())
    total_errors = sum(d["error_count"] for d in agg.values())
    print("-" * len(header))
    print(
        f"{'TOTAL':<40} {total_calls:>6} "
        f"{total_chars:>13,} "
        f"{_fmt_tokens(total_est):>11} "
        f"{total_errors:>7}"
    )


def cmd_biggest(args: argparse.Namespace) -> None:
    """Show top N largest tool results by estimated tokens.

    Drills into individual tool results across all invocations to find
    the single largest context consumers.

    Args:
        args: Parsed CLI args with 'since' and 'top' attributes.
    """
    records = load_records(since=args.since)
    top_n = args.top

    # Collect individual tool results from turns data
    results: list[dict] = []
    for r in records:
        rid = r.get("rid", "?")
        op = r.get("op", "?")
        for turn in r.get("turns", []):
            for tr in turn.get("tool_results", []):
                results.append({
                    "rid": rid,
                    "op": op,
                    "turn": turn.get("turn", 0),
                    "tool_name": tr.get("tool_name", "?"),
                    "result_chars": tr.get("result_chars", 0),
                    "result_est_tokens": tr.get("result_est_tokens", 0),
                    "is_error": tr.get("is_error", False),
                })

    if not results:
        # Fall back to tools_summary if no per-turn data
        print("No per-turn tool result data available (turns may not be logged).")
        print("Falling back to tools_summary aggregates:\n")
        cmd_tools(args)
        return

    # Sort by est tokens descending, take top N
    results.sort(key=lambda x: x["result_est_tokens"], reverse=True)
    results = results[:top_n]

    header = (
        f"{'#':>3} {'Record':<18} {'Operation':<18} {'Turn':>5} "
        f"{'Tool':<35} {'Chars':>10} {'Est Tokens':>11}"
    )
    print(header)
    print("-" * len(header))

    for i, res in enumerate(results, 1):
        err_flag = " [ERR]" if res["is_error"] else ""
        print(
            f"{i:>3} {res['rid']:<18} {res['op']:<18} {res['turn']:>5} "
            f"{res['tool_name']:<35} {res['result_chars']:>10,} "
            f"{_fmt_tokens(res['result_est_tokens']):>11}{err_flag}"
        )


def cmd_models(args: argparse.Namespace) -> None:
    """Show per-model cost breakdown across invocations.

    Uses the model_usage dict from each record to attribute cost and
    token usage per model (parent vs sub-agent).

    Args:
        args: Parsed CLI args with 'since' attribute.
    """
    records = load_records(since=args.since)

    # Aggregate by model
    agg: dict[str, dict] = {}
    for r in records:
        for model, mu in r.get("model_usage", {}).items():
            if model not in agg:
                agg[model] = {
                    "invocations": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read": 0,
                    "cache_creation": 0,
                    "cost_usd": 0.0,
                }
            agg[model]["invocations"] += 1
            agg[model]["input_tokens"] += mu.get("input_tokens", 0)
            agg[model]["output_tokens"] += mu.get("output_tokens", 0)
            agg[model]["cache_read"] += mu.get("cache_read", 0)
            agg[model]["cache_creation"] += mu.get("cache_creation", 0)
            agg[model]["cost_usd"] += mu.get("cost_usd", 0.0)

    if not agg:
        print("No model usage data found.")
        raise SystemExit(1)

    # Sort by cost descending
    sorted_models = sorted(agg.items(), key=lambda x: x[1]["cost_usd"], reverse=True)

    total_cost = sum(d["cost_usd"] for d in agg.values())

    header = (
        f"{'Model':<30} {'Invoc':>6} {'In Tok':>10} {'Out Tok':>10} "
        f"{'Cache Rd':>10} {'Cost':>10} {'% Cost':>7}"
    )
    print(header)
    print("-" * len(header))

    for model, data in sorted_models:
        pct = (data["cost_usd"] / total_cost * 100) if total_cost > 0 else 0
        print(
            f"{model:<30} {data['invocations']:>6} "
            f"{_fmt_tokens(data['input_tokens']):>10} "
            f"{_fmt_tokens(data['output_tokens']):>10} "
            f"{_fmt_tokens(data['cache_read']):>10} "
            f"{_fmt_cost(data['cost_usd']):>10} "
            f"{pct:>6.1f}%"
        )

    print("-" * len(header))
    total_in = sum(d["input_tokens"] for d in agg.values())
    total_out = sum(d["output_tokens"] for d in agg.values())
    total_cache = sum(d["cache_read"] for d in agg.values())
    print(
        f"{'TOTAL':<30} {'':>6} "
        f"{_fmt_tokens(total_in):>10} "
        f"{_fmt_tokens(total_out):>10} "
        f"{_fmt_tokens(total_cache):>10} "
        f"{_fmt_cost(total_cost):>10} "
        f"{'100.0%':>7}"
    )


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main() -> None:
    """Parse arguments and dispatch to the appropriate subcommand."""
    parser = argparse.ArgumentParser(
        description="Analyze pulse_detail.jsonl token usage logs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # summary
    p_summary = subparsers.add_parser("summary", help="Per-invocation summary table")
    p_summary.add_argument("--since", type=str, default=None, help="Filter records since date (YYYY-MM-DD)")
    p_summary.add_argument("--limit", type=int, default=None, help="Show only last N records")
    p_summary.set_defaults(func=cmd_summary)

    # tools
    p_tools = subparsers.add_parser("tools", help="Per-tool breakdown across invocations")
    p_tools.add_argument("--since", type=str, default=None, help="Filter records since date (YYYY-MM-DD)")
    p_tools.add_argument("--op", type=str, default=None, help="Filter by operation name")
    p_tools.set_defaults(func=cmd_tools)

    # biggest
    p_biggest = subparsers.add_parser("biggest", help="Top N largest tool results")
    p_biggest.add_argument("--since", type=str, default=None, help="Filter records since date (YYYY-MM-DD)")
    p_biggest.add_argument("--top", type=int, default=10, help="Number of results to show (default: 10)")
    p_biggest.set_defaults(func=cmd_biggest)

    # models
    p_models = subparsers.add_parser("models", help="Per-model cost breakdown")
    p_models.add_argument("--since", type=str, default=None, help="Filter records since date (YYYY-MM-DD)")
    p_models.set_defaults(func=cmd_models)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
