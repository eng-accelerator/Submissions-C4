"""Tests for the skills loader."""

import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills import discover_skills, load_skill, get_skill, get_skill_for_agent, _parse_frontmatter, Skill

SKILLS_DIR = Path(__file__).parent.parent / "skills"


class TestFrontmatterParser(unittest.TestCase):
    """Test YAML frontmatter parsing."""

    def test_valid_frontmatter(self):
        content = "---\nname: test-skill\ndescription: A test skill\n---\n\n# Instructions\nDo stuff."
        meta, body = _parse_frontmatter(content)
        self.assertEqual(meta["name"], "test-skill")
        self.assertEqual(meta["description"], "A test skill")
        self.assertIn("# Instructions", body)

    def test_no_frontmatter(self):
        content = "# Just markdown\nNo frontmatter here."
        meta, body = _parse_frontmatter(content)
        self.assertEqual(meta, {})
        self.assertEqual(body, content)

    def test_empty_frontmatter(self):
        content = "---\n---\n\nBody."
        meta, body = _parse_frontmatter(content)
        self.assertEqual(meta, {})
        self.assertIn("Body.", body)


class TestSkillDiscovery(unittest.TestCase):
    """Test skill discovery from the skills directory."""

    def test_discover_all_skills(self):
        skills = discover_skills(SKILLS_DIR)
        self.assertGreaterEqual(len(skills), 6)

    def test_all_skills_have_names(self):
        skills = discover_skills(SKILLS_DIR)
        for skill in skills:
            self.assertTrue(skill.name, f"Skill at {skill.path} has no name")

    def test_all_skills_have_descriptions(self):
        skills = discover_skills(SKILLS_DIR)
        for skill in skills:
            self.assertTrue(skill.description, f"Skill {skill.name} has no description")

    def test_all_skills_have_instructions(self):
        skills = discover_skills(SKILLS_DIR)
        for skill in skills:
            self.assertTrue(skill.instructions, f"Skill {skill.name} has no instructions")

    def test_skills_sorted_by_name(self):
        skills = discover_skills(SKILLS_DIR)
        names = [s.name for s in skills]
        self.assertEqual(names, sorted(names))

    def test_nonexistent_directory(self):
        skills = discover_skills(Path("/nonexistent/path"))
        self.assertEqual(skills, [])


class TestSkillLoading(unittest.TestCase):
    """Test loading individual skills."""

    def test_load_query_expansion(self):
        skill = load_skill(SKILLS_DIR / "query-expansion")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "query-expansion")
        self.assertIn("Expand", skill.instructions)

    def test_load_evidence_retrieval(self):
        skill = load_skill(SKILLS_DIR / "evidence-retrieval")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "evidence-retrieval")

    def test_load_contradiction_detection(self):
        skill = load_skill(SKILLS_DIR / "contradiction-detection")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "contradiction-detection")

    def test_load_source_credibility(self):
        skill = load_skill(SKILLS_DIR / "source-credibility")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "source-credibility")

    def test_load_theme_synthesis(self):
        skill = load_skill(SKILLS_DIR / "theme-synthesis")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "theme-synthesis")

    def test_load_report_generation(self):
        skill = load_skill(SKILLS_DIR / "report-generation")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "report-generation")

    def test_load_nonexistent(self):
        skill = load_skill(SKILLS_DIR / "nonexistent-skill")
        self.assertIsNone(skill)


class TestGetSkill(unittest.TestCase):
    """Test skill lookup by name."""

    def test_get_existing(self):
        skill = get_skill("query-expansion", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "query-expansion")

    def test_get_nonexistent(self):
        skill = get_skill("does-not-exist", SKILLS_DIR)
        self.assertIsNone(skill)


class TestAgentSkillMapping(unittest.TestCase):
    """Test agent-to-skill mapping."""

    def test_coordinator_maps_to_query_expansion(self):
        skill = get_skill_for_agent("coordinator", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "query-expansion")

    def test_retriever_maps_to_evidence_retrieval(self):
        skill = get_skill_for_agent("retriever", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "evidence-retrieval")

    def test_critical_analysis_maps_to_contradiction_detection(self):
        skill = get_skill_for_agent("critical_analysis", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "contradiction-detection")

    def test_fact_checker_maps_to_source_credibility(self):
        skill = get_skill_for_agent("fact_checker", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "source-credibility")

    def test_insight_generator_maps_to_theme_synthesis(self):
        skill = get_skill_for_agent("insight_generator", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "theme-synthesis")

    def test_report_builder_maps_to_report_generation(self):
        skill = get_skill_for_agent("report_builder", SKILLS_DIR)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "report-generation")

    def test_unknown_agent_returns_none(self):
        skill = get_skill_for_agent("nonexistent_agent", SKILLS_DIR)
        self.assertIsNone(skill)


class TestSkillDataclass(unittest.TestCase):
    """Test the Skill dataclass."""

    def test_repr(self):
        skill = Skill(name="test", description="desc", instructions="body", path=Path("/tmp"))
        self.assertIn("test", repr(skill))

    def test_default_references(self):
        skill = Skill(name="test", description="desc", instructions="body", path=Path("/tmp"))
        self.assertEqual(skill.references, {})


if __name__ == "__main__":
    unittest.main()
