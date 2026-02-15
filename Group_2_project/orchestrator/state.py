"""
orchestrator/state.py
======================
Shared state definition for the LangGraph research pipeline.

The ResearchState TypedDict is passed through every node in the graph.
Each agent reads what it needs and writes its results back.

WHY TypedDict:
    LangGraph requires a TypedDict (not a dataclass) for state management.
    This gives us type safety while being compatible with LangGraph's
    state merging mechanism.

STATE FLOW:
    ┌──────────────────────────────────────────────────────────────────┐
    │  START                                                          │
    │    │                                                            │
    │    ▼                                                            │
    │  decompose ── sub_queries                                       │
    │    │                                                            │
    │    ▼                                                            │
    │  retrieve ── sources[]                                          │
    │    │                                                            │
    │    ▼                                                            │
    │  analyze ── analysis                                            │
    │    │                                                            │
    │    ▼                                                            │
    │  fact_check ── fact_check_result                                │
    │    │                                                            │
    │    ▼                                                            │
    │  generate_insights ── insights                                  │
    │    │                                                            │
    │    ▼                                                            │
    │  build_report ── report (+ quality_score)                       │
    │    │                                                            │
    │    ▼                                                            │
    │  quality_gate ──→ END (if score >= threshold)                   │
    │       │                                                         │
    │       └──→ decompose (if score < threshold & iteration < max)   │
    └──────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from typing import TypedDict, Any


class ResearchState(TypedDict, total=False):
    """
    Shared state passed through the LangGraph research pipeline.

    All fields are optional (total=False) so agents only need to
    return the fields they update.
    """

    # ── Input ────────────────────────────────────────────────
    original_query: str          # The user's research question

    # ── Decomposer Output ────────────────────────────────────
    sub_queries: list[str]       # Atomic sub-queries for retrieval

    # ── Retriever Output ─────────────────────────────────────
    sources: list[dict]          # List of SourceDocument dicts

    # ── Analysis Output ──────────────────────────────────────
    analysis: dict               # AnalysisResult as dict

    # ── Fact-Checker Output ──────────────────────────────────
    fact_check: dict             # FactCheckResult as dict

    # ── Insight Output ───────────────────────────────────────
    insights: dict               # InsightResult as dict

    # ── Report Output ────────────────────────────────────────
    report: dict                 # ReportResult as dict

    # ── Orchestration Metadata ───────────────────────────────
    iteration: int               # Current reflection loop iteration
    max_iterations: int          # Max allowed iterations
    quality_score: float         # Report quality score (0-100)
    status: str                  # Pipeline status message
    errors: list[str]            # Any errors encountered
    agent_outputs: dict[str, Any]  # Raw outputs for debugging

    # ── Usage Tracking ────────────────────────────────────────
    usage_stats: dict            # Token usage & Tavily call stats
