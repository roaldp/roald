#!/usr/bin/env python3
"""Audit the Claude agent system on this machine and report what changed.

Responsibilities:
- Find instruction files that will never be loaded.
- Find references to subagents, skills and commands that do not exist.
- Measure how agents actually behave here: which tools they use, whether sessions compact,
  which commands and skills are ever invoked.
- Measure the writing markers Roald asked to be held to, in his own text and in the
  agents' output.
- Summarise the InstructionsLoaded log, when the logging hook is installed.

Read-only. It changes nothing and installs nothing.

Every check exists because it caught something real on 2026-09-06. The findings are in
.docs/plans/2026.09.06-agent-operating-framework/. Run this periodically: the point is the
trend, not the snapshot.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ============================================================================
# CONSTANTS
# ============================================================================

CLAUDE_HOME = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_HOME / "projects"
CONDUCTOR_WORKSPACES = Path.home() / "conductor" / "workspaces"
INSTRUCTIONS_LOG = CLAUDE_HOME / "framework-logs" / "instructions-loaded.jsonl"

# Claude Code loads these and nothing else. Verified three ways on 2026-09-06: the docs,
# the discovery array in the binary, and a live probe answering LOADED=no in a workspace
# whose only instruction file was AGENTS.md.
LOADED_FILENAMES = ("CLAUDE.md", "CLAUDE.local.md")

RECENT_DAYS = 14
LARGE_TRANSCRIPT_BYTES = 2_000_000

# A named subagent in an instruction file. `~/.claude/commands/create_plan.md` referenced
# a `plan-reviewer` that did not exist, so the review loop silently never ran.
SUBAGENT_REFERENCE = re.compile(
    r"(?:subagent|sub-agent|agent)\s+`?([a-z][a-z0-9-]{2,40})`?", re.IGNORECASE
)
COMMAND_INVOCATION = re.compile(r"<command-name>/?([a-zA-Z0-9_:-]+)")

# The two characters Roald asked never to appear in anything an agent writes.
EM_DASH = "—"
SEMICOLON = ";"


# ============================================================================
# DATA TRANSFER OBJECTS
# ============================================================================


@dataclass
class Finding:
    """One thing the audit noticed, and what to do about it."""

    check: str
    severity: str
    detail: str
    action: str


@dataclass
class Report:
    """Everything one audit run produced."""

    findings: list = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, check: str, severity: str, detail: str, action: str) -> None:
        self.findings.append(Finding(check, severity, detail, action))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a report.")
    parser.add_argument("--days", type=int, default=RECENT_DAYS,
                        help="Window for the behaviour measurements.")
    args = parser.parse_args()

    report = Report()
    check_instruction_loading(report)
    check_dangling_references(report)
    transcripts = collect_transcripts(args.days)
    check_tool_use(report, transcripts)
    check_compaction(report)
    check_command_usage(report)
    check_writing_markers(report, args.days)
    check_instructions_log(report)

    if args.json:
        print(json.dumps({
            "generated": time.strftime("%Y-%m-%d %H:%M"),
            "facts": report.facts,
            "findings": [f.__dict__ for f in report.findings],
        }, indent=2))
        return

    print_report(report)


# ============================================================================
# CHECKS
# ============================================================================


def check_instruction_loading(report: Report) -> None:
    """Find repos whose instruction file Claude Code will never load."""
    unloaded = []
    if CONDUCTOR_WORKSPACES.is_dir():
        for repo_dir in sorted(CONDUCTOR_WORKSPACES.iterdir()):
            if not repo_dir.is_dir():
                continue
            for workspace in sorted(repo_dir.iterdir()):
                if not workspace.is_dir():
                    continue
                if (workspace / "AGENTS.md").is_file() and not loads_instructions(workspace):
                    unloaded.append(repo_dir.name)
                    break

    report.facts["repos_with_unloaded_agents_md"] = unloaded
    if unloaded:
        report.add(
            "instruction loading",
            "HIGH",
            f"{len(unloaded)} repos have an AGENTS.md that is never loaded: "
            + ", ".join(unloaded),
            "Commit a one-line CLAUDE.md containing @AGENTS.md at each repo root.",
        )


def loads_instructions(directory: Path) -> bool:
    """Return whether a directory has a file Claude Code loads at session start."""
    return any((directory / name).is_file() for name in LOADED_FILENAMES)


def check_dangling_references(report: Report) -> None:
    """Find subagents named in user-level instruction files that do not exist."""
    available = set()
    for kind in ("agents", "skills"):
        directory = CLAUDE_HOME / kind
        if directory.is_dir():
            available |= {entry.stem for entry in directory.iterdir()}

    dangling = []
    for source_dir in (CLAUDE_HOME / "commands", CLAUDE_HOME / "skills"):
        if not source_dir.is_dir():
            continue
        for path in source_dir.rglob("*.md"):
            for name in set(SUBAGENT_REFERENCE.findall(path.read_text(errors="replace"))):
                lowered = name.lower()
                if "-" not in lowered or lowered in available:
                    continue
                dangling.append((path.name, lowered))

    report.facts["dangling_agent_references"] = dangling
    if dangling:
        listed = ", ".join(f"{name} in {where}" for where, name in dangling)
        report.add(
            "dangling references",
            "HIGH",
            f"Instruction files name {len(dangling)} agents that do not exist: {listed}",
            "Create the agent, or delete the reference. A named agent that is missing means "
            "that step silently never runs.",
        )


def check_tool_use(report: Report, transcripts: list) -> None:
    """Measure which tools agents actually use, since hook matchers depend on it."""
    counts: collections.Counter = collections.Counter()
    for path in transcripts:
        with path.open(errors="replace") as handle:
            for line in handle:
                if '"tool_use"' not in line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = (record.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "tool_use":
                        counts[part.get("name")] += 1

    bash = counts.get("Bash", 0)
    file_tools = counts.get("Edit", 0) + counts.get("Write", 0)
    report.facts["tool_counts"] = dict(counts.most_common(10))
    report.facts["bash_vs_file_tools"] = [bash, file_tools]

    if file_tools and bash / file_tools > 2:
        report.add(
            "tool use",
            "INFO",
            f"Bash {bash} against Edit plus Write {file_tools}, a ratio of "
            f"{bash / file_tools:.1f}. Under bypass permissions the harness tells agents to "
            "prefer heredocs and sed.",
            "Any hook matching only Edit|Write is decorative here. Include Bash in the "
            "matcher, or use permissions.deny, which is tool-agnostic.",
        )


def check_compaction(report: Report) -> None:
    """Measure how often sessions actually compact, since anti-drift advice assumes it."""
    total = hits = large = large_hits = 0
    for path in PROJECTS_DIR.rglob("*.jsonl"):
        total += 1
        is_large = path.stat().st_size > LARGE_TRANSCRIPT_BYTES
        large += is_large
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        if "isCompactSummary" in text or '"compact"' in text:
            hits += 1
            large_hits += is_large

    report.facts["compaction"] = {"transcripts": total, "with_marker": hits,
                                  "large": large, "large_with_marker": large_hits}
    if total and hits / total < 0.05:
        report.add(
            "compaction",
            "INFO",
            f"{hits} of {total} transcripts carry a compaction marker, and "
            f"{large_hits} of {large} large ones.",
            "Compaction is not the durability axis on this machine. Do not build "
            "anti-drift mechanisms around surviving it.",
        )


def check_command_usage(report: Report) -> None:
    """Find custom commands and skills that are never actually invoked."""
    invoked: collections.Counter = collections.Counter()
    for path in PROJECTS_DIR.rglob("*.jsonl"):
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for name in set(COMMAND_INVOCATION.findall(text)):
            invoked[name] += 1

    installed = set()
    for source_dir in (CLAUDE_HOME / "commands", CLAUDE_HOME / "skills"):
        if source_dir.is_dir():
            installed |= {entry.stem for entry in source_dir.iterdir()
                          if not entry.name.startswith(".")}

    never = sorted(name for name in installed if invoked.get(name, 0) == 0)
    # A skill invoked by the model leaves no <command-name> marker, so this check only sees
    # what the user typed. Read it as "never typed", and use the framework-logs and the
    # transcripts to find model invocations.
    report.facts["commands_invoked"] = dict(invoked.most_common(15))
    report.facts["never_invoked"] = never

    if never:
        report.add(
            "command usage",
            "MEDIUM",
            f"{len(never)} installed commands or skills have never been typed by the user: "
            + ", ".join(never),
            "This counts typed invocations only, so a skill the model invokes itself will "
            "still appear here. What matters is whether each one has a description written "
            "for the task and a when_to_use written for the trigger. Without those, the "
            "model cannot route to it and it will never fire either way.",
        )


def check_writing_markers(report: Report, days: int) -> None:
    """Measure em dashes and semicolons in Roald's own typing and in agent output."""
    cutoff = time.time() - days * 86400
    human = {"words": 0, "em": 0, "semi": 0}
    agent = {"words": 0, "em": 0, "semi": 0}

    for path in PROJECTS_DIR.rglob("*.jsonl"):
        if path.stat().st_mtime < cutoff:
            continue
        with path.open(errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                bucket = pick_bucket(record, human, agent)
                if bucket is None:
                    continue
                text = extract_text(record, bucket is human)
                if text is None:
                    continue
                bucket["words"] += len(re.findall(r"[A-Za-z']+", text))
                bucket["em"] += text.count(EM_DASH)
                bucket["semi"] += text.count(SEMICOLON)

    for label, bucket in (("roald", human), ("agents", agent)):
        if not bucket["words"]:
            continue
        report.facts[f"{label}_per_1k"] = {
            "words": bucket["words"],
            "em_dash": round(bucket["em"] / bucket["words"] * 1000, 2),
            "semicolon": round(bucket["semi"] / bucket["words"] * 1000, 2),
        }

    if agent["words"] and agent["em"] / agent["words"] * 1000 > 1.0:
        report.add(
            "writing markers",
            "MEDIUM",
            f"Agent output runs {agent['em'] / agent['words'] * 1000:.1f} em dashes per "
            f"thousand words over the last {days} days. Roald asked for zero.",
            "The style rules are not reaching the surface that produces this. Check whether "
            "the write-external skill and the steering output style are installed and firing.",
        )


def pick_bucket(record: dict, human: dict, agent: dict) -> Optional[dict]:
    """Route a transcript record to the human or agent bucket, or skip it."""
    if record.get("isMeta"):
        return None
    kind = record.get("type")
    if kind == "user":
        return human
    if kind == "assistant":
        return agent
    return None


def extract_text(record: dict, human: bool) -> Optional[str]:
    """Pull plain text out of a transcript record, skipping tool traffic and pastes.

    Args:
        record: One transcript line.
        human: True when this is a user turn, which needs the stricter filter.

    Returns:
        The text, or None when the record is not usable prose.
    """
    content = (record.get("message") or {}).get("content")
    if isinstance(content, list):
        content = " ".join(part.get("text", "") for part in content
                           if isinstance(part, dict) and part.get("type") == "text")
    if not isinstance(content, str):
        return None

    content = content.strip()
    if not content or content.startswith("<") or "system-reminder" in content:
        return None
    if len(content) < 40 or len(content) > 4000:
        return None
    if human and looks_pasted(content):
        return None
    return content


def looks_pasted(text: str) -> bool:
    """Return whether a user turn is pasted material rather than something Roald typed.

    Without this the human em-dash rate is inflated by roughly a factor of seven, because
    agent output pasted back into the conversation is recorded as a user turn.
    """
    if len(text) > 600 or "```" in text:
        return True
    if re.search(r"^\s*[-*]\s", text, re.M) or re.search(r"^#{1,6}\s", text, re.M):
        return True
    if re.search(r"^\s*\|", text, re.M) or "**" in text:
        return True
    return text.count("\n") > 6


def check_instructions_log(report: Report) -> None:
    """Summarise which instruction files are actually loading, when the log exists."""
    if not INSTRUCTIONS_LOG.is_file():
        report.add(
            "instructions log",
            "MEDIUM",
            "No InstructionsLoaded log. Nothing here can tell an ignored instruction from "
            "one that was never loaded.",
            "Install the logging hook: python3 scripts/install_framework.py --apply",
        )
        return

    files: collections.Counter = collections.Counter()
    with INSTRUCTIONS_LOG.open(errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("file_path"):
                files[record["file_path"]] += 1

    report.facts["instructions_loaded"] = dict(files.most_common(15))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def collect_transcripts(days: int) -> list:
    """Return large transcripts modified inside the window."""
    cutoff = time.time() - days * 86400
    return [path for path in PROJECTS_DIR.rglob("*.jsonl")
            if path.stat().st_size > LARGE_TRANSCRIPT_BYTES and path.stat().st_mtime > cutoff]


# ============================================================================
# REPORTING
# ============================================================================


def print_report(report: Report) -> None:
    """Print the audit as a readable report."""
    print(f"Agent system audit, {time.strftime('%Y-%m-%d %H:%M')}\n")

    if not report.findings:
        print("No findings.\n")
    for finding in sorted(report.findings, key=lambda f: ("HIGH", "MEDIUM", "INFO").index(f.severity)):
        print(f"[{finding.severity}] {finding.check}")
        print(f"  {finding.detail}")
        print(f"  Action: {finding.action}\n")

    print("Measurements")
    for key, value in report.facts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
