"""
Remediation agent: maps each detected issue to fixes and rationale using the knowledge base and LLM.
"""

from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from models import ClassifiedIssue, RemediationPlan
from utils.knowledge_base import RemediationKB


REMEDIATION_PROMPT = """You are an SRE expert. Given an issue and relevant runbook excerpts, produce a concise remediation plan.

Issue: {issue_summary}
Category: {category}, Subcategory: {subcategory}, Severity: {severity}
Affected services: {affected_services}

Runbook excerpts from knowledge base:
{runbook_excerpts}

Output a short remediation plan (2-5 bullet steps) and a one-line time estimate (e.g. "5-10 minutes").
If no runbook is relevant, suggest generic steps based on the issue type.
Format your response as:
STEPS:
1. ...
2. ...
TIME_ESTIMATE: ...
"""


class RemediationAgent:
    """Maps classified issues to remediation plans using RAG and LLM."""

    def __init__(self, knowledge_base: RemediationKB = None, llm=None):
        self.kb = knowledge_base or RemediationKB()
        self.llm = llm or get_llm(temperature=0.2)

    def find_remediations(self, issues: List[ClassifiedIssue]) -> List[RemediationPlan]:
        """For each issue, search KB and optionally LLM to produce a RemediationPlan."""
        plans = []
        for issue in issues:
            desc = f"{issue.summary} {issue.category} {issue.subcategory}"
            hits = self.kb.search_remediation(desc, category=issue.category, k=3)
            runbook_excerpts = "\n---\n".join(
                (h["content"][:1500] for h in hits if h.get("content"))
            ) or "No runbooks found."
            prompt = REMEDIATION_PROMPT.format(
                issue_summary=issue.summary,
                category=issue.category,
                subcategory=issue.subcategory,
                severity=issue.severity,
                affected_services=", ".join(issue.affected_services) or "unknown",
                runbook_excerpts=runbook_excerpts,
            )
            messages = [
                SystemMessage(content="Output STEPS and TIME_ESTIMATE clearly."),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            text = response.content if hasattr(response, "content") else str(response)
            steps = []
            time_est = None
            for line in text.splitlines():
                line = line.strip()
                if line.upper().startswith("TIME_ESTIMATE:"):
                    time_est = line.split(":", 1)[-1].strip()
                elif line and line[0].isdigit() and "." in line:
                    steps.append(line.split(".", 1)[-1].strip())
                elif line.startswith("- ") or (len(line) > 2 and line[1] == "."):
                    steps.append(line.lstrip("- ").split(".", 1)[-1].strip() if "." in line else line)
            runbook_content = hits[0]["content"] if hits else text
            plan = RemediationPlan(
                issue_summary=issue.summary,
                runbook_content=runbook_content[:3000],
                steps=steps or [text[:500]],
                category=issue.category,
                subcategory=issue.subcategory,
                time_estimate=time_est,
                success_rate=hits[0].get("metadata", {}).get("success_rate") if hits else None,
                runbook_id=hits[0].get("id") if hits else None,
            )
            plans.append(plan)
        return plans
