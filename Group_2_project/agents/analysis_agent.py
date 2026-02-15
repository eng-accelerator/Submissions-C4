"""
agents/analysis_agent.py
=========================
Agent 2: Critical Analysis Agent

RESPONSIBILITY:
    Synthesize raw sources into structured findings, detect contradictions,
    identify gaps, and assess source reliability.

INPUT (from state):
    original_query: str
    sources: List[dict] — SourceDocument dicts from retriever.

OUTPUT (to state):
    analysis: dict — AnalysisResult with findings, contradictions, gaps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from utils.llm_client import LLMClient
from prompts.analysis_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """A single research finding extracted from sources."""
    claim: str
    source_indices: list[int] = field(default_factory=list)
    category: str = "fact"        # fact, statistic, opinion, prediction
    importance: str = "medium"    # high, medium, low


@dataclass
class AnalysisResult:
    """Complete analysis output."""
    executive_summary: str = ""
    findings: list[dict] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    source_assessments: list[dict] = field(default_factory=list)


class AnalysisAgent:
    """
    Critically analyzes collected sources to produce structured findings.

    Uses the LLM to:
    1. Summarize key information across all sources
    2. Extract specific claims with source attribution
    3. Detect contradictions between sources
    4. Identify information gaps
    5. Assess source reliability
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()

    def run(self, state: dict) -> dict:
        """
        LangGraph node function: analyze the collected sources.

        Args:
            state: Current ResearchState dict.

        Returns:
            State update with analysis dict.
        """
        query = state.get("original_query", "")
        sources = state.get("sources", [])

        if not sources:
            logger.warning("No sources to analyze")
            return {
                "analysis": {
                    "executive_summary": "No sources were found for this query.",
                    "findings": [],
                    "contradictions": [],
                    "gaps": ["No sources were retrieved"],
                    "source_assessments": [],
                },
                "status": "Analysis: No sources available",
            }

        # Format sources for the LLM
        sources_text = self._format_sources(sources)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            sources_text=sources_text,
        )

        try:
            result = self.llm.chat_json(SYSTEM_PROMPT, user_prompt)

            analysis = {
                "executive_summary": result.get("executive_summary", ""),
                "findings": result.get("findings", []),
                "contradictions": result.get("contradictions", []),
                "gaps": result.get("gaps", []),
                "source_assessments": result.get("source_assessments", []),
            }

            n_findings = len(analysis["findings"])
            n_contradictions = len(analysis["contradictions"])
            n_gaps = len(analysis["gaps"])

            logger.info(
                f"Analysis complete: {n_findings} findings, "
                f"{n_contradictions} contradictions, {n_gaps} gaps"
            )

            return {
                "analysis": analysis,
                "status": f"Analyzed: {n_findings} findings, {n_contradictions} contradictions",
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "analysis": {
                    "executive_summary": f"Analysis encountered an error: {str(e)}",
                    "findings": [],
                    "contradictions": [],
                    "gaps": ["Analysis failed — manual review recommended"],
                    "source_assessments": [],
                },
                "status": f"Analysis error: {str(e)[:100]}",
                "errors": state.get("errors", []) + [f"Analysis: {str(e)}"],
            }

    @staticmethod
    def _format_sources(sources: list[dict]) -> str:
        """Format sources for the LLM prompt."""
        parts = []
        for i, src in enumerate(sources):
            parts.append(
                f"[Source {i}]\n"
                f"  Title: {src.get('title', 'Unknown')}\n"
                f"  URL: {src.get('url', 'N/A')}\n"
                f"  Type: {src.get('source_type', 'unknown')}\n"
                f"  Domain: {src.get('domain', 'unknown')}\n"
                f"  Content:\n{src.get('content', '')[:1500]}\n"
            )
        return "\n---\n".join(parts)
