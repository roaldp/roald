"""Inventory every Claude Code agent surface on this machine.

Responsibilities:
- Find every directory Claude Code has been run in, ranked by recent activity.
- Group those directories into roots (a git repo, a Conductor repo, or a plain folder).
- Report which instruction surfaces each root already has: CLAUDE.md, AGENTS.md,
  .claude/agents, .claude/skills, .claude/commands, .claude/settings.json.
- Report the user-global surfaces under ~/.claude.

Used to plan and verify rollout of the agent operating framework. Read-only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================

CLAUDE_HOME = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_HOME / "projects"
CONDUCTOR_WORKSPACES = Path.home() / "conductor" / "workspaces"
CONDUCTOR_REPOS = Path.home() / "conductor" / "repos"

INSTRUCTION_FILES = ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"]
CLAUDE_SUBDIRS = ["agents", "skills", "commands", "hooks"]

# ============================================================================
# DATA TRANSFER OBJECTS
# ============================================================================


@dataclass
class SessionDir:
    """One directory Claude Code has been run in, as recorded under ~/.claude/projects."""

    path: Path
    session_count: int
    total_bytes: int
    last_active: float


@dataclass
class Root:
    """A repo or folder that owns instruction files, aggregating its session dirs."""

    path: Path
    kind: str
    sessions: list[SessionDir] = field(default_factory=list)

    @property
    def last_active(self) -> float:
        return max((s.last_active for s in self.sessions), default=0.0)

    @property
    def session_count(self) -> int:
        return sum(s.session_count for s in self.sessions)

    @property
    def total_bytes(self) -> int:
        return sum(s.total_bytes for s in self.sessions)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--limit", type=int, default=40, help="Rows to print in table mode.")
    args = parser.parse_args()

    sessions = collect_session_dirs()
    roots = group_into_roots(sessions)
    globals_ = describe_global_surfaces()

    if args.json:
        print(json.dumps({"globals": globals_, "roots": [serialise_root(r) for r in roots]}, indent=2, default=str))
        return

    print_report(roots, globals_, args.limit)


# ============================================================================
# COLLECTION
# ============================================================================


def collect_session_dirs() -> list[SessionDir]:
    """Read ~/.claude/projects and recover the working directory each entry refers to.

    Returns:
        Session directories that still exist on disk, newest first.
    """
    found: list[SessionDir] = []
    if not PROJECTS_DIR.is_dir():
        return found

    for entry in PROJECTS_DIR.iterdir():
        if not entry.is_dir():
            continue
        transcripts = list(entry.glob("*.jsonl"))
        if not transcripts:
            continue
        cwd = resolve_project_cwd(entry, transcripts)
        if cwd is None or not cwd.is_dir():
            continue
        found.append(
            SessionDir(
                path=cwd,
                session_count=len(transcripts),
                total_bytes=sum(t.stat().st_size for t in transcripts),
                last_active=max(t.stat().st_mtime for t in transcripts),
            )
        )

    found.sort(key=lambda s: s.last_active, reverse=True)
    return found


def resolve_project_cwd(entry: Path, transcripts: list[Path]) -> Path | None:
    """Recover the real working directory for a ~/.claude/projects entry.

    The directory name is the path with separators replaced by dashes, which is
    ambiguous when a path segment itself contains a dash. The transcript records the
    true cwd, so read that first and only fall back to decoding the name.

    Args:
        entry: The ~/.claude/projects/<encoded-path> directory.
        transcripts: Its .jsonl transcript files.

    Returns:
        The working directory, or None when it cannot be determined.
    """
    for transcript in transcripts:
        with transcript.open("r", encoding="utf-8", errors="replace") as handle:
            for _ in range(50):
                line = handle.readline()
                if not line:
                    break
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = record.get("cwd")
                if cwd:
                    return Path(cwd)

    decoded = Path("/" + entry.name.lstrip("-").replace("-", "/"))
    return decoded if decoded.is_dir() else None


def group_into_roots(sessions: list[SessionDir]) -> list[Root]:
    """Attribute each session directory to the root that owns its instruction files."""
    roots: dict[Path, Root] = {}
    for session in sessions:
        root_path, kind = find_root(session.path)
        root = roots.get(root_path)
        if root is None:
            root = Root(path=root_path, kind=kind)
            roots[root_path] = root
        root.sessions.append(session)

    ordered = sorted(roots.values(), key=lambda r: r.last_active, reverse=True)
    return ordered


def find_root(path: Path) -> tuple[Path, str]:
    """Find the instruction-owning root for a working directory.

    A Conductor workspace is a checkout of a repo, so its root is itself: instruction
    files live in the workspace and are committed back to the repo. Otherwise the
    root is the enclosing git repository, and failing that the directory itself.

    Args:
        path: A directory Claude Code was run in.

    Returns:
        Tuple of (root path, kind) where kind is conductor-workspace, git-repo or folder.
    """
    if CONDUCTOR_WORKSPACES in path.parents:
        relative = path.relative_to(CONDUCTOR_WORKSPACES)
        if len(relative.parts) >= 2:
            return CONDUCTOR_WORKSPACES / relative.parts[0] / relative.parts[1], "conductor-workspace"

    toplevel = git_toplevel(path)
    if toplevel is not None:
        return toplevel, "git-repo"
    return path, "folder"


def git_toplevel(path: Path) -> Path | None:
    """Return the git repository root for a path, or None when it is not a repo."""
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


# ============================================================================
# SURFACE DESCRIPTION
# ============================================================================


def describe_surfaces(root: Path) -> dict[str, object]:
    """List which agent instruction surfaces exist inside a root."""
    surfaces: dict[str, object] = {}
    for name in INSTRUCTION_FILES:
        candidate = root / name
        surfaces[name] = candidate.stat().st_size if candidate.is_file() else None

    for name in CLAUDE_SUBDIRS:
        directory = root / ".claude" / name
        surfaces[f".claude/{name}"] = (
            sorted(p.name for p in directory.iterdir()) if directory.is_dir() else None
        )

    settings = root / ".claude" / "settings.json"
    surfaces[".claude/settings.json"] = settings.is_file()
    return surfaces


def describe_global_surfaces() -> dict[str, object]:
    """Describe the user-global surfaces under ~/.claude."""
    return describe_surfaces(Path.home()) | describe_surfaces(CLAUDE_HOME.parent) | {
        "~/.claude/CLAUDE.md": (CLAUDE_HOME / "CLAUDE.md").stat().st_size
        if (CLAUDE_HOME / "CLAUDE.md").is_file()
        else None,
        "~/.claude/agents": sorted(p.name for p in (CLAUDE_HOME / "agents").iterdir())
        if (CLAUDE_HOME / "agents").is_dir()
        else None,
        "~/.claude/skills": sorted(p.name for p in (CLAUDE_HOME / "skills").iterdir())
        if (CLAUDE_HOME / "skills").is_dir()
        else None,
        "~/.claude/commands": sorted(p.name for p in (CLAUDE_HOME / "commands").iterdir())
        if (CLAUDE_HOME / "commands").is_dir()
        else None,
    }


def serialise_root(root: Root) -> dict[str, object]:
    """Convert a Root into a JSON-friendly dictionary."""
    return {
        "path": str(root.path),
        "kind": root.kind,
        "last_active": time.strftime("%Y-%m-%d", time.localtime(root.last_active)),
        "session_count": root.session_count,
        "total_mb": round(root.total_bytes / 1e6, 1),
        "working_dirs": len(root.sessions),
        "surfaces": describe_surfaces(root.path),
    }


# ============================================================================
# REPORTING
# ============================================================================


def print_report(roots: list[Root], globals_: dict[str, object], limit: int) -> None:
    """Print a human-readable inventory table."""
    print("USER-GLOBAL SURFACES (~/.claude)")
    for key in ("~/.claude/CLAUDE.md", "~/.claude/agents", "~/.claude/skills", "~/.claude/commands"):
        print(f"  {key:<24} {globals_.get(key)}")

    print(f"\nROOTS WITH CLAUDE CODE ACTIVITY ({len(roots)} total, showing {min(limit, len(roots))})\n")
    header = f"{'last active':<12} {'MB':>7} {'sess':>5} {'dirs':>5}  {'CLAUDE.md':>9} {'AGENTS.md':>9}  path"
    print(header)
    print("-" * len(header))
    for root in roots[:limit]:
        surfaces = describe_surfaces(root.path)
        claude_md = "yes" if surfaces["CLAUDE.md"] else "-"
        agents_md = "yes" if surfaces["AGENTS.md"] else "-"
        print(
            f"{time.strftime('%Y-%m-%d', time.localtime(root.last_active)):<12} "
            f"{root.total_bytes / 1e6:>7.1f} {root.session_count:>5} {len(root.sessions):>5}  "
            f"{claude_md:>9} {agents_md:>9}  {root.path}"
        )


if __name__ == "__main__":
    main()
