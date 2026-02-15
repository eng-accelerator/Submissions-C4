"""
agents/decomposer_agent.py
============================
Agent 0: Query Decomposer

RESPONSIBILITY:
    Break a complex research query into 2-5 focused, atomic sub-queries
    for multi-hop retrieval. This dramatically improves research coverage
    by ensuring different angles of the topic are explored.

INPUT (from state):
    original_query: str — The user's research question.
    iteration: int — Current loop iteration (affects decomposition strategy).

OUTPUT (to state):
    sub_queries: List[str] — Atomic sub-queries for the retriever.

EXAMPLE:
    Input:  "Impact of AI on healthcare costs vs education spending in 2024"
    Output: [
        "AI impact on healthcare costs 2024 statistics",
        "AI spending in education sector 2024",
        "comparison healthcare vs education AI investment",
        "critical analysis AI healthcare cost reduction evidence"
    ]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from utils.llm_client import LLMClient
from prompts.decomposer_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class DecompositionResult:
    """Result of query decomposition."""
    original_query: str
    sub_queries: list[str]
    is_complex: bool
    reasoning: str


class DecomposerAgent:
    """
    Decomposes complex research queries into atomic sub-queries.

    Uses chain-of-thought prompting to analyze the query structure
    and generate focused sub-queries that cover different angles.
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()

    def run(self, state: dict) -> dict:
        """
        LangGraph node function: decompose the research query.

        Args:
            state: Current ResearchState dict.

        Returns:
            State update with sub_queries.
        """
        query = state.get("original_query", "")
        iteration = state.get("iteration", 0)
        previous_gaps = ""

        # On reflection loops, include gaps from previous report
        if iteration > 0 and state.get("report"):
            follow_ups = state["report"].get("follow_up_queries", [])
            if follow_ups:
                previous_gaps = (
                    "PREVIOUS ITERATION IDENTIFIED THESE GAPS — "
                    "focus sub-queries on filling them:\n"
                    + "\n".join(f"- {q}" for q in follow_ups)
                )
                logger.info(f"Reflection loop {iteration}: targeting {len(follow_ups)} gaps")

        context = previous_gaps or "This is the first research pass."

        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            context=context,
        )

        try:
            result = self.llm.chat_json(SYSTEM_PROMPT, user_prompt)
            sub_queries = result.get("sub_queries", [query])

            # Enforce limits
            max_q = settings.MAX_SUB_QUERIES
            if len(sub_queries) > max_q:
                sub_queries = sub_queries[:max_q]
            if not sub_queries:
                sub_queries = [query]

            logger.info(f"Decomposed into {len(sub_queries)} sub-queries: {sub_queries}")

            return {
                "sub_queries": sub_queries,
                "status": f"Decomposed into {len(sub_queries)} sub-queries",
            }

        except Exception as e:
            logger.error(f"Decomposition failed: {e}. Using original query.")
            return {
                "sub_queries": [query],
                "status": f"Decomposition fallback: {str(e)[:100]}",
                "errors": state.get("errors", []) + [f"Decomposer: {str(e)}"],
            }
