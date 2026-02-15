"""
Research Coordinator Agent
━━━━━━━━━━━━━━━━━━━━━━━━━
First agent in the pipeline. Like a bank's Loan Officer who receives the
application and figures out exactly what information is needed before
passing it to the next desk.

Responsibilities:
  • Analyze the user query
  • Expand into multiple search queries (multi-query RAG)
  • Decide routing hints for the Retriever
"""

from __future__ import annotations
from typing import Dict, Any, List
import re
import config
from llm import chat_completion, is_available


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input context keys:
      - query: str  (the user's original research query)

    Output added to context:
      - expanded_queries: List[str]
      - query_analysis: dict  (topic, intent, complexity)
      - routing_hint: str
    """
    query = context.get("query", "")

    # ── Query analysis ────────────────────────────────────────────────
    query_analysis = _analyze_query(query)

    # ── Query expansion ───────────────────────────────────────────────
    expanded_queries = _expand_query(query, config.MAX_QUERY_EXPANSIONS)

    # ── Routing (single vector DB for v1) ─────────────────────────────
    routing_hint = "vector_store"  # only option in v1

    context["expanded_queries"] = expanded_queries
    context["query_analysis"] = query_analysis
    context["routing_hint"] = routing_hint
    context["coordinator_output"] = {
        "original_query": query,
        "expanded_queries": expanded_queries,
        "analysis": query_analysis,
        "routing": routing_hint,
    }

    return context


def _analyze_query(query: str) -> Dict[str, Any]:
    """Simple rule-based query analysis (no LLM needed for v1)."""
    words = query.lower().split()
    word_count = len(words)

    # Detect intent
    if any(w in words for w in ["how", "why", "explain", "describe"]):
        intent = "explanatory"
    elif any(w in words for w in ["compare", "difference", "versus", "vs"]):
        intent = "comparative"
    elif any(w in words for w in ["what", "define", "definition"]):
        intent = "definitional"
    elif any(w in words for w in ["list", "examples", "types"]):
        intent = "enumerative"
    else:
        intent = "exploratory"

    # Estimate complexity
    if word_count <= 5:
        complexity = "simple"
    elif word_count <= 15:
        complexity = "moderate"
    else:
        complexity = "complex"

    # Extract key topics (simple: take nouns-ish words > 3 chars)
    stop_words = {"the", "and", "for", "are", "but", "not", "you", "all",
                  "can", "had", "her", "was", "one", "our", "out", "has",
                  "how", "what", "when", "where", "which", "who", "why",
                  "this", "that", "with", "from", "they", "been", "have",
                  "does", "will", "would", "could", "should", "about"}
    topics = [w for w in words if len(w) > 3 and w not in stop_words]

    return {
        "intent": intent,
        "complexity": complexity,
        "topics": topics[:5],
        "word_count": word_count,
    }


def _expand_query(query: str, n_expansions: int) -> List[str]:
    """
    Generate query variants for multi-query retrieval.
    Uses OpenRouter LLM when available; otherwise template-based expansion.
    """
    # Try OpenRouter first
    if is_available():
        llm_queries = _expand_query_via_llm(query, n_expansions)
        if llm_queries:
            return llm_queries

    # Fallback: template-based expansion
    expansions = [query]  # always include original
    templates = [
        "What is {topic} and how does it work?",
        "{topic} key concepts and techniques",
        "Recent research and developments in {topic}",
        "Advantages and challenges of {topic}",
        "Practical applications of {topic}",
    ]
    topic = _extract_topic(query)
    for template in templates[:n_expansions - 1]:
        expansion = template.format(topic=topic)
        if expansion != query:
            expansions.append(expansion)
    return expansions[:n_expansions]


def _expand_query_via_llm(query: str, n_expansions: int) -> List[str]:
    """Use OpenRouter to generate alternative search queries."""
    prompt = f"""You are a research query expander. Given the following research question, output exactly {n_expansions} alternative phrasings that would help retrieve relevant documents from a search engine. Each line must be one short search query (no numbering, no bullets). Include the original question as the first line.

Original question: {query}

Alternative search queries (one per line):"""

    reply = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4,
    )
    if not reply:
        return []

    # Parse: one query per line, strip numbering like "1." or "-"
    lines = [line.strip() for line in reply.strip().split("\n") if line.strip()]
    queries = []
    for line in lines:
        line = re.sub(r"^[\d]+[\.\)]\s*", "", line).strip()
        line = re.sub(r"^[-*]\s*", "", line).strip()
        if line and line not in queries:
            queries.append(line)
    if not queries:
        return []
    return queries[:n_expansions]


def _extract_topic(query: str) -> str:
    """Extract the core topic from a query by stripping question words."""
    prefixes = [
        "how does ", "how do ", "how is ", "how are ", "how to ",
        "what is ", "what are ", "what does ", "what do ",
        "why does ", "why do ", "why is ", "why are ",
        "explain ", "describe ", "tell me about ",
        "compare ", "define ",
    ]
    lower = query.lower().strip().rstrip("?").rstrip(".")
    for prefix in prefixes:
        if lower.startswith(prefix):
            return lower[len(prefix):]
    return lower
