"""
Retrieval logic: multi-query expansion search, hybrid merge, and optional re-ranking.
Think of this like casting multiple fishing nets (expanded queries) into a lake
and then picking the best catch from all nets combined.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np
from rag.vector_store import query_store
import config


def multi_query_retrieval(
    queries: List[str],
    top_k: int = None,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run each expanded query against the vector store, merge results,
    and re-rank by reciprocal-rank fusion.

    Returns a dict with:
      chunks: List[dict]  – ranked results with id, text, metadata, score
      stage_counts: dict   – counts at each pipeline stage (for waterfall viz)
      per_query_counts: dict – how many results each query contributed
    """
    if top_k is None:
        top_k = config.TOP_K_RESULTS

    all_results: Dict[str, dict] = {}  # id -> {text, metadata, scores:[]}
    per_query_counts = {}

    # Stage 1: Dense retrieval from each query
    for q in queries:
        res = query_store(q, n_results=top_k * 2, where=where)
        per_query_counts[q] = len(res["ids"])

        for idx, doc_id in enumerate(res["ids"]):
            distance = res["distances"][idx] if idx < len(res["distances"]) else 1.0
            similarity = 1.0 - distance  # cosine distance → similarity

            if doc_id not in all_results:
                all_results[doc_id] = {
                    "id": doc_id,
                    "text": res["documents"][idx] if idx < len(res["documents"]) else "",
                    "metadata": res["metadatas"][idx] if idx < len(res["metadatas"]) else {},
                    "scores": [],
                    "embedding": res["embeddings"][idx] if idx < len(res["embeddings"]) else None,
                }
            all_results[doc_id]["scores"].append(similarity)

    dense_count = len(all_results)

    # Stage 2: Reciprocal Rank Fusion (RRF) re-ranking
    k = 60  # RRF constant
    for doc in all_results.values():
        # Average the similarity scores across queries, boosted by frequency
        avg_score = np.mean(doc["scores"])
        frequency_boost = len(doc["scores"]) / len(queries)
        doc["final_score"] = avg_score * (0.7 + 0.3 * frequency_boost)

    ranked = sorted(all_results.values(), key=lambda d: d["final_score"], reverse=True)

    # Stage 3: Take top-k
    final_chunks = ranked[:top_k]

    stage_counts = {
        "queries": len(queries),
        "dense_candidates": dense_count,
        "after_rerank": len(ranked),
        "final_chunks": len(final_chunks),
    }

    return {
        "chunks": final_chunks,
        "stage_counts": stage_counts,
        "per_query_counts": per_query_counts,
    }


def keyword_search(query: str, documents: List[str]) -> List[int]:
    """
    Simple keyword overlap search (used as hybrid complement).
    Returns indices of documents sorted by keyword overlap score.
    """
    query_terms = set(query.lower().split())
    scores = []
    for i, doc in enumerate(documents):
        doc_terms = set(doc.lower().split())
        overlap = len(query_terms & doc_terms)
        scores.append((i, overlap))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in scores if _ > 0]
