"""
agents/report_agent.py
=======================
Agent 5: Report Builder Agent

RESPONSIBILITY:
    Compile all research outputs (analysis, fact-checks, insights)
    into a structured, professional report. Also evaluates overall
    research quality and suggests follow-up queries if quality is low.

INPUT (from state):
    original_query, sources, analysis, fact_check, insights

OUTPUT (to state):
    report: dict — Full ReportResult with quality score.
    quality_score: float — For the quality gate conditional edge.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from utils.llm_client import LLMClient
from prompts.report_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class ReportResult:
    """Complete research report output."""
    title: str = ""
    executive_summary: str = ""
    key_findings: list[dict] = field(default_factory=list)
    contradictions_and_gaps: str = ""
    insights_and_trends: str = ""
    source_reliability: str = ""
    methodology_note: str = ""
    sources_cited: list[dict] = field(default_factory=list)
    quality_score: float = 0.0
    quality_breakdown: dict = field(default_factory=dict)
    follow_up_queries: list[str] = field(default_factory=list)
    generated_at: str = ""


class ReportAgent:
    """
    Compiles all research outputs into a structured report.

    The report includes:
    1. Executive Summary
    2. Key Findings (with confidence scores)
    3. Contradictions & Gaps
    4. Insights & Trends
    5. Source Reliability Assessment
    6. Quality Score (0-100)
    7. Follow-up Queries (for reflection loop)
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()

    def run(self, state: dict) -> dict:
        """
        LangGraph node function: build the final report.

        Args:
            state: Current ResearchState dict.

        Returns:
            State update with report dict and quality_score.
        """
        query = state.get("original_query", "")
        sources = state.get("sources", [])
        analysis = state.get("analysis", {})
        fact_check = state.get("fact_check", {})
        insights = state.get("insights", {})

        # Format all inputs for the report builder
        analysis_summary = analysis.get("executive_summary", "No analysis available.")

        verified_findings_text = self._format_verified_findings(
            analysis.get("findings", []),
            fact_check.get("verified_claims", []),
        )

        contradictions_text = self._format_contradictions(
            analysis.get("contradictions", []),
            analysis.get("gaps", []),
            fact_check.get("warnings", []),
        )

        insights_text = self._format_insights(insights)

        sources_summary = self._format_sources_summary(sources)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            analysis_summary=analysis_summary,
            verified_findings_text=verified_findings_text,
            contradictions_text=contradictions_text,
            insights_text=insights_text,
            source_count=len(sources),
            sources_summary=sources_summary,
        )

        try:
            result = self.llm.chat_json(SYSTEM_PROMPT, user_prompt)

            quality_score = float(result.get("quality_score", 50))

            report = {
                "title": result.get("title", f"Research Report: {query}"),
                "executive_summary": result.get("executive_summary", analysis_summary),
                "key_findings": result.get("key_findings", []),
                "contradictions_and_gaps": result.get("contradictions_and_gaps", ""),
                "insights_and_trends": result.get("insights_and_trends", ""),
                "source_reliability": result.get("source_reliability", ""),
                "methodology_note": result.get(
                    "methodology_note",
                    "This report was generated using a multi-agent AI research system "
                    "with automated web search, critical analysis, fact-checking, "
                    "and insight generation."
                ),
                "sources_cited": [
                    {"title": s.get("title", ""), "url": s.get("url", "")}
                    for s in sources
                ],
                "quality_score": quality_score,
                "quality_breakdown": result.get("quality_breakdown", {}),
                "follow_up_queries": result.get("follow_up_queries", []),
                "generated_at": datetime.now().isoformat(),
            }

            logger.info(f"Report built. Quality score: {quality_score}/100")

            return {
                "report": report,
                "quality_score": quality_score,
                "status": f"Report complete (quality: {quality_score}/100)",
            }

        except Exception as e:
            logger.error(f"Report building failed: {e}")
            # Fallback: assemble a basic report from raw data
            fallback_report = self._build_fallback_report(
                query, sources, analysis, fact_check, insights, str(e)
            )
            return {
                "report": fallback_report,
                "quality_score": 30,
                "status": f"Report fallback: {str(e)[:100]}",
                "errors": state.get("errors", []) + [f"Report: {str(e)}"],
            }

    @staticmethod
    def _format_verified_findings(findings: list[dict], verified: list[dict]) -> str:
        """Combine findings with their verification scores."""
        parts = []
        for i, f in enumerate(findings):
            claim = f.get("claim", "")
            # Find matching verification
            vc = next(
                (v for v in verified if v.get("claim", "")[:60] == claim[:60]),
                {},
            )
            confidence = vc.get("confidence_score", "N/A")
            status = vc.get("status", "unverified")
            parts.append(f"- [{status}, {confidence}%] {claim}")
        return "\n".join(parts) if parts else "No findings available."

    @staticmethod
    def _format_contradictions(contradictions: list[dict], gaps: list[str], warnings: list[str]) -> str:
        """Format contradictions, gaps, and warnings together."""
        parts = []
        if contradictions:
            parts.append("CONTRADICTIONS:")
            for c in contradictions:
                parts.append(f"  - {c.get('topic', '')}: {c.get('position_a', '')} vs {c.get('position_b', '')}")
        if gaps:
            parts.append("\nGAPS IN RESEARCH:")
            for g in gaps:
                parts.append(f"  - {g}")
        if warnings:
            parts.append("\nWARNINGS:")
            for w in warnings:
                parts.append(f"  - {w}")
        return "\n".join(parts) if parts else "No significant contradictions or gaps."

    @staticmethod
    def _format_insights(insights: dict) -> str:
        """Format insights for the report prompt."""
        parts = []
        for h in insights.get("hypotheses", []):
            parts.append(
                f"HYPOTHESIS ({h.get('confidence', 'medium')} confidence): "
                f"{h.get('statement', '')}"
            )
        for t in insights.get("trends", []):
            parts.append(
                f"TREND ({t.get('direction', '')}): {t.get('description', '')}"
            )
        for p in insights.get("key_patterns", []):
            parts.append(f"PATTERN: {p}")
        for imp in insights.get("implications", []):
            parts.append(f"IMPLICATION: {imp}")
        return "\n".join(parts) if parts else "No insights generated."

    @staticmethod
    def _format_sources_summary(sources: list[dict]) -> str:
        """Brief source summary for the report."""
        parts = []
        for i, s in enumerate(sources):
            parts.append(
                f"[{i}] {s.get('title', 'Unknown')} "
                f"({s.get('source_type', 'unknown')}) — {s.get('url', '')}"
            )
        return "\n".join(parts) if parts else "No sources available."

    @staticmethod
    def _build_fallback_report(
        query: str, sources: list, analysis: dict,
        fact_check: dict, insights: dict, error: str,
    ) -> dict:
        """Build a basic report when the LLM-based builder fails."""
        return {
            "title": f"Research Report: {query}",
            "executive_summary": analysis.get(
                "executive_summary",
                "Report generation encountered an error. Raw findings are included below.",
            ),
            "key_findings": [
                {"finding": f.get("claim", ""), "confidence": 50, "sources_count": len(f.get("source_indices", []))}
                for f in analysis.get("findings", [])[:10]
            ],
            "contradictions_and_gaps": "Report builder error — review raw analysis data.",
            "insights_and_trends": str(insights.get("hypotheses", [])),
            "source_reliability": f"Overall reliability: {fact_check.get('overall_reliability_score', 'N/A')}/100",
            "methodology_note": (
                f"Note: Report assembly encountered an error ({error[:100]}). "
                "This is a fallback report with reduced formatting."
            ),
            "sources_cited": [
                {"title": s.get("title", ""), "url": s.get("url", "")}
                for s in sources
            ],
            "quality_score": 30,
            "quality_breakdown": {},
            "follow_up_queries": [query],
            "generated_at": datetime.now().isoformat(),
        }
