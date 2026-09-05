"""Install the agent operating framework from this repo into ~/.claude.

Responsibilities:
- Symlink the framework's skills, agents, output styles, rules and hooks into ~/.claude
  so that one git pull updates every agent on the machine.
- Merge the framework's hook entries into ~/.claude/settings.json without touching
  anything else in that file.
- Report what it would do, and change nothing, unless --apply is passed.
- Undo everything it did, with --uninstall.

Symlinks rather than copies, so the installed framework and the repo cannot drift apart.
Claude Code supports symlinks in personal skill directories and in .claude/rules.

Nothing here writes to any other repository. Per-repo changes are listed by
--report-repos and have to be made deliberately.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ============================================================================
# CONSTANTS
# ============================================================================

# Install from a dedicated clone pinned to main, not from a Conductor primary checkout.
# That checkout follows whatever branch it happens to be on, which would tie global agent
# behaviour to an unrelated feature branch.
REPO_ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = REPO_ROOT / "framework"
CLAUDE_HOME = Path.home() / ".claude"
SETTINGS = CLAUDE_HOME / "settings.json"
BACKUP_SUFFIX = ".pre-framework"

# Every hook entry this framework adds, keyed by event. Written into settings.json under
# a marker so uninstall can find and remove exactly these and nothing else.
MARKER = "agent-operating-framework"

# The default set. These observe or re-anchor. None of them blocks a tool call.
HOOK_PLAN = {
    "InstructionsLoaded": [(None, "instructions_log.py")],
    "SessionStart": [("startup|resume|compact", "reanchor.py")],
    "SubagentStart": [(None, "reanchor.py")],
}

# Opt-in with --with-gate. The contract gate blocks writes, so it is off by default until
# it has been used on a real job. Bash is in both matchers because under bypass
# permissions most file access on this machine goes through Bash: measured 6,429 Bash
# calls against 1,640 Edit and Write across 52 recent large sessions.
GATE_PLAN = {
    "PreToolUse": [("Write|Edit|Bash", "contract_gate.py")],
    "PostToolUse": [("Read|Bash", "evidence_tracker.py")],
}


# ============================================================================
# DATA TRANSFER OBJECTS
# ============================================================================


@dataclass
class Link:
    """One symlink the installer manages."""

    source: Path
    target: Path

    @property
    def already_correct(self) -> bool:
        return self.target.is_symlink() and self.target.resolve() == self.source.resolve()

    @property
    def blocked_by(self) -> Optional[str]:
        """Return a description of what is in the way, or None when the path is free."""
        if not self.target.exists() and not self.target.is_symlink():
            return None
        if self.already_correct:
            return None
        if self.target.is_symlink():
            return f"symlink to {self.target.resolve()}"
        return "an existing file" if self.target.is_file() else "an existing directory"


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Actually make the changes.")
    parser.add_argument("--uninstall", action="store_true", help="Remove what this script installed.")
    parser.add_argument("--with-gate", action="store_true",
                        help="Also install the contract write-gate, which blocks tool calls.")
    parser.add_argument("--report-repos", action="store_true",
                        help="List repos on this machine that need a per-repo change, and stop.")
    args = parser.parse_args()

    if args.report_repos:
        report_repos()
        return

    links = planned_links()
    plan = dict(HOOK_PLAN)
    if args.with_gate:
        plan.update(GATE_PLAN)

    if args.uninstall:
        uninstall(links, apply=args.apply)
        return

    install(links, plan, apply=args.apply)


# ============================================================================
# INSTALL
# ============================================================================


def install(links: list[Link], plan: dict, apply: bool) -> None:
    """Create the symlinks and merge the hook entries into settings.json."""
    print(f"Framework source: {FRAMEWORK}")
    print(f"Install target:   {CLAUDE_HOME}")
    print(f"Mode:             {'APPLY' if apply else 'DRY RUN (pass --apply to make changes)'}\n")

    print("Symlinks")
    for link in links:
        blocker = link.blocked_by
        if link.already_correct:
            print(f"  ok       {link.target}")
            continue
        if blocker:
            print(f"  BLOCKED  {link.target}  <- {blocker}")
            continue
        print(f"  create   {link.target} -> {link.source}")
        if apply:
            link.target.parent.mkdir(parents=True, exist_ok=True)
            link.target.symlink_to(link.source)

    print("\nsettings.json hooks")
    settings = load_settings()
    updated, changes = merge_hooks(settings, plan)
    for change in changes:
        print(f"  {change}")
    if apply and changes:
        back_up_settings()
        SETTINGS.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
        print(f"  written, previous version at {SETTINGS.with_suffix('.json' + BACKUP_SUFFIX)}")

    if not apply:
        print("\nNothing was changed. Re-run with --apply.")


def planned_links() -> list[Link]:
    """Build the list of symlinks this installer manages."""
    links: list[Link] = []

    for kind in ("skills", "agents", "output-styles"):
        source_dir = FRAMEWORK / kind
        if not source_dir.is_dir():
            continue
        for entry in sorted(source_dir.iterdir()):
            if entry.name.startswith("."):
                continue
            links.append(Link(source=entry, target=CLAUDE_HOME / kind / entry.name))

    rules_dir = FRAMEWORK / "rules"
    if rules_dir.is_dir():
        for entry in sorted(rules_dir.glob("*.md")):
            links.append(Link(source=entry, target=CLAUDE_HOME / "rules" / entry.name))

    links.append(Link(source=FRAMEWORK / "hooks", target=CLAUDE_HOME / "framework-hooks"))
    links.append(Link(source=FRAMEWORK / "style", target=CLAUDE_HOME / "framework-style"))
    return links


def merge_hooks(settings: dict, plan: dict) -> tuple[dict, list[str]]:
    """Add this framework's hook entries to a settings dict, leaving the rest alone.

    Args:
        settings: The parsed contents of ~/.claude/settings.json.
        plan: Events mapped to (matcher, script) pairs to register.

    Returns:
        Tuple of (updated settings, list of human-readable change descriptions).
    """
    updated = json.loads(json.dumps(settings))
    hooks = updated.setdefault("hooks", {})
    changes: list[str] = []

    for event, entries in plan.items():
        bucket = hooks.setdefault(event, [])
        for matcher, script in entries:
            command = f"python3 {CLAUDE_HOME / 'framework-hooks' / script}"
            if any(has_command(group, command) for group in bucket):
                print(f"  ok       {event}: {script}")
                continue
            group: dict = {"hooks": [{"type": "command", "command": command, "_source": MARKER}]}
            if matcher:
                group["matcher"] = matcher
            bucket.append(group)
            changes.append(f"add      {event}: {script}"
                           + (f" (matcher {matcher})" if matcher else ""))

    return updated, changes


def has_command(group: dict, command: str) -> bool:
    """Return whether a settings hook group already runs a given command."""
    return any(h.get("command") == command for h in group.get("hooks", []))


# ============================================================================
# UNINSTALL
# ============================================================================


def uninstall(links: list[Link], apply: bool) -> None:
    """Remove the symlinks and hook entries this installer created."""
    print(f"Mode: {'APPLY' if apply else 'DRY RUN (pass --apply to make changes)'}\n")

    print("Symlinks")
    for link in links:
        if link.already_correct:
            print(f"  remove   {link.target}")
            if apply:
                link.target.unlink()
        else:
            print(f"  skip     {link.target} (not ours)")

    print("\nsettings.json hooks")
    settings = load_settings()
    hooks = settings.get("hooks", {})
    removed = 0
    for event in list(hooks):
        kept = []
        for group in hooks[event]:
            inner = [h for h in group.get("hooks", []) if h.get("_source") != MARKER]
            if len(inner) != len(group.get("hooks", [])):
                removed += len(group.get("hooks", [])) - len(inner)
            if inner:
                group["hooks"] = inner
                kept.append(group)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    print(f"  {removed} hook entries removed")
    if apply and removed:
        back_up_settings()
        SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    if not apply:
        print("\nNothing was changed. Re-run with --apply.")


# ============================================================================
# PER-REPO REPORT
# ============================================================================


def report_repos() -> None:
    """List repos that have an AGENTS.md Claude Code will never load.

    Claude Code loads CLAUDE.md and CLAUDE.local.md only. A repo with an AGENTS.md and no
    CLAUDE.md has instructions that are never read at session start. The fix is a
    one-line CLAUDE.md containing `@AGENTS.md`, committed to the repo's main branch.
    """
    workspaces = Path.home() / "conductor" / "workspaces"
    if not workspaces.is_dir():
        print("No Conductor workspaces directory found.")
        return

    print("Repos whose AGENTS.md is not being loaded\n")
    seen: set[str] = set()
    for repo_dir in sorted(workspaces.iterdir()):
        if not repo_dir.is_dir():
            continue
        for workspace in sorted(repo_dir.iterdir()):
            if not workspace.is_dir():
                continue
            has_agents = (workspace / "AGENTS.md").is_file()
            has_claude = (workspace / "CLAUDE.md").is_file()
            if has_agents and not has_claude and repo_dir.name not in seen:
                seen.add(repo_dir.name)
                print(f"  {repo_dir.name}")
                print(f"    example workspace: {workspace}")
                print(f"    fix: echo '@AGENTS.md' > CLAUDE.md, commit to main\n")

    if not seen:
        print("  none")


# ============================================================================
# SETTINGS HELPERS
# ============================================================================


def load_settings() -> dict:
    """Read ~/.claude/settings.json, returning an empty dict when it does not exist."""
    if not SETTINGS.is_file():
        return {}
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def back_up_settings() -> None:
    """Copy settings.json aside before the first write of a run."""
    backup = SETTINGS.with_suffix(".json" + BACKUP_SUFFIX)
    if SETTINGS.is_file() and not backup.exists():
        shutil.copy2(SETTINGS, backup)


if __name__ == "__main__":
    main()
