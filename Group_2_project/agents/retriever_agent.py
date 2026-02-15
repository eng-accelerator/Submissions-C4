"""
agents/retriever_agent.py
==========================
Agent 1: Retriever Agent

RESPONSIBILITY:
    Given sub-queries from the decomposer, search the web using the Tavily API
    and collect high-quality sources. Handles deduplication and source diversity.

INPUT (from state):
    sub_queries: List[str] — Focused sub-queries from the decomposer.

OUTPUT (to state):
    sources: List[dict] — Deduplicated SourceDocument dicts.

FEATURES:
    - Parallel-like search across multiple sub-queries
    - URL-based deduplication
    - Source type categorization via LLM
    - Graceful fallback if Tavily fails
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

from tavily import TavilyClient

from utils.llm_client import LLMClient
from prompts.retriever_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class SourceDocument:
    """
    A single web source collected by the Retriever Agent.

    Attributes:
        title: The page title.
        url: The full URL.
        content: Extracted text content (truncated).
        source_type: Category: 'news', 'academic', 'blog', 'government', etc.
        relevance_score: Tavily's relevance score (0.0-1.0).
        domain: The domain name (e.g., 'bbc.com').
        sub_query: Which sub-query produced this result.
    """
    title: str
    url: str
    content: str
    source_type: str = "other"
    relevance_score: float = 0.0
    domain: str = ""
    sub_query: str = ""


class RetrieverAgent:
    """
    Searches the web via Tavily and collects research sources.

    Handles multiple sub-queries, deduplicates results by URL,
    and categorizes source types using the LLM.
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()
        self.tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
        self.tavily_calls: int = 0  # Track number of Tavily API calls

    def run(self, state: dict) -> dict:
        """
        LangGraph node function: retrieve sources for all sub-queries.

        Args:
            state: Current ResearchState dict.

        Returns:
            State update with sources list.
        """
        sub_queries = state.get("sub_queries", [])
        existing_urls = {s["url"] for s in state.get("sources", [])}
        all_sources: list[SourceDocument] = []

        for i, query in enumerate(sub_queries):
            logger.info(f"Searching sub-query {i+1}/{len(sub_queries)}: {query}")
            try:
                results = self._search(query)
                for src in results:
                    if src.url not in existing_urls:
                        existing_urls.add(src.url)
                        all_sources.append(src)
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                continue

        # Categorize sources using LLM
        if all_sources:
            all_sources = self._categorize_sources(all_sources)

        logger.info(f"Retrieved {len(all_sources)} unique sources total")

        # Combine with existing sources from previous iterations
        existing_sources = state.get("sources", [])
        new_sources_dicts = [asdict(s) for s in all_sources]

        return {
            "sources": existing_sources + new_sources_dicts,
            "status": f"Retrieved {len(all_sources)} new sources ({len(existing_sources) + len(all_sources)} total)",
        }

    def _search(self, query: str) -> list[SourceDocument]:
        """
        Execute a single Tavily search and convert results to SourceDocuments.

        Args:
            query: The search query string.

        Returns:
            List of SourceDocument objects.
        """
        self.tavily_calls += 1
        response = self.tavily.search(
            query=query,
            max_results=settings.MAX_SEARCH_RESULTS,
            include_answer=False,
            search_depth="advanced",
        )

        sources = []
        for result in response.get("results", []):
            domain = urlparse(result.get("url", "")).netloc.replace("www.", "")
            content = result.get("content", "")

            # Truncate very long content to ~800 words
            words = content.split()
            if len(words) > 800:
                content = " ".join(words[:800]) + "..."

            sources.append(SourceDocument(
                title=result.get("title", "Untitled"),
                url=result.get("url", ""),
                content=content,
                relevance_score=result.get("score", 0.0),
                domain=domain,
                sub_query=query,
            ))

        return sources

    def _categorize_sources(self, sources: list[SourceDocument]) -> list[SourceDocument]:
        """
        Use LLM to categorize source types and domain authority.

        Args:
            sources: List of uncategorized SourceDocuments.

        Returns:
            Same list with source_type updated.
        """
        sources_text = "\n".join(
            f"[{i}] Domain: {s.domain} | Title: {s.title} | URL: {s.url}"
            for i, s in enumerate(sources)
        )

        try:
            user_prompt = USER_PROMPT_TEMPLATE.format(
                count=len(sources),
                sources_text=sources_text,
            )
            result = self.llm.chat_json(SYSTEM_PROMPT, user_prompt)

            for item in result.get("sources", []):
                idx = item.get("index", -1)
                if 0 <= idx < len(sources):
                    sources[idx].source_type = item.get("source_type", "other")

        except Exception as e:
            logger.warning(f"Source categorization failed: {e}. Using defaults.")
            # Fallback: simple domain-based categorization
            for s in sources:
                s.source_type = self._fallback_categorize(s.domain)

        return sources

    @staticmethod
    def _fallback_categorize(domain: str) -> str:
        """Simple rule-based source categorization as fallback."""
        domain = domain.lower()
        if any(x in domain for x in [".edu", "arxiv", "scholar", "pubmed", "ncbi"]):
            return "academic"
        if any(x in domain for x in [".gov", "government"]):
            return "government"
        if any(x in domain for x in ["reuters", "bbc", "nytimes", "cnn", "guardian", "apnews"]):
            return "news"
        if any(x in domain for x in ["wikipedia", "britannica"]):
            return "encyclopedia"
        if any(x in domain for x in ["medium.com", "substack", "wordpress", "blogspot"]):
            return "blog"
        return "other"
