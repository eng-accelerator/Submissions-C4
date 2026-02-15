"""
Fact-Checker Agent
━━━━━━━━━━━━━━━━━
Fourth agent. Like the Fraud Detection desk at a bank — double-checks
everything the Credit Analysis found. Assesses source credibility and
cross-references claims. Trust, but verify.

Responsibilities:
  • Assess source credibility
  • Cross-check key claims across sources
  • Output fact-check verdicts
"""

from __future__ import annotations
from typing import Dict, Any, List


# Source credibility tiers (like credit ratings!)
SOURCE_CREDIBILITY = {
    "arxiv": {"tier": "high", "score": 0.85, "label": "Peer-reviewed / Preprint"},
    "research_paper": {"tier": "high", "score": 0.85, "label": "Research Paper"},
    "documentation": {"tier": "high", "score": 0.80, "label": "Official Documentation"},
    "government": {"tier": "high", "score": 0.90, "label": "Government / Regulatory"},
    "web": {"tier": "medium", "score": 0.65, "label": "Web Source (Live Search)"},
    "blog": {"tier": "medium", "score": 0.60, "label": "Technical Blog"},
    "technical_blog": {"tier": "medium", "score": 0.65, "label": "Technical Blog"},
    "news": {"tier": "medium", "score": 0.55, "label": "News Article"},
    "social_media": {"tier": "low", "score": 0.30, "label": "Social Media"},
    "unknown": {"tier": "low", "score": 0.40, "label": "Unknown Source"},
}


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input context keys:
      - claims: List[dict]
      - contradictions: List[dict]
      - evidence_chains: List[dict]
      - retrieved_chunks: List[dict]

    Output added to context:
      - fact_check_results: List[dict]
      - credibility_summary: dict
    """
    claims = context.get("claims", [])
    contradictions = context.get("contradictions", [])
    evidence_chains = context.get("evidence_chains", [])
    chunks = context.get("retrieved_chunks", [])

    # ── Source credibility assessment ─────────────────────────────────
    credibility_map = _assess_sources(chunks)

    # ── Cross-check claims ────────────────────────────────────────────
    fact_check_results = _cross_check_claims(claims, chunks, credibility_map, contradictions)

    # ── Credibility summary ───────────────────────────────────────────
    credibility_summary = _summarize_credibility(credibility_map, fact_check_results)

    context["fact_check_results"] = fact_check_results
    context["credibility_summary"] = credibility_summary
    context["credibility_map"] = credibility_map

    context["fact_checker_output"] = {
        "total_checked": len(fact_check_results),
        "verified": sum(1 for r in fact_check_results if r["verdict"] == "verified"),
        "partially_verified": sum(1 for r in fact_check_results if r["verdict"] == "partially_verified"),
        "unverified": sum(1 for r in fact_check_results if r["verdict"] == "unverified"),
        "disputed": sum(1 for r in fact_check_results if r["verdict"] == "disputed"),
        "credibility_summary": credibility_summary,
        "top_results": [
            {"claim": r["claim"][:80], "verdict": r["verdict"], "credibility_score": r["credibility_score"]}
            for r in fact_check_results[:5]
        ],
    }

    return context


def _assess_sources(chunks: List[dict]) -> Dict[str, dict]:
    """Assess credibility of each source in the retrieved chunks."""
    source_cred = {}
    for chunk in chunks:
        source = chunk.get("metadata", {}).get("source", "unknown")
        doc_type = chunk.get("metadata", {}).get("doc_type", "unknown")
        chunk_id = chunk.get("id", "unknown")

        # Use the better of source or doc_type credibility
        cred_source = SOURCE_CREDIBILITY.get(source, SOURCE_CREDIBILITY["unknown"])
        cred_type = SOURCE_CREDIBILITY.get(doc_type, SOURCE_CREDIBILITY["unknown"])
        best_cred = cred_source if cred_source["score"] >= cred_type["score"] else cred_type

        source_cred[chunk_id] = {
            "source": source,
            "doc_type": doc_type,
            "tier": best_cred["tier"],
            "score": best_cred["score"],
            "label": best_cred["label"],
        }

    return source_cred


def _cross_check_claims(
    claims: List[dict],
    chunks: List[dict],
    credibility_map: Dict[str, dict],
    contradictions: List[dict],
) -> List[dict]:
    """Cross-check each claim and produce a verdict."""
    results = []
    contradicted_claims = set()

    # Build set of contradicted claims
    for c in contradictions:
        contradicted_claims.add(c.get("claim_a", "")[:80])
        contradicted_claims.add(c.get("claim_b", "")[:80])

    for claim in claims:
        source_id = claim["source_id"]
        cred = credibility_map.get(source_id, {"score": 0.4, "tier": "low"})

        # Check if this claim appears (or is supported) in multiple sources
        support_count = _count_supporting_sources(claim["claim"], chunks, source_id)

        # Determine verdict
        is_contradicted = claim["claim"][:80] in contradicted_claims

        if is_contradicted:
            verdict = "disputed"
            fact_score = max(0.2, cred["score"] * 0.5)
        elif support_count >= 2 and cred["score"] >= 0.7:
            verdict = "verified"
            fact_score = min(0.95, cred["score"] + 0.1 * support_count)
        elif support_count >= 1 or cred["score"] >= 0.6:
            verdict = "partially_verified"
            fact_score = cred["score"] * 0.8 + 0.05 * support_count
        else:
            verdict = "unverified"
            fact_score = cred["score"] * 0.5

        results.append({
            "claim": claim["claim"],
            "source_id": source_id,
            "verdict": verdict,
            "credibility_score": round(fact_score, 2),
            "source_credibility": cred["tier"],
            "supporting_sources": support_count,
            "evidence_type": claim.get("evidence_type", "unknown"),
        })

    return results


def _count_supporting_sources(claim_text: str, chunks: List[dict], exclude_id: str) -> int:
    """Count how many other chunks contain overlapping content with the claim."""
    claim_words = set(claim_text.lower().split()) - _COMMON_WORDS
    support = 0

    for chunk in chunks:
        if chunk.get("id") == exclude_id:
            continue
        chunk_words = set(chunk.get("text", "").lower().split()) - _COMMON_WORDS
        overlap = len(claim_words & chunk_words)
        if overlap >= 3:  # at least 3 meaningful words in common
            support += 1

    return support


def _summarize_credibility(credibility_map: Dict[str, dict], results: List[dict]) -> dict:
    """Produce an overall credibility summary."""
    if not credibility_map:
        return {"overall": "unknown", "score": 0.0, "breakdown": {}}

    scores = [c["score"] for c in credibility_map.values()]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    tier_counts = {}
    for c in credibility_map.values():
        tier = c["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    verdict_counts = {}
    for r in results:
        v = r["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    return {
        "overall": "high" if avg_score >= 0.7 else "medium" if avg_score >= 0.5 else "low",
        "average_score": round(avg_score, 2),
        "tier_breakdown": tier_counts,
        "verdict_breakdown": verdict_counts,
    }


_COMMON_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "this", "that", "these",
    "those", "it", "its", "they", "them", "their", "we", "our", "you",
}
