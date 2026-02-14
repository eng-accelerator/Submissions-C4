"""
agents/retriever_agent.py
=========================
Agent 1: RetrieverAgent

RESPONSIBILITY:
    Given a user's research query, search the web using the Tavily API
    and collect 5–8 high-quality sources. This is the "eyes" of the system —
    it brings in raw information from the real world.

INPUT:
    user_query: str — The research question from the user.

OUTPUT:
    List[SourceDocument] — Each source has: title, url, content, source_type.

IMPLEMENTATION STATUS: Built in Step 4.
"""

# Implementation coming in Step 4.
# Placeholder so the module can be imported without errors.

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SourceDocument:
    """
    A single web source collected by the RetrieverAgent.

    Attributes:
        title: The page title.
        url: The full URL.
        content: Extracted text content (truncated to ~500 words).
        source_type: Category like 'news', 'blog', 'academic', 'official'.
        relevance_score: Tavily's relevance score (0.0–1.0).
    """
    title: str
    url: str
    content: str
    source_type: str
    relevance_score: float = 0.0


class RetrieverAgent:
    """
    Searches the web and collects sources for a given research query.

    WILL BE IMPLEMENTED in Step 4.
    """
    pass


if __name__ == "__main__":
    # Quick standalone test — will be filled in during Step 4
    print("RetrieverAgent — implementation coming in Step 4")
