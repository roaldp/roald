#!/usr/bin/env python3
"""Check that a PLAN.md carries a real measurable outcome, not a described activity.

Responsibilities:
- Verify the Success criteria section names a metric with a unit, a baseline, a threshold
  and a read date.
- Verify the MVP scope section names what is out, what the deliverable is, a kill
  condition and a budget.
- Fail on placeholder text left in from the template.

This is the mechanical half of the screen described in
framework/skills/scope-brief/SKILL.md. It is a lint and not a judgement: it can tell you a
threshold is missing, it cannot tell you the threshold is the right one, and it cannot tell
you the work should have been declined.

Exit code 0 when the plan passes, 1 when it does not, so it can gate a step.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

# ============================================================================
# CONSTANTS
# ============================================================================

# Labelled fields the plan must carry, keyed by the section they belong to. The labels are
# fixed so parsing is unambiguous. The template writes them.
REQUIRED_FIELDS = {
    "Success criteria": [
        ("Metric", "the thing being measured, with a unit"),
        ("Baseline", "what that number is today, or NOT MEASURED"),
        ("Threshold", "the value that makes the work worth having done"),
        ("Read date", "when the number gets read"),
    ],
    "MVP scope": [
        ("Out", "what is deliberately not being done"),
        ("What the deliverable looks like", "a file at a path, a message of a given shape"),
        ("Kill condition", "what makes the work stop rather than get extended"),
        ("Budget", "how much agent work and how much of Roald's review time"),
    ],
}

# A metric without one of these is an activity description rather than a measurement.
UNIT_HINTS = re.compile(
    r"\b(per cent|percent|%|minutes?|hours?|days?|weeks?|seconds?|ms|"
    r"eur|usd|chf|€|\$|count|per (?:day|week|month)|kb|mb|gb|tokens?|lines?|"
    r"requests?|users?|calls?|messages?|files?|steps?)\b",
    re.IGNORECASE,
)

# Text the template ships with. Left in place, it means the section was never filled. A
# real value never opens with an angle bracket, and template guidance often runs over
# several lines, so the opening bracket alone is the reliable signal.
PLACEHOLDER = re.compile(r"^<|TBD|TODO|\bxxx\b", re.IGNORECASE)

DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b",
                  re.IGNORECASE)

NOT_MEASURED = "not measured"


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="Path to PLAN.md")
    args = parser.parse_args()

    if not args.plan.is_file():
        print(f"No such plan: {args.plan}")
        raise SystemExit(1)

    text = args.plan.read_text(encoding="utf-8")
    problems = check_plan(text)

    if not problems:
        print(f"{args.plan}: metrics complete.")
        return

    print(f"{args.plan}: {len(problems)} problems\n")
    for problem in problems:
        print(f"  {problem}")
    print("\nThe screen: framework/skills/scope-brief/SKILL.md section 1.")
    raise SystemExit(1)


# ============================================================================
# CHECKS
# ============================================================================


def check_plan(text: str) -> list:
    """Return every problem found in a plan's measurable-outcome sections.

    Args:
        text: The full contents of PLAN.md.

    Returns:
        Human-readable problem descriptions, empty when the plan passes.
    """
    problems: list = []

    for heading, fields in REQUIRED_FIELDS.items():
        section = extract_section(text, heading)
        if section is None:
            problems.append(f"No '{heading}' section.")
            continue
        for label, meaning in fields:
            problems.extend(check_field(section, heading, label, meaning))

    problems.extend(check_metric_quality(text))
    return problems


def check_field(section: str, heading: str, label: str, meaning: str) -> list:
    """Check one labelled field inside a section."""
    value = read_field(section, label)
    if value is None:
        return [f"{heading}: no '{label}' line. That is {meaning}."]
    if not value:
        return [f"{heading}: '{label}' is empty. That is {meaning}."]
    if PLACEHOLDER.search(value):
        return [f"{heading}: '{label}' still holds template text: {value[:60]}"]
    return []


def check_metric_quality(text: str) -> list:
    """Check the metric, baseline and read date say something checkable."""
    problems: list = []
    section = extract_section(text, "Success criteria")
    if section is None:
        return problems

    metric = read_field(section, "Metric")
    if metric and not PLACEHOLDER.search(metric) and not UNIT_HINTS.search(metric):
        problems.append(
            f"Success criteria: 'Metric' names no unit: {metric[:60]}. "
            "Without a unit this is an activity, not an outcome."
        )

    baseline = read_field(section, "Baseline")
    if baseline and not PLACEHOLDER.search(baseline) and NOT_MEASURED in baseline.lower():
        problems.append(
            "Success criteria: baseline is NOT MEASURED. That is allowed, and it means "
            "measuring it is the first step of the job and probably the whole MVP. Say so "
            "in the plan."
        )

    read_date = read_field(section, "Read date")
    if read_date and not PLACEHOLDER.search(read_date) and not DATE.search(read_date):
        problems.append(
            f"Success criteria: 'Read date' carries no date: {read_date[:60]}. "
            "A metric with no read date is never read."
        )

    return problems


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def extract_section(text: str, heading: str) -> Optional[str]:
    """Return the body of a markdown section, or None when the heading is absent."""
    start = re.search(rf"^#+\s+{re.escape(heading)}\s*$", text, re.MULTILINE | re.IGNORECASE)
    if start is None:
        return None
    following = re.search(r"^#+\s+", text[start.end():], re.MULTILINE)
    return text[start.end():start.end() + following.start()] if following else text[start.end():]


def read_field(section: str, label: str) -> Optional[str]:
    """Return the value of a `**Label:** value` line, or None when the label is absent."""
    match = re.search(rf"\*\*{re.escape(label)}:?\*\*:?\s*(.*)", section, re.IGNORECASE)
    return match.group(1).strip() if match else None


if __name__ == "__main__":
    main()
