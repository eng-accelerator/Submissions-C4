"""
Critical Analysis Agent
━━━━━━━━━━━━━━━━━━━━━━━
Third agent. Like the Credit Analysis desk — scrutinizes the documents,
extracts specific claims, spots contradictions, and builds evidence chains.
Uses the LLM to extract claims that are RELEVANT to the actual research
query, not just any sentence with a percentage sign.

Responsibilities:
  • Extract claims from retrieved chunks (LLM-powered)
  • Detect potential contradictions
  • Build evidence chains linking claims to sources
"""

from __future__ import annotations
from typing import Dict, Any, List
import re
import json
import logging
import config
from llm import chat_completion, is_available as llm_available

logger = logging.getLogger(__name__)


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input context keys:
      - retrieved_chunks: List[dict]
      - query: str

    Output added to context:
      - claims, contradictions, evidence_chains
    """
    chunks = context.get("retrieved_chunks", [])
    query = context.get("query", "")

    # ── Claim extraction (LLM-first, regex fallback) ───────────────
    claims = _extract_claims(chunks, query)

    # ── Contradiction detection ────────────────────────────────────
    contradictions = _detect_contradictions(claims)

    # ── Evidence chains ────────────────────────────────────────────
    evidence_chains = _build_evidence_chains(claims, chunks)

    context["claims"] = claims
    context["contradictions"] = contradictions
    context["evidence_chains"] = evidence_chains

    context["critical_analysis_output"] = {
        "total_claims": len(claims),
        "contradictions_found": len(contradictions),
        "evidence_chains": len(evidence_chains),
        "claims_summary": [
            {"claim": c["claim"][:100], "confidence": c["confidence"], "source": c["source_id"]}
            for c in claims[:8]
        ],
        "contradiction_details": contradictions[:3],
    }

    return context


# ══════════════════════════════════════════════════════════════════════
# Claim Extraction
# ══════════════════════════════════════════════════════════════════════

def _extract_claims(chunks: List[dict], query: str) -> List[dict]:
    """
    Extract factual claims from chunks. Tries the LLM first for
    topic-relevant extraction; falls back to regex heuristics.
    """
    if llm_available() and chunks:
        llm_claims = _extract_claims_via_llm(chunks, query)
        if llm_claims:
            return llm_claims

    # Fallback: regex-based extraction
    return _extract_claims_regex(chunks)


def _extract_claims_via_llm(chunks: List[dict], query: str) -> List[dict]:
    """Use LLM to extract claims that are relevant to the research query."""
    # Build chunk text for prompt
    chunk_summaries = []
    char_count = 0
    for chunk in chunks:
        text = chunk.get("text", "")[:400]
        source_id = chunk.get("id", "unknown")
        meta = chunk.get("metadata", {})
        source_type = meta.get("source", meta.get("doc_type", "unknown"))
        block = f"[Source: {source_id} ({source_type})]\n{text}\n"
        if char_count + len(block) > 3500:
            break
        chunk_summaries.append(block)
        char_count += len(block)

    if not chunk_summaries:
        return []

    chunks_text = "\n".join(chunk_summaries)

    prompt = f"""You are a research analyst. Extract factual claims from the following source material that are relevant to the research query.

**Research Query:** {query}

**Source Material:**
{chunks_text}

For EACH claim, output a JSON array with objects like:
[
  {{
    "claim": "The factual statement",
    "source_id": "the source ID from the [Source: ...] tag",
    "confidence": 0.75,
    "evidence_type": "statistical|empirical|contradictory|inferential|descriptive"
  }}
]

Rules:
1. Extract 5-15 claims ONLY about the topic "{query}"
2. IGNORE claims about unrelated topics (e.g. if query is about invoicing, ignore claims about AI hallucinations)
3. Each claim should be a clear, specific, factual statement
4. Confidence: 0.5-0.95 based on how well-supported the claim is
5. evidence_type: "statistical" if has numbers, "empirical" if cites studies, "contradictory" if debates, "inferential" if suggests/implies, "descriptive" otherwise

Output ONLY the JSON array."""

    reply = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.2,
    )
    if not reply:
        return []

    try:
        json_match = re.search(r'\[.*\]', reply, re.DOTALL)
        if json_match:
            raw = json.loads(json_match.group())
            claims = []
            for item in raw:
                claims.append({
                    "claim": item.get("claim", ""),
                    "source_id": item.get("source_id", "unknown"),
                    "confidence": min(max(float(item.get("confidence", 0.65)), 0.5), 0.95),
                    "evidence_type": item.get("evidence_type", "descriptive"),
                })
            return claims if claims else []
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Critical analysis LLM JSON parse failed: %s", exc, exc_info=config.DEBUG)

    return []


def _extract_claims_regex(chunks: List[dict]) -> List[dict]:
    """
    Fallback: Extract factual claims using sentence-level regex heuristics.
    Looks for declarative statements with numbers, comparisons, or causal language.
    """
    claims = []
    claim_patterns = [
        r'[\d]+[\.\d]*\s*%',                                     # percentages
        r'(?:significantly|dramatically|substantially)',           # strength words
        r'(?:reduces?|increases?|improves?|outperforms?)',         # causal verbs
        r'(?:however|but|although|despite)',                      # contrast
        r'(?:shows?|demonstrates?|found|suggests?)',              # evidence verbs
        r'(?:requires?|must|shall|mandatory|obligat)',            # regulatory language
        r'(?:deadline|effective|implementation|regulation|law)',   # policy language
    ]

    for chunk in chunks:
        text = chunk.get("text", "")
        source_id = chunk.get("id", "unknown")
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            score = 0
            for pattern in claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    score += 1

            if score >= 1:
                confidence = min(0.5 + score * 0.15, 0.95)
                claims.append({
                    "claim": sentence,
                    "source_id": source_id,
                    "confidence": round(confidence, 2),
                    "evidence_type": _classify_evidence(sentence),
                })

    return claims


def _classify_evidence(sentence: str) -> str:
    """Classify the type of evidence in a claim."""
    lower = sentence.lower()
    if re.search(r'\d+[\.\d]*\s*%', lower):
        return "statistical"
    elif any(w in lower for w in ["study", "research", "paper", "benchmark"]):
        return "empirical"
    elif any(w in lower for w in ["however", "but", "although", "despite"]):
        return "contradictory"
    elif any(w in lower for w in ["suggests", "indicates", "implies"]):
        return "inferential"
    elif any(w in lower for w in ["requires", "must", "shall", "mandatory"]):
        return "regulatory"
    else:
        return "descriptive"


# ══════════════════════════════════════════════════════════════════════
# Contradiction Detection
# ══════════════════════════════════════════════════════════════════════

def _detect_contradictions(claims: List[dict]) -> List[dict]:
    """
    Detect potential contradictions by finding claims that discuss
    similar topics but have opposing sentiment/direction.
    """
    contradictions = []

    for i, claim_a in enumerate(claims):
        for j, claim_b in enumerate(claims):
            if j <= i:
                continue
            if claim_a["source_id"] == claim_b["source_id"]:
                continue

            text_a = claim_a["claim"].lower()
            text_b = claim_b["claim"].lower()

            opposing_pairs = [
                ("increase", "decrease"), ("improve", "worsen"),
                ("reduce", "increase"), ("better", "worse"),
                ("higher", "lower"), ("more", "less"),
                ("can", "cannot"), ("effective", "ineffective"),
                ("mandatory", "optional"), ("required", "voluntary"),
            ]

            for word_a, word_b in opposing_pairs:
                if ((word_a in text_a and word_b in text_b) or
                        (word_b in text_a and word_a in text_b)):
                    words_a = set(text_a.split()) - _STOP_WORDS
                    words_b = set(text_b.split()) - _STOP_WORDS
                    overlap = words_a & words_b
                    if len(overlap) >= 2:
                        contradictions.append({
                            "claim_a": claim_a["claim"][:120],
                            "claim_b": claim_b["claim"][:120],
                            "source_a": claim_a["source_id"],
                            "source_b": claim_b["source_id"],
                            "opposing_terms": (word_a, word_b),
                            "shared_topics": list(overlap)[:5],
                        })
                        break

    return contradictions


# ══════════════════════════════════════════════════════════════════════
# Evidence Chains
# ══════════════════════════════════════════════════════════════════════

def _build_evidence_chains(claims: List[dict], chunks: List[dict]) -> List[dict]:
    """Build evidence chains linking claims back to source chunks."""
    chains = []
    for claim in claims[:12]:
        chain = {
            "claim": claim["claim"][:150],
            "confidence": claim["confidence"],
            "evidence_type": claim["evidence_type"],
            "source_id": claim["source_id"],
            "source_metadata": {},
            "strength": _assess_strength(claim),
        }

        for chunk in chunks:
            if chunk.get("id") == claim["source_id"]:
                chain["source_metadata"] = chunk.get("metadata", {})
                break

        chains.append(chain)

    return chains


def _assess_strength(claim: dict) -> str:
    """Assess the overall strength of a claim's evidence."""
    conf = claim["confidence"]
    if conf >= 0.8:
        return "strong"
    elif conf >= 0.6:
        return "moderate"
    else:
        return "weak"


_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "this", "that", "these",
    "those", "it", "its", "they", "them", "their", "we", "our", "you",
    "your", "he", "she", "his", "her", "as", "if", "not", "no", "so",
    "than", "too", "very", "just", "about", "also", "more", "some",
    "such", "only", "other", "into", "over", "after", "then",
}
