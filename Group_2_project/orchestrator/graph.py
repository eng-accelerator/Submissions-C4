"""
orchestrator/graph.py
======================
LangGraph StateGraph definition for the multi-agent research pipeline.

This is the "brain" of the system — it defines HOW agents collaborate:
    1. The execution order (edges)
    2. The shared state (ResearchState)
    3. Conditional logic (quality gate reflection loop)

PIPELINE ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │  START → decompose → retrieve → analyze → fact_check            │
    │              ▲                                    │              │
    │              │                                    ▼              │
    │              │                            generate_insights      │
    │              │                                    │              │
    │              │                                    ▼              │
    │              └── (quality < threshold) ── build_report → END    │
    │                   & iteration < max                              │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘

USAGE:
    from orchestrator.graph import create_research_graph, run_research
    result = run_research("What is the impact of AI on healthcare?")
"""

from __future__ import annotations

import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from orchestrator.state import ResearchState
from agents.decomposer_agent import DecomposerAgent
from agents.retriever_agent import RetrieverAgent
from agents.analysis_agent import AnalysisAgent
from agents.fact_checker_agent import FactCheckerAgent
from agents.insight_agent import InsightAgent
from agents.report_agent import ReportAgent
from utils.llm_client import LLMClient
from utils.callbacks import ProgressTracker
from config import settings

logger = logging.getLogger(__name__)


def create_research_graph(
    llm: Optional[LLMClient] = None,
    tracker: Optional[ProgressTracker] = None,
) -> StateGraph:
    """
    Build and compile the LangGraph research pipeline.

    Args:
        llm: Shared LLM client instance (for token tracking).
        tracker: Optional progress tracker for UI updates.

    Returns:
        Compiled LangGraph StateGraph ready to invoke.
    """
    llm = llm or LLMClient()

    # Initialize all agents with the shared LLM client
    decomposer = DecomposerAgent(llm)
    retriever = RetrieverAgent(llm)
    analyzer = AnalysisAgent(llm)
    fact_checker = FactCheckerAgent(llm)
    insight_gen = InsightAgent(llm)
    reporter = ReportAgent(llm)

    # ── Node Functions ───────────────────────────────────────
    # Each wraps an agent's run() with progress tracking

    def decompose(state: ResearchState) -> dict:
        """Node: Decompose query into sub-queries."""
        llm.set_agent("Decomposer")
        if tracker:
            with tracker.agent_step("decomposer"):
                result = decomposer.run(state)
                tracker.update_message(
                    f"Created {len(result.get('sub_queries', []))} sub-queries"
                )
                return result
        return decomposer.run(state)

    def retrieve(state: ResearchState) -> dict:
        """Node: Retrieve sources for all sub-queries."""
        llm.set_agent("Retriever")
        if tracker:
            with tracker.agent_step("retriever"):
                result = retriever.run(state)
                n = len(result.get("sources", []))
                tracker.update_message(f"Collected {n} sources")
                llm._tavily_calls = getattr(llm, "_tavily_calls", 0) + retriever.tavily_calls
                retriever.tavily_calls = 0  # Reset for next iteration
                return result
        result = retriever.run(state)
        llm._tavily_calls = getattr(llm, "_tavily_calls", 0) + retriever.tavily_calls
        retriever.tavily_calls = 0
        return result

    def analyze(state: ResearchState) -> dict:
        """Node: Critically analyze collected sources."""
        llm.set_agent("Analyzer")
        if tracker:
            with tracker.agent_step("analyzer"):
                result = analyzer.run(state)
                n = len(result.get("analysis", {}).get("findings", []))
                tracker.update_message(f"Extracted {n} findings")
                return result
        return analyzer.run(state)

    def fact_check(state: ResearchState) -> dict:
        """Node: Cross-validate findings and assign confidence scores."""
        llm.set_agent("Fact-Checker")
        if tracker:
            with tracker.agent_step("fact_checker"):
                result = fact_checker.run(state)
                score = result.get("fact_check", {}).get(
                    "overall_reliability_score", 0
                )
                tracker.update_message(f"Reliability score: {score}/100")
                return result
        return fact_checker.run(state)

    def generate_insights(state: ResearchState) -> dict:
        """Node: Generate hypotheses and identify trends."""
        llm.set_agent("Insight")
        if tracker:
            with tracker.agent_step("insight"):
                result = insight_gen.run(state)
                n = len(result.get("insights", {}).get("hypotheses", []))
                tracker.update_message(f"Generated {n} hypotheses")
                return result
        return insight_gen.run(state)

    def build_report(state: ResearchState) -> dict:
        """Node: Compile final report and evaluate quality."""
        llm.set_agent("Reporter")
        if tracker:
            with tracker.agent_step("reporter"):
                result = reporter.run(state)
                score = result.get("quality_score", 0)
                tracker.update_message(f"Quality: {score}/100")
                return result
        return reporter.run(state)

    # ── Quality Gate (Conditional Edge Router) ───────────────

    def quality_gate(state: ResearchState) -> str:
        """
        Decide whether to accept the report or loop back for refinement.

        Returns:
            "accept" — Quality is sufficient or max iterations reached.
            "refine" — Quality is below threshold, loop back to decomposer.
        """
        quality = state.get("quality_score", 0)
        iteration = state.get("iteration", 0)
        max_iter = state.get("max_iterations", settings.MAX_ITERATIONS)
        threshold = settings.QUALITY_THRESHOLD

        if tracker:
            with tracker.agent_step("quality_gate"):
                pass_fail = "PASS" if quality >= threshold else "FAIL"
                tracker.update_message(
                    f"Quality: {quality}/100 (threshold: {threshold}) — "
                    f"{pass_fail} | Iteration {iteration + 1}/{max_iter}"
                )

        if quality >= threshold:
            logger.info(f"Quality gate PASSED: {quality} >= {threshold}")
            return "accept"

        if iteration + 1 >= max_iter:
            logger.warning(
                f"Quality gate: {quality} < {threshold}, "
                f"but max iterations ({max_iter}) reached. Accepting."
            )
            return "accept"

        logger.info(
            f"Quality gate FAILED: {quality} < {threshold}. "
            f"Refining (iteration {iteration + 1}/{max_iter})."
        )
        return "refine"

    # ── Iteration Counter ────────────────────────────────────

    def increment_iteration(state: ResearchState) -> dict:
        """Increment the iteration counter before looping back."""
        return {"iteration": state.get("iteration", 0) + 1}

    # ── Build the Graph ──────────────────────────────────────

    builder = StateGraph(ResearchState)

    # Add all nodes
    builder.add_node("decompose", decompose)
    builder.add_node("retrieve", retrieve)
    builder.add_node("analyze", analyze)
    builder.add_node("fact_check", fact_check)
    builder.add_node("generate_insights", generate_insights)
    builder.add_node("build_report", build_report)
    builder.add_node("increment_iteration", increment_iteration)

    # Set entry point
    builder.set_entry_point("decompose")

    # Linear edges: decompose → retrieve → analyze → fact_check → insights → report
    builder.add_edge("decompose", "retrieve")
    builder.add_edge("retrieve", "analyze")
    builder.add_edge("analyze", "fact_check")
    builder.add_edge("fact_check", "generate_insights")
    builder.add_edge("generate_insights", "build_report")

    # Conditional edge: quality gate after report
    builder.add_conditional_edges(
        "build_report",
        quality_gate,
        {
            "accept": END,
            "refine": "increment_iteration",
        },
    )

    # Loop back: increment → decompose (for reflection)
    builder.add_edge("increment_iteration", "decompose")

    # Compile the graph
    graph = builder.compile()
    logger.info("Research graph compiled successfully")
    return graph


def run_research(
    query: str,
    llm: Optional[LLMClient] = None,
    tracker: Optional[ProgressTracker] = None,
    max_iterations: int = None,
) -> dict:
    """
    Execute the full research pipeline for a given query.

    This is the main entry point for running research.

    Args:
        query: The research question to investigate.
        llm: Optional shared LLM client.
        tracker: Optional progress tracker for UI updates.
        max_iterations: Override max reflection loop iterations.

    Returns:
        Final ResearchState dict with all results.
    """
    llm = llm or LLMClient()
    graph = create_research_graph(llm=llm, tracker=tracker)

    # Keep a reference to the retriever for Tavily call tracking
    # (agents are created inside create_research_graph, so we also store
    #  a reference on the llm object for convenience)
    from agents.retriever_agent import RetrieverAgent as _RA  # noqa: avoid circular at module level

    initial_state: ResearchState = {
        "original_query": query,
        "sub_queries": [],
        "sources": [],
        "analysis": {},
        "fact_check": {},
        "insights": {},
        "report": {},
        "iteration": 0,
        "max_iterations": max_iterations or settings.MAX_ITERATIONS,
        "quality_score": 0.0,
        "status": "Starting research...",
        "errors": [],
        "agent_outputs": {},
        "usage_stats": {},
    }

    logger.info(f"Starting research pipeline for: {query}")

    try:
        result = graph.invoke(initial_state)

        # Attach usage stats from the shared LLM client
        usage = llm.get_usage_summary()
        usage["tavily_calls"] = getattr(llm, "_tavily_calls", 0)
        result["usage_stats"] = usage

        logger.info(
            f"Research complete. Quality: {result.get('quality_score', 0)}/100, "
            f"Sources: {len(result.get('sources', []))}, "
            f"Iterations: {result.get('iteration', 0) + 1}, "
            f"Total tokens: {usage.get('total_tokens', 0)}"
        )
        return result

    except Exception as e:
        logger.error(f"Research pipeline failed: {e}", exc_info=True)
        initial_state["status"] = f"Pipeline error: {str(e)}"
        initial_state["errors"] = [str(e)]
        initial_state["usage_stats"] = llm.get_usage_summary()
        return initial_state
