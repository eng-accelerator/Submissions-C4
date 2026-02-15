"""
Cookbook synthesizer agent: creates actionable checklists from classified issues and remediations.
"""

from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from models import ClassifiedIssue, RemediationPlan


COOKBOOK_PROMPT = """You are an SRE creating a single incident response cookbook from the following analysis.

Classified issues:
{issues_text}

Remediation plans:
{remediations_text}

Produce one markdown document with:
1. Title: "Incident Response Cookbook"
2. Executive summary (2-3 sentences)
3. For each issue: a section with heading (severity + summary), affected services, and numbered actionable steps
4. A "Verification" section at the end with checks to confirm resolution
5. Optional "Rollback" section if applicable

Use clear headings (##), bullet lists, and numbered steps. Keep it concise and actionable.
Output only the markdown document.
"""


class CookbookSynthesizerAgent:
    """Synthesizes a single cookbook from issues and remediation plans."""

    def __init__(self, llm=None):
        self.llm = llm or get_llm(temperature=0.3)

    def generate(self, issues: List[ClassifiedIssue], remediations: List[RemediationPlan]) -> str:
        """Generate a markdown cookbook from issues and remediations."""
        if not issues and not remediations:
            return "# Incident Response Cookbook\n\nNo issues identified."
        issues_text = "\n".join(
            f"- [{i.severity}] {i.summary} (category: {i.category}, services: {i.affected_services})"
            for i in issues
        )
        remediations_text = "\n".join(
            f"- **{r.issue_summary}**\n  Steps: " + "; ".join(r.steps[:3])
            for r in remediations
        )
        prompt = COOKBOOK_PROMPT.format(
            issues_text=issues_text,
            remediations_text=remediations_text,
        )
        messages = [
            SystemMessage(content="Output only valid markdown."),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)
