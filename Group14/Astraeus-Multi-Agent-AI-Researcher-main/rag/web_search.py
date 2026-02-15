"""
Tavily Web Search Client
━━━━━━━━━━━━━━━━━━━━━━━
Fetches real web results with URLs, titles, and snippets.
Think of it like sending a research assistant to the internet library
while your other assistant searches the local filing cabinet (vector DB).
Two sources of evidence are always better than one — just like in banking
audits, you cross-reference internal records with external reports.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
import config

_client = None
logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Return True if Tavily API key is configured."""
    return bool(config.TAVILY_API_KEY and config.TAVILY_API_KEY.strip())


def _get_client():
    """Lazy-init Tavily client."""
    global _client
    if _client is None:
        from tavily import TavilyClient
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> List[Dict[str, Any]]:
    """
    Search the web via Tavily and return structured results.

    Returns list of dicts, each with:
      - title: str
      - url: str
      - snippet: str  (content excerpt)
      - score: float  (relevance 0-1)
      - source: "web"
    """
    if not is_available():
        return []

    try:
        client = _get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=False,
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:500],
                "score": item.get("score", 0.0),
                "source": "web",
            })

        return results

    except Exception as exc:
        logger.warning("Tavily web_search failed for query '%s': %s", query, exc, exc_info=config.DEBUG)
        return []


def multi_query_web_search(
    queries: List[str],
    max_results_per_query: int = 3,
) -> List[Dict[str, Any]]:
    """
    Run web search for multiple query variants, deduplicate by URL.
    Returns a merged, deduplicated list of web results.
    """
    if not is_available():
        return []

    seen_urls = set()
    all_results = []

    for q in queries:
        results = web_search(q, max_results=max_results_per_query)
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    # Sort by relevance score descending
    all_results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return all_results
