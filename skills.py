"""skills.py — Skill loader, index builder, and registry for Roald."""

import re
from pathlib import Path
from typing import Optional

import yaml

BASE_DIR = Path(__file__).parent
SKILLS_DIR = BASE_DIR / "skills"
INDEX_PATH = SKILLS_DIR / "_index.yaml"

# Search order: local > community > bundled (higher precedence first)
SKILL_DIRS = [
    SKILLS_DIR / "local",
    SKILLS_DIR / "community",
    SKILLS_DIR / "bundled",
]

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill(skill_path: Path) -> Optional[dict]:
    """Parse a SKILL.md file and return metadata dict, or None on failure."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None
    text = skill_md.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict) or "name" not in meta:
        return None
    # Extract body (everything after frontmatter)
    body = text[match.end():]
    return {
        "name": str(meta["name"]),
        "description": str(meta.get("description", "")),
        "requires": meta.get("requires", []),
        "path": str(skill_path),
        "body": body,
    }


def discover_skills() -> dict[str, dict]:
    """Scan all skill directories and return name→metadata, respecting precedence."""
    skills: dict[str, dict] = {}
    for skill_dir in SKILL_DIRS:
        if not skill_dir.exists():
            continue
        for child in sorted(skill_dir.iterdir()):
            if not child.is_dir():
                continue
            parsed = parse_skill(child)
            if parsed and parsed["name"] not in skills:
                skills[parsed["name"]] = parsed
    return skills


def check_requirements(skill: dict) -> bool:
    """Check if a skill's requirements are met (env vars, binaries)."""
    import shutil
    import os

    for req in skill.get("requires", []):
        req = str(req)
        if req.startswith("env:"):
            if not os.environ.get(req[4:]):
                return False
        elif req.startswith("bin:"):
            if not shutil.which(req[4:]):
                return False
    return True


def build_index() -> list[dict]:
    """Discover skills, filter by requirements, write _index.yaml, return list."""
    skills = discover_skills()
    index = []
    for name, meta in sorted(skills.items()):
        if not check_requirements(meta):
            continue
        index.append({
            "name": meta["name"],
            "description": meta["description"],
            "path": meta["path"],
        })
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(yaml.dump(index, default_flow_style=False), encoding="utf-8")
    return index


def generate_index_markdown() -> str:
    """Generate a markdown snippet for injection into pulse prompts."""
    index = build_index()
    if not index:
        return "_No skills installed._"
    lines = ["| Skill | Description |", "|-------|-------------|"]
    for entry in index:
        lines.append(f"| `{entry['name']}` | {entry['description']} |")
    return "\n".join(lines)


def load_skill_body(skill_name: str) -> Optional[str]:
    """Load the full SKILL.md content for a given skill name."""
    skills = discover_skills()
    meta = skills.get(skill_name)
    if not meta:
        return None
    skill_md = Path(meta["path"]) / "SKILL.md"
    if not skill_md.exists():
        return None
    return skill_md.read_text(encoding="utf-8")
