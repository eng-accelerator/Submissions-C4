"""
agents/insight_agent.py
========================
Agent 4: Insight Generation Agent

RESPONSIBILITY:
    Go beyond summarization to generate hypotheses, identify trends,
    and provide forward-looking analysis using reasoning chains.

INPUT (from state):
    original_query: str
    analysis: dict — Findings and gaps from analysis agent.
    fact_check: dict — Verified claims with confidence scores.

OUTPUT (to state):
    insights: dict — InsightResult with hypotheses, trends, patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from utils.llm_client import LLMClient
from prompts.insight_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    """A research hypothesis with supporting evidence."""
    statement: str
    confidence: str = "medium"
    supporting_evidence: list[str] = field(default_factory=list)
    reasoning_chain: str = ""


@dataclass
class Trend:
    """An identified trend or pattern."""
    description: str
    direction: str = "emerging"
    evidence: list[str] = field(default_factory=list)
    timeframe: str = "medium-term"


@dataclass
class InsightResult:
    """Complete insight generation output."""
    hypotheses: list[dict] = field(default_factory=list)
    trends: list[dict] = field(default_factory=list)
    key_patterns: list[str] = field(default_factory=list)
    implications: list[str] = field(default_factory=list)
    further_questions: list[str] = field(default_factory=list)


class InsightAgent:
    """
    Generates strategic insights from research findings.

    Uses chain-of-thought reasoning to:
    1. Formulate testable hypotheses grounded in evidence
    2. Identify emerging trends and patterns
    3. Derive broader implications
    4. Suggest follow-up research questions
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()

    def run(self, state: dict) -> dict:
        """
        LangGraph node function: generate insights from findings.

        Args:
            state: Current ResearchState dict.

        Returns:
            State update with insights dict.
        """
        query = state.get("original_query", "")
        analysis = state.get("analysis", {})
        fact_check = state.get("fact_check", {})

        findings = analysis.get("findings", [])
        verified_claims = fact_check.get("verified_claims", [])
        gaps = analysis.get("gaps", [])

        # Format inputs
        findings_text = self._format_verified_findings(findings, verified_claims)
        fact_check_text = self._format_fact_check_summary(fact_check)
        gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else "No significant gaps identified."

        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            findings_text=findings_text,
            fact_check_text=fact_check_text,
            gaps_text=gaps_text,
        )

        try:
            result = self.llm.chat_json(SYSTEM_PROMPT, user_prompt)

            insights = {
                "hypotheses": result.get("hypotheses", []),
                "trends": result.get("trends", []),
                "key_patterns": result.get("key_patterns", []),
                "implications": result.get("implications", []),
                "further_questions": result.get("further_questions", []),
            }

            n_hyp = len(insights["hypotheses"])
            n_trends = len(insights["trends"])

            logger.info(
                f"Insights generated: {n_hyp} hypotheses, "
                f"{n_trends} trends, "
                f"{len(insights['key_patterns'])} patterns"
            )

            return {
                "insights": insights,
                "status": f"Generated {n_hyp} hypotheses and {n_trends} trends",
            }

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return {
                "insights": {
                    "hypotheses": [],
                    "trends": [],
                    "key_patterns": [],
                    "implications": [f"Insight generation encountered an error: {str(e)}"],
                    "further_questions": [
                        "What are the main factors driving this topic?",
                        "What are experts predicting for the near future?",
                    ],
                },
                "status": f"Insight error: {str(e)[:100]}",
                "errors": state.get("errors", []) + [f"Insights: {str(e)}"],
            }

    @staticmethod
    def _format_verified_findings(findings: list[dict], verified: list[dict]) -> str:
        """Merge findings with their verification status."""
        # Build a lookup from claim text to verification info
        verification_map = {}
        for vc in verified:
            claim_key = vc.get("claim", "")[:80]
            verification_map[claim_key] = vc

        parts = []
        for i, f in enumerate(findings):
            claim = f.get("claim", "")
            claim_key = claim[:80]
            vc = verification_map.get(claim_key, {})
            confidence = vc.get("confidence_score", "N/A")
            status = vc.get("status", "unverified")

            parts.append(
                f"[{i}] {claim}\n"
                f"    Category: {f.get('category', 'unknown')} | "
                f"Confidence: {confidence}% | Status: {status}"
            )

        return "\n\n".join(parts) if parts else "No findings available."

    @staticmethod
    def _format_fact_check_summary(fact_check: dict) -> str:
        """Format fact-check results as a brief summary."""
        reliability = fact_check.get("overall_reliability_score", "N/A")
        warnings = fact_check.get("warnings", [])
        n_verified = sum(
            1 for c in fact_check.get("verified_claims", [])
            if c.get("status") == "verified"
        )
        n_disputed = sum(
            1 for c in fact_check.get("verified_claims", [])
            if c.get("status") == "disputed"
        )
        total = len(fact_check.get("verified_claims", []))

        summary = (
            f"Overall reliability: {reliability}/100\n"
            f"Claims: {total} total, {n_verified} verified, {n_disputed} disputed\n"
        )
        if warnings:
            summary += "Warnings:\n" + "\n".join(f"  - {w}" for w in warnings)

        return summary
