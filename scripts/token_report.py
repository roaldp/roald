"""Token usage report generator.

Parses the token usage JSONL log produced by pulse.py and generates
a summary report showing cost and token consumption by operation.

Responsibilities:
- Load and filter JSONL token usage entries by time window
- Aggregate token counts and costs by operation name
- Print a human-readable table sorted by total cost descending
- Provide a CLI interface with --since flag for time filtering
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "token_usage.jsonl"

SINCE_PATTERN = re.compile(r"^(\d+)([mhd])$")

SINCE_MULTIPLIERS: dict[str, str] = {
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


# ============================================================================
# TYPES
# ============================================================================

@dataclass
class TimelineBucket:
    """Aggregated token usage for a single time period."""

    period_label: str
    total_cost_usd: float
    call_count: int
    top_operation: str


@dataclass
class OperationSummary:
    """Aggregated token usage for a single operation."""

    operation: str
    call_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_cache_tokens: int
    total_cost_usd: float
    avg_cost_per_call: float


@dataclass
class TokenReport:
    """Complete token usage report for a time period."""

    period: str
    operations: list[OperationSummary]
    grand_total_cost: float


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_since(since_str: str) -> datetime:
    """Parse a --since value like '1h', '24h', '7d', '30m' into a datetime.

    Args:
        since_str: Duration string with numeric value and suffix (m/h/d).

    Returns:
        A datetime representing now minus the specified duration.

    Raises:
        ValueError: If the format is not recognized.
    """
    match = SINCE_PATTERN.match(since_str)
    if not match:
        raise ValueError(
            f"Invalid --since format: '{since_str}'. "
            "Expected format like '30m', '1h', '24h', '7d'."
        )
    value = int(match.group(1))
    unit = match.group(2)
    delta = timedelta(**{SINCE_MULTIPLIERS[unit]: value})
    return datetime.now() - delta


_VERBOSE_TO_LEAN: dict[str, str] = {
    "timestamp": "ts",
    "operation": "op",
    "input_tokens": "in",
    "output_tokens": "out",
    "cache_creation_input_tokens": "cache_in",
    "cache_read_input_tokens": "cache_read",
    "cost_usd": "cost",
    "elapsed_s": "dur",
}


def _normalize_entry(entry: dict) -> dict:
    """Normalize a log entry from verbose keys to lean keys in-place.

    Args:
        entry: Raw parsed JSONL dict (may use old or new key names).

    Returns:
        The same dict, with verbose keys replaced by lean equivalents.
    """
    for old_key, new_key in _VERBOSE_TO_LEAN.items():
        if old_key in entry and new_key not in entry:
            entry[new_key] = entry.pop(old_key)
    entry.setdefault("model", "unknown")
    entry.setdefault("rid", "unknown")
    return entry


def load_usage_log(path: Path, since: datetime | None) -> list[dict]:
    """Read JSONL token usage log and optionally filter by timestamp.

    Args:
        path: Path to the JSONL log file.
        since: If provided, only return entries with timestamp >= this value.

    Returns:
        List of parsed log entry dicts, normalized to lean keys.
        Malformed lines are skipped.
    """
    if not path.exists():
        return []

    entries: list[dict] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            _normalize_entry(entry)

            if since is not None:
                ts_str = entry.get("ts")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str)
                except ValueError:
                    continue
                if ts < since:
                    continue

            entries.append(entry)

    return entries


def aggregate_by_operation(entries: list[dict]) -> list[OperationSummary]:
    """Group log entries by operation name and compute totals.

    Args:
        entries: List of parsed JSONL log entry dicts.

    Returns:
        List of OperationSummary, one per unique operation name.
    """
    if not entries:
        return []

    buckets: dict[str, dict] = {}
    for entry in entries:
        op = entry.get("op", "unknown")
        if op not in buckets:
            buckets[op] = {
                "call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cache_tokens": 0,
                "total_cost_usd": 0.0,
            }
        b = buckets[op]
        b["call_count"] += 1
        b["total_input_tokens"] += entry.get("in", 0)
        b["total_output_tokens"] += entry.get("out", 0)
        b["total_cache_tokens"] += (
            entry.get("cache_in", 0)
            + entry.get("cache_read", 0)
        )
        b["total_cost_usd"] += entry.get("cost", 0.0)

    summaries: list[OperationSummary] = []
    for op, b in buckets.items():
        summaries.append(OperationSummary(
            operation=op,
            call_count=b["call_count"],
            total_input_tokens=b["total_input_tokens"],
            total_output_tokens=b["total_output_tokens"],
            total_cache_tokens=b["total_cache_tokens"],
            total_cost_usd=b["total_cost_usd"],
            avg_cost_per_call=b["total_cost_usd"] / b["call_count"],
        ))

    return summaries


def aggregate_by_model(entries: list[dict]) -> list[OperationSummary]:
    """Group log entries by model name and compute totals.

    Args:
        entries: List of parsed JSONL log entry dicts (lean keys).

    Returns:
        List of OperationSummary, one per unique model. The model name
        is stored in the ``operation`` field.
    """
    if not entries:
        return []

    buckets: dict[str, dict] = {}
    for entry in entries:
        model = entry.get("model", "unknown")
        if model not in buckets:
            buckets[model] = {
                "call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cache_tokens": 0,
                "total_cost_usd": 0.0,
            }
        b = buckets[model]
        b["call_count"] += 1
        b["total_input_tokens"] += entry.get("in", 0)
        b["total_output_tokens"] += entry.get("out", 0)
        b["total_cache_tokens"] += (
            entry.get("cache_in", 0)
            + entry.get("cache_read", 0)
        )
        b["total_cost_usd"] += entry.get("cost", 0.0)

    summaries: list[OperationSummary] = []
    for model, b in buckets.items():
        summaries.append(OperationSummary(
            operation=model,
            call_count=b["call_count"],
            total_input_tokens=b["total_input_tokens"],
            total_output_tokens=b["total_output_tokens"],
            total_cache_tokens=b["total_cache_tokens"],
            total_cost_usd=b["total_cost_usd"],
            avg_cost_per_call=b["total_cost_usd"] / b["call_count"],
        ))

    return summaries


# ============================================================================
# MAIN ENTRYPOINT
# ============================================================================

def print_report(report: TokenReport) -> None:
    """Print a human-readable token usage report to stdout.

    Displays a table sorted by total cost descending, showing operation name,
    call count, total cost, average cost per call, total tokens, and percentage
    of total cost.

    Args:
        report: The TokenReport to display.
    """
    print(f"\nToken Usage Report -- {report.period}")
    print("=" * 100)

    if not report.operations:
        print("No data found for this period.")
        return

    sorted_ops = sorted(report.operations, key=lambda o: o.total_cost_usd, reverse=True)

    header = (
        f"{'Operation':<40} {'Calls':>6} {'Total Cost':>11} "
        f"{'Avg/Call':>10} {'Tokens':>12} {'% Cost':>7}"
    )
    print(header)
    print("-" * 100)

    for op in sorted_ops:
        total_tokens = op.total_input_tokens + op.total_output_tokens + op.total_cache_tokens
        pct = (op.total_cost_usd / report.grand_total_cost * 100) if report.grand_total_cost > 0 else 0.0
        print(
            f"{op.operation:<40} {op.call_count:>6} "
            f"${op.total_cost_usd:>10.4f} "
            f"${op.avg_cost_per_call:>9.4f} "
            f"{total_tokens:>12,} "
            f"{pct:>6.1f}%"
        )

    print("-" * 100)
    print(f"{'TOTAL':<40} {'':>6} ${report.grand_total_cost:>10.4f}")
    print()


def print_model_report(summaries: list[OperationSummary], grand_total: float, period: str) -> None:
    """Print a model breakdown table to stdout.

    Columns: Model, Calls, Total Cost, Avg/Call, % Cost.
    Sorted by total cost descending.

    Args:
        summaries: List of OperationSummary (model name in ``operation`` field).
        grand_total: Grand total cost in USD across all summaries.
        period: Human-readable period string for the header.
    """
    print(f"\nToken Usage by Model -- {period}")
    print("=" * 100)

    if not summaries:
        print("No data found for this period.")
        return

    sorted_summaries = sorted(summaries, key=lambda s: s.total_cost_usd, reverse=True)

    header = (
        f"{'Model':<20} {'Calls':>6}  {'Total Cost':>11}  "
        f"{'Avg/Call':>10}  {'% Cost':>7}"
    )
    print(header)
    print("-" * 100)

    for s in sorted_summaries:
        pct = (s.total_cost_usd / grand_total * 100) if grand_total > 0 else 0.0
        print(
            f"{s.operation[:20]:<20} {s.call_count:>6}  "
            f"${s.total_cost_usd:>10.4f}  "
            f"${s.avg_cost_per_call:>9.4f}  "
            f"{pct:>6.1f}%"
        )

    print("-" * 100)
    print(f"{'TOTAL':<20} {'':>6}  ${grand_total:>10.4f}")
    print()


def aggregate_by_timeline(entries: list[dict], bucket_size: str) -> list[TimelineBucket]:
    """Group log entries into chronological time buckets.

    Args:
        entries: List of parsed JSONL log entry dicts (lean keys).
        bucket_size: Either "hourly" or "daily".

    Returns:
        List of TimelineBucket sorted chronologically.

    Raises:
        ValueError: If bucket_size is not "hourly" or "daily".
    """
    if bucket_size not in ("hourly", "daily"):
        raise ValueError(f"Invalid bucket_size: '{bucket_size}'. Expected 'hourly' or 'daily'.")

    # bucket_key -> {cost_usd, call_count, op_costs: {op: cost}}
    buckets: dict[str, dict] = {}

    for entry in entries:
        ts_str = entry.get("ts", "")
        try:
            ts = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            continue

        if bucket_size == "hourly":
            label = f"{ts.hour:02d}:00-{ts.hour + 1:02d}:00"
            sort_key = f"{ts.strftime('%Y-%m-%d')}T{ts.hour:02d}"
        else:
            label = ts.strftime("%Y-%m-%d")
            sort_key = label

        if sort_key not in buckets:
            buckets[sort_key] = {
                "label": label,
                "cost": 0.0,
                "count": 0,
                "op_costs": {},
            }

        b = buckets[sort_key]
        cost = entry.get("cost", 0.0)
        b["cost"] += cost
        b["count"] += 1
        op = entry.get("op", "unknown")
        b["op_costs"][op] = b["op_costs"].get(op, 0.0) + cost

    result: list[TimelineBucket] = []
    for sort_key in sorted(buckets):
        b = buckets[sort_key]
        top_op = max(b["op_costs"], key=b["op_costs"].get)
        result.append(TimelineBucket(
            period_label=b["label"],
            total_cost_usd=b["cost"],
            call_count=b["count"],
            top_operation=top_op,
        ))

    return result


def print_timeline_report(
    buckets: list[TimelineBucket],
    grand_total: float,
    period: str,
    bucket_size: str,
) -> None:
    """Print a timeline report to stdout.

    Args:
        buckets: List of TimelineBucket sorted chronologically.
        grand_total: Grand total cost in USD across all buckets.
        period: Human-readable period string for the header.
        bucket_size: Either "hourly" or "daily" (for the header).
    """
    print(f"\nToken Usage Timeline ({bucket_size}) -- {period}")
    print("=" * 100)

    if not buckets:
        print("No data found for this period.")
        return

    header = f"{'Period':<17}{'Calls':>5}  {'Cost':>11}   {'Top Consumer'}"
    print(header)
    print("-" * 100)

    for b in buckets:
        print(
            f"{b.period_label:<17}{b.call_count:>5}  "
            f"${b.total_cost_usd:>10.4f}   "
            f"{b.top_operation}"
        )

    print("-" * 100)
    print(f"{'TOTAL':<17}{'':>5}  ${grand_total:>10.4f}")
    print()


def print_detail_report(entries: list[dict], grand_total: float, limit: int, period: str) -> None:
    """Print a per-invocation detail report to stdout.

    Shows every invocation as a row, most recent first, capped by limit.
    Columns: Timestamp, Operation, Model, Cost, Duration, Tokens.

    Args:
        entries: List of normalized log entry dicts (lean keys).
        grand_total: Grand total cost in USD across all entries.
        limit: Maximum number of rows to display.
        period: Human-readable period string for the header.
    """
    print(f"\nToken Usage Detail -- {period} (limit {limit})")
    print("=" * 100)

    if not entries:
        print("No data found for this period.")
        return

    # Sort by timestamp descending
    sorted_entries = sorted(entries, key=lambda e: e.get("ts", ""), reverse=True)
    display_entries = sorted_entries[:limit]

    header = (
        f"{'Timestamp':<21}{'Operation':<25}{'Model':<10}"
        f"{'Cost':>11}  {'Duration':>9}  {'Tokens':>10}"
    )
    print(header)
    print("-" * 100)

    for entry in display_entries:
        ts = entry.get("ts", "")[:19]
        op = entry.get("op", "unknown")[:24]
        model = entry.get("model", "unknown")[:20]
        cost = entry.get("cost", 0.0)
        dur = entry.get("dur", 0.0)
        tokens = (
            entry.get("in", 0)
            + entry.get("out", 0)
            + entry.get("cache_in", 0)
            + entry.get("cache_read", 0)
        )
        print(
            f"{ts:<21}{op:<25}{model:<10}"
            f"${cost:>10.4f}  {dur:>8.1f}s  {tokens:>10,}"
        )

    print("-" * 100)
    print(f"TOTAL ({len(entries)} invocations){'':>25}${grand_total:>10.4f}")
    print()


def main() -> int:
    """CLI entry point for the token usage report.

    Parses --since flag to filter by time window and report mode flags.
    Defaults to showing the operation-aggregated report if no mode flag
    is provided.

    Returns:
        0 on success, 1 on error.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Token usage report generator")
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Time window filter, e.g. '30m', '1h', '24h', '7d'",
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="Path to token_usage.jsonl (default: logs/token_usage.jsonl)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max rows for --detail mode (default: 50)",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--detail",
        action="store_true",
        help="Show every invocation as a row (most recent first)",
    )
    mode_group.add_argument(
        "--by-model",
        action="store_true",
        help="Show cost breakdown grouped by model",
    )
    mode_group.add_argument(
        "--timeline",
        type=str,
        choices=["hourly", "daily"],
        default=None,
        help="Show cost over time, bucketed hourly or daily",
    )

    args = parser.parse_args()

    log_path = Path(args.log) if args.log else DEFAULT_LOG_PATH

    since: datetime | None = None
    period = "all time"
    if args.since:
        try:
            since = parse_since(args.since)
            period = f"last {args.since}"
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    entries = load_usage_log(log_path, since)

    if args.timeline:
        buckets = aggregate_by_timeline(entries, args.timeline)
        grand_total = sum(b.total_cost_usd for b in buckets)
        print_timeline_report(buckets, grand_total, period, args.timeline)
    elif args.detail:
        grand_total = sum(e.get("cost", 0.0) for e in entries)
        print_detail_report(entries, grand_total, args.limit, period)
    elif args.by_model:
        summaries = aggregate_by_model(entries)
        grand_total = sum(s.total_cost_usd for s in summaries)
        print_model_report(summaries, grand_total, period)
    else:
        summaries = aggregate_by_operation(entries)
        grand_total = sum(s.total_cost_usd for s in summaries)
        report = TokenReport(
            period=period,
            operations=summaries,
            grand_total_cost=grand_total,
        )
        print_report(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
