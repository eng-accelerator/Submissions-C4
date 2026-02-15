"""
agents/fact_checker_agent.py
=============================
Agent 3: Fact-Checker Agent

RESPONSIBILITY:
    Cross-validate research findings across sources, assign confidence
    scores, and flag disputed or unverified claims.

INPUT (from state):
    original_query: str
    sources: List[dict]
    analysis: dict — AnalysisResult from analysis agent.

OUTPUT (to state):
    fact_check: dict — FactCheckResult with verified claims and scores.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from utils.llm_client import LLMClient
from prompts.fact_checker_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class VerifiedClaim:
    """A fact-checked research claim with confidence score."""
    claim: str
    confidence_score: float = 50.0     # 0-100
    status: str = "unverified"         # verified, disputed, unverified
    supporting_sources: list[int] = field(default_factory=list)
    contradicting_sources: list[int] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class FactCheckResult:
    """Complete fact-check output."""
    verified_claims: list[dict] = field(default_factory=list)
    overall_reliability_score: float = 50.0
    warnings: list[str] = field(default_factory=list)
    contradiction_details: list[dict] = field(default_factory=list)


class FactCheckerAgent:
    """
    Cross-validates research findings and assigns confidence scores.

    Evaluates each claim based on:
    - Number of independent confirming sources
    - Authority of those sources
    - Recency of information
    - Internal consistency with other findings
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()

    def run(self, state: dict) -> dict:
        """
        LangGraph node function: fact-check analysis findings.

        Args:
            state: Current ResearchState dict.

        Returns:
            State update with fact_check dict.
        """
        query = state.get("original_query", "")
        sources = state.get("sources", [])
        analysis = state.get("analysis", {})
        findings = analysis.get("findings", [])

        if not findings:
            logger.warning("No findings to fact-check")
            return {
                "fact_check": {
                    "verified_claims": [],
                    "overall_reliability_score": 0,
                    "warnings": ["No findings available for fact-checking"],
                    "contradiction_details": [],
                },
                "status": "Fact-check: No findings to verify",
            }

        # Format inputs for the LLM
        findings_text = self._format_findings(findings)
        sources_text = self._format_sources_brief(sources)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            findings_text=findings_text,
            sources_text=sources_text,
        )

        try:
            result = self.llm.chat_json(SYSTEM_PROMPT, user_prompt)

            fact_check = {
                "verified_claims": result.get("verified_claims", []),
                "overall_reliability_score": result.get("overall_reliability_score", 50),
                "warnings": result.get("warnings", []),
                "contradiction_details": result.get("contradiction_details", []),
            }

            # Count by status
            verified = sum(
                1 for c in fact_check["verified_claims"]
                if c.get("status") == "verified"
            )
            disputed = sum(
                1 for c in fact_check["verified_claims"]
                if c.get("status") == "disputed"
            )
            reliability = fact_check["overall_reliability_score"]

            logger.info(
                f"Fact-check complete: {verified} verified, {disputed} disputed, "
                f"reliability: {reliability}/100"
            )

            return {
                "fact_check": fact_check,
                "status": f"Fact-checked: {verified} verified, {disputed} disputed (reliability: {reliability}%)",
            }

        except Exception as e:
            logger.error(f"Fact-checking failed: {e}")
            # Graceful degradation: pass through findings as unverified
            return {
                "fact_check": {
                    "verified_claims": [
                        {
                            "claim": f.get("claim", ""),
                            "confidence_score": 50,
                            "status": "unverified",
                            "supporting_sources": f.get("source_indices", []),
                            "contradicting_sources": [],
                            "reasoning": "Fact-check unavailable — treating as unverified",
                        }
                        for f in findings
                    ],
                    "overall_reliability_score": 40,
                    "warnings": [
                        f"Fact-checking failed ({str(e)[:80]}). "
                        "All claims marked as unverified."
                    ],
                    "contradiction_details": [],
                },
                "status": f"Fact-check fallback: {str(e)[:100]}",
                "errors": state.get("errors", []) + [f"FactChecker: {str(e)}"],
            }

    @staticmethod
    def _format_findings(findings: list[dict]) -> str:
        """Format findings for fact-check prompt."""
        parts = []
        for i, f in enumerate(findings):
            parts.append(
                f"[Finding {i}]\n"
                f"  Claim: {f.get('claim', '')}\n"
                f"  Category: {f.get('category', 'unknown')}\n"
                f"  Source indices: {f.get('source_indices', [])}\n"
                f"  Importance: {f.get('importance', 'medium')}"
            )
        return "\n\n".join(parts)

    @staticmethod
    def _format_sources_brief(sources: list[dict]) -> str:
        """Format sources briefly for cross-reference context."""
        parts = []
        for i, src in enumerate(sources):
            parts.append(
                f"[{i}] {src.get('title', 'Unknown')} "
                f"({src.get('source_type', 'unknown')}, {src.get('domain', 'unknown')}) — "
                f"{src.get('content', '')[:300]}..."
            )
        return "\n".join(parts)
