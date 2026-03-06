"""skills.py — Skill loader, index builder, and requirement checker for Roald."""

import re
from pathlib import Path
from typing import Optional

import yaml

BASE_DIR = Path(__file__).parent
SKILLS_DIR = BASE_DIR / "skills"
INDEX_PATH = SKILLS_DIR / "_index.yaml"

# Scan order: local > community > bundled (higher precedence first)
SKILL_DIRS = [
    SKILLS_DIR / "local",
    SKILLS_DIR / "community",
    SKILLS_DIR / "bundled",
]


def parse_skill_md(path: Path) -> Optional[dict]:
    """Parse a SKILL.md file and extract YAML frontmatter + body."""
    text = path.read_text(encoding="utf-8")

    # Extract YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None

    if not isinstance(frontmatter, dict) or "name" not in frontmatter:
        return None

    return {
        "name": frontmatter["name"],
        "description": frontmatter.get("description", ""),
        "requires": frontmatter.get("requires", {}),
        "path": str(path),
        "body": match.group(2).strip(),
    }


def discover_skills() -> list[dict]:
    """Scan skill directories and return all valid skills (respecting precedence)."""
    seen_names: set[str] = set()
    skills: list[dict] = []

    for skill_dir in SKILL_DIRS:
        if not skill_dir.exists():
            continue
        for skill_md in sorted(skill_dir.rglob("SKILL.md")):
            parsed = parse_skill_md(skill_md)
            if parsed is None:
                continue
            if parsed["name"] in seen_names:
                continue  # higher-precedence version already loaded
            seen_names.add(parsed["name"])
            skills.append(parsed)

    return sorted(skills, key=lambda s: s["name"])


def build_index() -> list[dict]:
    """Discover skills, write _index.yaml, and return the skill list."""
    skills = discover_skills()

    index_entries = [
        {"name": s["name"], "description": s["description"], "path": s["path"]}
        for s in skills
    ]

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        yaml.dump(index_entries, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    return skills


def generate_index_markdown(skills: Optional[list[dict]] = None) -> str:
    """Generate a compact markdown snippet for injection into pulse prompts."""
    if skills is None:
        skills = discover_skills()

    if not skills:
        return "_No skills installed._"

    lines = ["| Skill | Description |", "|-------|-------------|"]
    for s in skills:
        lines.append(f"| `{s['name']}` | {s['description']} |")

    return "\n".join(lines)


def get_skill(name: str, skills: Optional[list[dict]] = None) -> Optional[dict]:
    """Look up a skill by name. Returns None if not found."""
    if skills is None:
        skills = discover_skills()
    for s in skills:
        if s["name"] == name:
            return s
    return None


def get_skill_tools(skill: dict) -> str:
    """Extract allowed tools from a skill's requires section."""
    requires = skill.get("requires", {})
    tools = requires.get("tools", [])
    if not tools:
        return "Read,Write,Glob,Grep"
    return ",".join(tools)
