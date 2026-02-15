"""
Skill loader for Astraeus agent skills.

Discovers and loads SKILL.md files following the Agent Skills standard
(agentskills.io). Each skill directory contains a SKILL.md with YAML
frontmatter (name, description) and markdown instructions.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Skill:
    """A loaded agent skill."""
    name: str
    description: str
    instructions: str
    path: Path
    references: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, path={self.path})"


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns (metadata_dict, body_markdown).
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    # Simple YAML parser for flat key-value pairs (avoids PyYAML dependency)
    metadata = {}
    for line in frontmatter_text.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()

    return metadata, body


def load_skill(skill_dir: Path) -> Optional[Skill]:
    """Load a single skill from a directory containing SKILL.md."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None

    content = skill_file.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(content)

    name = metadata.get("name", skill_dir.name)
    description = metadata.get("description", "")

    if not name:
        return None

    # Load references if present
    references = {}
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref_file in refs_dir.iterdir():
            if ref_file.is_file() and ref_file.suffix in (".md", ".txt"):
                references[ref_file.name] = ref_file.read_text(encoding="utf-8")

    return Skill(
        name=name,
        description=description,
        instructions=body.strip(),
        path=skill_dir,
        references=references,
    )


def discover_skills(skills_root: Path | str | None = None) -> List[Skill]:
    """Discover and load all skills from the skills directory.

    Args:
        skills_root: Path to the skills directory. Defaults to ./skills/
                     relative to this file's parent.

    Returns:
        List of loaded Skill objects, sorted by name.
    """
    if skills_root is None:
        skills_root = Path(__file__).parent
    else:
        skills_root = Path(skills_root)

    if not skills_root.is_dir():
        return []

    skills = []
    for entry in sorted(skills_root.iterdir()):
        if entry.is_dir() and not entry.name.startswith(("_", ".")):
            skill = load_skill(entry)
            if skill is not None:
                skills.append(skill)

    return skills


def get_skill(name: str, skills_root: Path | str | None = None) -> Optional[Skill]:
    """Load a specific skill by name."""
    all_skills = discover_skills(skills_root)
    for skill in all_skills:
        if skill.name == name:
            return skill
    return None


def get_skill_for_agent(agent_id: str, skills_root: Path | str | None = None) -> Optional[Skill]:
    """Find the skill that maps to a given agent ID.

    Mapping:
        coordinator       → query-expansion
        retriever          → evidence-retrieval
        critical_analysis  → contradiction-detection
        fact_checker       → source-credibility
        insight_generator  → theme-synthesis
        report_builder     → report-generation
    """
    agent_skill_map = {
        "coordinator": "query-expansion",
        "retriever": "evidence-retrieval",
        "critical_analysis": "contradiction-detection",
        "fact_checker": "source-credibility",
        "insight_generator": "theme-synthesis",
        "report_builder": "report-generation",
    }
    skill_name = agent_skill_map.get(agent_id)
    if skill_name is None:
        return None
    return get_skill(skill_name, skills_root)
