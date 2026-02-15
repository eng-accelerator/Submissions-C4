"""
Insight Generator Agent
━━━━━━━━━━━━━━━━━━━━━━━
Fifth agent. Like the Risk Assessment desk — looks at the big picture,
clusters findings into themes, spots gaps in the evidence, and generates
hypotheses. Uses the LLM to produce analysis relevant to the ACTUAL
query topic, not a hardcoded set of AI keywords.

Responsibilities:
  • Cluster findings into themes (LLM-driven)
  • Identify knowledge gaps (LLM-driven)
  • Generate hypotheses / key insights (LLM-driven)
"""

from __future__ import annotations
from typing import Dict, Any, List
import re
import json
import logging
import config
from collections import Counter
from llm import chat_completion, is_available as llm_available

logger = logging.getLogger(__name__)


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input context keys:
      - claims: List[dict]
      - fact_check_results: List[dict]
      - retrieved_chunks: List[dict]
      - web_results: List[dict]
      - query: str

    Output added to context:
      - themes, gaps, hypotheses, key_insights
    """
    claims = context.get("claims", [])
    fact_results = context.get("fact_check_results", [])
    chunks = context.get("retrieved_chunks", [])
    web_results = context.get("web_results", [])
    query = context.get("query", "")

    # Build source text for LLM
    source_text = _gather_source_text(chunks, web_results)

    # ── LLM-powered analysis ──────────────────────────────────────────
    if llm_available() and source_text.strip():
        themes = _llm_themes(query, source_text, claims)
        gaps = _llm_gaps(query, source_text, claims, fact_results)
        hypotheses = _llm_hypotheses(query, source_text, claims)
        key_insights = _llm_key_insights(query, source_text, claims, fact_results)
    else:
        # Fallback: basic stats-only analysis
        themes = _fallback_themes(claims)
        gaps = _fallback_gaps(claims, fact_results)
        hypotheses = _fallback_hypotheses(claims)
        key_insights = _fallback_key_insights(claims, fact_results)

    context["themes"] = themes
    context["gaps"] = gaps
    context["hypotheses"] = hypotheses
    context["key_insights"] = key_insights

    context["insight_generator_output"] = {
        "themes_found": len(themes),
        "gaps_identified": len(gaps),
        "hypotheses_generated": len(hypotheses),
        "key_insights": key_insights[:5],
        "themes_summary": [
            {"name": t["name"], "claim_count": t.get("claim_count", 0), "strength": t.get("strength", "emerging")}
            for t in themes
        ],
        "gaps_list": gaps,
    }

    return context


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════

def _gather_source_text(chunks: List[dict], web_results: List[dict], max_chars: int = 3000) -> str:
    """Collect source material for the LLM."""
    parts = []
    char_count = 0
    for w in web_results:
        block = f"[Web] {w.get('title', '')}: {w.get('snippet', '')}"
        if char_count + len(block) > max_chars:
            break
        parts.append(block)
        char_count += len(block)
    for c in chunks:
        block = f"[Doc] {c.get('text', '')[:300]}"
        if char_count + len(block) > max_chars:
            break
        parts.append(block)
        char_count += len(block)
    return "\n".join(parts)


def _claims_text(claims: List[dict], limit: int = 10) -> str:
    """Format top claims as text for the LLM."""
    lines = []
    for c in claims[:limit]:
        lines.append(f"- [{c.get('source_id', '?')}] {c['claim'][:150]}")
    return "\n".join(lines) if lines else "(no claims extracted)"


# ══════════════════════════════════════════════════════════════════════
# LLM-powered functions
# ══════════════════════════════════════════════════════════════════════

def _llm_themes(query: str, source_text: str, claims: List[dict]) -> List[dict]:
    """Use LLM to identify thematic clusters relevant to the actual query."""
    prompt = f"""You are a research analyst. Given the following source material about "{query}", identify 3-5 key thematic areas.

**Source Material:**
{source_text}

**Extracted Claims:**
{_claims_text(claims)}

For each theme, output a JSON array like:
[
  {{"name": "Theme Name", "description": "One sentence description", "strength": "strong"}},
  ...
]

Use "strong" if well-supported, "moderate" if partially supported, "emerging" if early evidence only.
Focus ONLY on themes related to "{query}". Output ONLY the JSON array, nothing else."""

    reply = chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=600, temperature=0.3)
    if not reply:
        return _fallback_themes(claims)

    try:
        # Extract JSON from reply
        json_match = re.search(r'\[.*\]', reply, re.DOTALL)
        if json_match:
            themes_raw = json.loads(json_match.group())
            themes = []
            for t in themes_raw:
                themes.append({
                    "name": t.get("name", "Unknown"),
                    "description": t.get("description", ""),
                    "strength": t.get("strength", "moderate"),
                    "claims": [],  # no claim-level mapping needed for LLM themes
                    "claim_count": 0,
                    "avg_confidence": 0.0,
                })
            return themes
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Insight generator theme parse failed: %s", exc, exc_info=config.DEBUG)

    return _fallback_themes(claims)


def _llm_gaps(query: str, source_text: str, claims: List[dict], fact_results: List[dict]) -> List[str]:
    """Use LLM to identify knowledge gaps specific to the query topic."""
    unverified = sum(1 for r in fact_results if r.get("verdict") in ("unverified", "disputed"))

    prompt = f"""You are a research analyst assessing evidence gaps. Given source material about "{query}":

**Source Material (summary):**
{source_text[:2000]}

**Stats:** {len(claims)} claims extracted, {unverified} unverified/disputed.

List 3-5 specific knowledge gaps or areas where the evidence is weak or missing for this topic.
Output one gap per line, no numbering. Focus on "{query}" specifically."""

    reply = chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=400, temperature=0.3)
    if not reply:
        return _fallback_gaps(claims, fact_results)

    lines = [line.strip() for line in reply.strip().split("\n") if line.strip()]
    gaps = []
    for line in lines:
        line = re.sub(r"^[\d]+[\.\)]\s*", "", line).strip()
        line = re.sub(r"^[-*•]\s*", "", line).strip()
        if line and len(line) > 10:
            gaps.append(line)
    return gaps[:5] if gaps else _fallback_gaps(claims, fact_results)


def _llm_hypotheses(query: str, source_text: str, claims: List[dict]) -> List[str]:
    """Use LLM to generate research hypotheses specific to the query topic."""
    prompt = f"""You are a research analyst. Based on evidence about "{query}":

**Source Material:**
{source_text[:2000]}

Generate 3 research hypotheses or forward-looking predictions related to "{query}".
Each should be a single sentence that a researcher could investigate further.
Output one hypothesis per line, no numbering. Be specific to the topic."""

    reply = chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=400, temperature=0.4)
    if not reply:
        return _fallback_hypotheses(claims)

    lines = [line.strip() for line in reply.strip().split("\n") if line.strip()]
    hypos = []
    for line in lines:
        line = re.sub(r"^[\d]+[\.\)]\s*", "", line).strip()
        line = re.sub(r"^[-*•]\s*", "", line).strip()
        if line and len(line) > 10:
            hypos.append(line)
    return hypos[:4] if hypos else _fallback_hypotheses(claims)


def _llm_key_insights(query: str, source_text: str, claims: List[dict], fact_results: List[dict]) -> List[str]:
    """Use LLM to generate key insights specific to the query topic."""
    verified = sum(1 for r in fact_results if r.get("verdict") in ("verified", "partially_verified"))

    prompt = f"""Based on research about "{query}":

**Source Material:**
{source_text[:2000]}

**Stats:** {len(claims)} claims, {verified} verified.

List 4-5 key takeaways that a decision-maker would find most valuable about "{query}".
One insight per line, no numbering. Be specific and actionable."""

    reply = chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=500, temperature=0.3)
    if not reply:
        return _fallback_key_insights(claims, fact_results)

    lines = [line.strip() for line in reply.strip().split("\n") if line.strip()]
    insights = []
    for line in lines:
        line = re.sub(r"^[\d]+[\.\)]\s*", "", line).strip()
        line = re.sub(r"^[-*•]\s*", "", line).strip()
        if line and len(line) > 10:
            insights.append(line)
    return insights[:5] if insights else _fallback_key_insights(claims, fact_results)


# ══════════════════════════════════════════════════════════════════════
# Fallback (no LLM) — basic stats-based analysis
# ══════════════════════════════════════════════════════════════════════

def _fallback_themes(claims: List[dict]) -> List[dict]:
    """Group claims by source as a simple fallback."""
    by_source = {}
    for c in claims:
        src = c.get("source_id", "unknown")
        by_source.setdefault(src, []).append(c)

    themes = []
    for src, src_claims in sorted(by_source.items(), key=lambda x: -len(x[1])):
        if src_claims:
            avg_conf = sum(c["confidence"] for c in src_claims) / len(src_claims)
            themes.append({
                "name": f"Source: {src}",
                "claims": src_claims,
                "claim_count": len(src_claims),
                "avg_confidence": round(avg_conf, 2),
                "strength": "strong" if len(src_claims) >= 3 else "moderate" if len(src_claims) >= 2 else "emerging",
            })
    return themes[:5]


def _fallback_gaps(claims: List[dict], fact_results: List[dict]) -> List[str]:
    gaps = []
    unverified = [r for r in fact_results if r.get("verdict") in ("unverified", "disputed")]
    if unverified:
        gaps.append(f"{len(unverified)} claim(s) could not be fully verified.")
    if not claims:
        gaps.append("No claims could be extracted — try a more specific query.")
    if not gaps:
        gaps.append("No significant evidence gaps detected.")
    return gaps


def _fallback_hypotheses(claims: List[dict]) -> List[str]:
    if not claims:
        return ["More evidence is needed to form hypotheses on this topic."]
    return ["The available evidence suggests further investigation would be valuable."]


def _fallback_key_insights(claims: List[dict], fact_results: List[dict]) -> List[str]:
    insights = []
    total = len(fact_results)
    if total > 0:
        verified = sum(1 for r in fact_results if r.get("verdict") in ("verified", "partially_verified"))
        pct = round(100 * verified / total)
        insights.append(f"{pct}% of {total} claims are at least partially verified.")
    evidence_types = Counter(c.get("evidence_type", "unknown") for c in claims)
    if evidence_types:
        most_common = evidence_types.most_common(1)[0]
        insights.append(f"Most common evidence type: '{most_common[0]}' ({most_common[1]} instances).")
    return insights if insights else ["Insufficient evidence to generate insights."]
