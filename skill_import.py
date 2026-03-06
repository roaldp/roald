#!/usr/bin/env python3
"""skill_import.py — CLI tool for importing and managing OpenClaw skills."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import skills as skills_module

BASE_DIR = Path(__file__).parent
COMMUNITY_DIR = BASE_DIR / "skills" / "community"
LOCAL_DIR = BASE_DIR / "skills" / "local"


def cmd_install(args: argparse.Namespace) -> None:
    """Install a skill from a local path or ClawHub."""
    source = args.source

    source_path = Path(source)
    if source_path.exists():
        # Local install
        skill_md = source_path / "SKILL.md" if source_path.is_dir() else source_path
        if not skill_md.exists():
            print(f"Error: no SKILL.md found at {source_path}", file=sys.stderr)
            sys.exit(1)

        parsed = skills_module.parse_skill_md(skill_md)
        if parsed is None:
            print(f"Error: invalid SKILL.md at {skill_md}", file=sys.stderr)
            sys.exit(1)

        dest = COMMUNITY_DIR / parsed["name"]
        dest.mkdir(parents=True, exist_ok=True)

        if source_path.is_dir():
            # Copy entire skill folder
            for item in source_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, dest / item.name)
        else:
            shutil.copy2(skill_md, dest / "SKILL.md")

        print(f"Installed '{parsed['name']}' from local path → {dest}")
    else:
        # Remote install from GitHub (ClawHub convention)
        skill_name = source
        print(f"Fetching '{skill_name}' from ClawHub...")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Try sparse checkout from openclaw/skills repo
            repo_url = f"https://github.com/openclaw/skills.git"
            try:
                subprocess.run(
                    ["git", "clone", "--depth=1", "--filter=blob:none",
                     "--sparse", repo_url, tmpdir],
                    check=True, capture_output=True, text=True,
                )
                subprocess.run(
                    ["git", "-C", tmpdir, "sparse-checkout", "set", skill_name],
                    check=True, capture_output=True, text=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Error: could not fetch '{skill_name}' from ClawHub: {e.stderr}",
                      file=sys.stderr)
                sys.exit(1)

            fetched_dir = Path(tmpdir) / skill_name
            skill_md = fetched_dir / "SKILL.md"
            if not skill_md.exists():
                print(f"Error: '{skill_name}' not found in ClawHub", file=sys.stderr)
                sys.exit(1)

            parsed = skills_module.parse_skill_md(skill_md)
            if parsed is None:
                print(f"Error: invalid SKILL.md in '{skill_name}'", file=sys.stderr)
                sys.exit(1)

            dest = COMMUNITY_DIR / parsed["name"]
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(fetched_dir, dest)

            print(f"Installed '{parsed['name']}' from ClawHub → {dest}")

    # Regenerate index
    skill_list = skills_module.build_index()
    print(f"Index rebuilt: {len(skill_list)} skill(s) total")


def cmd_list(args: argparse.Namespace) -> None:
    """List all installed skills."""
    skill_list = skills_module.discover_skills()
    if not skill_list:
        print("No skills installed.")
        return

    print(f"{'Name':<25} {'Source':<12} Description")
    print(f"{'─' * 25} {'─' * 12} {'─' * 40}")
    for s in skill_list:
        path = s["path"]
        if "/bundled/" in path:
            source = "bundled"
        elif "/community/" in path:
            source = "community"
        elif "/local/" in path:
            source = "local"
        else:
            source = "unknown"
        desc = s["description"][:60] + "..." if len(s["description"]) > 60 else s["description"]
        print(f"{s['name']:<25} {source:<12} {desc}")


def cmd_remove(args: argparse.Namespace) -> None:
    """Remove a community skill."""
    skill_name = args.name
    skill_dir = COMMUNITY_DIR / skill_name
    if not skill_dir.exists():
        # Also check local
        skill_dir = LOCAL_DIR / skill_name
        if not skill_dir.exists():
            print(f"Error: skill '{skill_name}' not found in community/ or local/",
                  file=sys.stderr)
            sys.exit(1)

    shutil.rmtree(skill_dir)
    print(f"Removed '{skill_name}'")

    # Regenerate index
    skill_list = skills_module.build_index()
    print(f"Index rebuilt: {len(skill_list)} skill(s) total")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import and manage OpenClaw-compatible skills for Roald"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    install_parser = sub.add_parser("install", help="Install a skill from ClawHub or local path")
    install_parser.add_argument("source", help="Skill name (from ClawHub) or local path")
    install_parser.set_defaults(func=cmd_install)

    list_parser = sub.add_parser("list", help="List all installed skills")
    list_parser.set_defaults(func=cmd_list)

    remove_parser = sub.add_parser("remove", help="Remove a community or local skill")
    remove_parser.add_argument("name", help="Skill name to remove")
    remove_parser.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
