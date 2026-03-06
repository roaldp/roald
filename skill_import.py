#!/usr/bin/env python3
"""skill_import.py — CLI for importing, listing, and removing OpenClaw skills."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
COMMUNITY_DIR = BASE_DIR / "skills" / "community"


def cmd_install(source: str) -> None:
    """Install a skill from a local path or ClawHub GitHub repo."""
    source_path = Path(source)
    if source_path.is_dir():
        # Local install
        skill_md = source_path / "SKILL.md"
        if not skill_md.exists():
            print(f"ERROR: No SKILL.md found in {source_path}", file=sys.stderr)
            sys.exit(1)
        name = source_path.name
        dest = COMMUNITY_DIR / name
        if dest.exists():
            print(f"Skill '{name}' already installed. Remove it first to reinstall.")
            sys.exit(1)
        shutil.copytree(source_path, dest)
        print(f"Installed '{name}' from local path.")
    else:
        # Treat as a ClawHub skill name — fetch from GitHub
        name = source
        dest = COMMUNITY_DIR / name
        if dest.exists():
            print(f"Skill '{name}' already installed. Remove it first to reinstall.")
            sys.exit(1)
        repo_url = f"https://github.com/openclaw/clawhub.git"
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(
                    ["git", "clone", "--depth=1", "--filter=blob:none", "--sparse", repo_url, tmpdir],
                    check=True, capture_output=True, text=True,
                )
                subprocess.run(
                    ["git", "-C", tmpdir, "sparse-checkout", "set", f"skills/{name}"],
                    check=True, capture_output=True, text=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to fetch skill '{name}' from ClawHub: {e.stderr}", file=sys.stderr)
                sys.exit(1)
            fetched = Path(tmpdir) / "skills" / name
            if not (fetched / "SKILL.md").exists():
                print(f"ERROR: Skill '{name}' not found on ClawHub.", file=sys.stderr)
                sys.exit(1)
            shutil.copytree(fetched, dest)
        print(f"Installed '{name}' from ClawHub.")

    _rebuild_index()


def cmd_list() -> None:
    """List all installed skills."""
    # Import here to avoid circular dependency at module level
    from skills import discover_skills
    skills = discover_skills()
    if not skills:
        print("No skills installed.")
        return
    print(f"{'Name':<25} {'Source':<12} Description")
    print("-" * 70)
    for name, meta in sorted(skills.items()):
        path = Path(meta["path"])
        if "bundled" in path.parts:
            source = "bundled"
        elif "community" in path.parts:
            source = "community"
        else:
            source = "local"
        print(f"{name:<25} {source:<12} {meta['description']}")


def cmd_remove(name: str) -> None:
    """Remove a community skill."""
    dest = COMMUNITY_DIR / name
    if not dest.exists():
        print(f"Skill '{name}' not found in community skills.", file=sys.stderr)
        sys.exit(1)
    shutil.rmtree(dest)
    print(f"Removed '{name}'.")
    _rebuild_index()


def _rebuild_index() -> None:
    from skills import build_index
    build_index()
    print("Skill index rebuilt.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Roald skills (OpenClaw-compatible)")
    sub = parser.add_subparsers(dest="command")

    install_p = sub.add_parser("install", help="Install a skill from ClawHub or local path")
    install_p.add_argument("source", help="Skill name (ClawHub) or local path")

    sub.add_parser("list", help="List installed skills")

    remove_p = sub.add_parser("remove", help="Remove a community skill")
    remove_p.add_argument("name", help="Skill name to remove")

    args = parser.parse_args()
    if args.command == "install":
        cmd_install(args.source)
    elif args.command == "list":
        cmd_list()
    elif args.command == "remove":
        cmd_remove(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
