"""
Vector Store — Lightweight NumPy-based implementation.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No external vector DB dependency — works on any Python version.
Think of this like a smart filing cabinet that remembers every document
by its "meaning fingerprint" and can instantly find the most relevant ones.

Uses cosine similarity for ranking (same as ChromaDB/Qdrant under the hood).
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import json
import numpy as np
import config
from rag.embeddings import embed_texts, embed_query

# ── In-memory store ───────────────────────────────────────────────────
_store: Dict[str, Any] = {
    "ids": [],
    "documents": [],
    "metadatas": [],
    "embeddings": None,  # numpy array (N, dim)
}
_initialized = False


def _ensure_init():
    """Load persisted store from disk if available."""
    global _initialized
    if _initialized:
        return

    persist_path = os.path.join(config.VECTOR_DB_PATH, "store.json")
    emb_path = os.path.join(config.VECTOR_DB_PATH, "embeddings.npy")

    if os.path.exists(persist_path) and os.path.exists(emb_path):
        with open(persist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _store["ids"] = data.get("ids", [])
        _store["documents"] = data.get("documents", [])
        _store["metadatas"] = data.get("metadatas", [])
        _store["embeddings"] = np.load(emb_path)

    _initialized = True


def _persist():
    """Save store to disk for persistence across runs."""
    os.makedirs(config.VECTOR_DB_PATH, exist_ok=True)
    persist_path = os.path.join(config.VECTOR_DB_PATH, "store.json")
    emb_path = os.path.join(config.VECTOR_DB_PATH, "embeddings.npy")

    data = {
        "ids": _store["ids"],
        "documents": _store["documents"],
        "metadatas": _store["metadatas"],
    }
    with open(persist_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    if _store["embeddings"] is not None:
        np.save(emb_path, _store["embeddings"])


def reset_collection():
    """Clear the entire store."""
    global _initialized
    _store["ids"] = []
    _store["documents"] = []
    _store["metadatas"] = []
    _store["embeddings"] = None
    _initialized = True
    _persist()


def index_documents(
    documents: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> int:
    """
    Index documents into the vector store.
    Returns number of documents indexed.
    """
    _ensure_init()

    if ids is None:
        existing_count = len(_store["ids"])
        ids = [f"doc_{existing_count + i}" for i in range(len(documents))]
    if metadatas is None:
        metadatas = [{"source": "unknown"} for _ in documents]

    # Compute embeddings
    new_embeddings = embed_texts(documents)

    # Check for existing IDs (upsert behavior)
    existing_set = set(_store["ids"])
    for i, doc_id in enumerate(ids):
        if doc_id in existing_set:
            # Update existing
            idx = _store["ids"].index(doc_id)
            _store["documents"][idx] = documents[i]
            _store["metadatas"][idx] = metadatas[i]
            if _store["embeddings"] is not None:
                _store["embeddings"][idx] = new_embeddings[i]
        else:
            # Append new
            _store["ids"].append(doc_id)
            _store["documents"].append(documents[i])
            _store["metadatas"].append(metadatas[i])

            if _store["embeddings"] is None:
                _store["embeddings"] = new_embeddings[i:i+1].copy()
            else:
                _store["embeddings"] = np.vstack([_store["embeddings"], new_embeddings[i:i+1]])

    _persist()
    return len(documents)


def query_store(
    query_text: str,
    n_results: int = None,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Query the vector store using cosine similarity.
    Returns dict with keys: ids, documents, metadatas, distances, embeddings
    """
    _ensure_init()

    if n_results is None:
        n_results = config.TOP_K_RESULTS

    if _store["embeddings"] is None or len(_store["ids"]) == 0:
        return {"ids": [], "documents": [], "metadatas": [], "distances": [], "embeddings": []}

    query_embedding = embed_query(query_text)

    # Compute cosine similarity
    embeddings = _store["embeddings"]
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)  # avoid division by zero
    normalized = embeddings / norms

    q_norm = np.linalg.norm(query_embedding)
    if q_norm == 0:
        q_norm = 1e-10
    q_normalized = query_embedding / q_norm

    similarities = normalized @ q_normalized  # (N,)
    distances = 1.0 - similarities  # cosine distance

    # Apply metadata filter if provided
    mask = np.ones(len(_store["ids"]), dtype=bool)
    if where:
        for key, value in where.items():
            for i, meta in enumerate(_store["metadatas"]):
                if meta.get(key) != value:
                    mask[i] = False
        distances = np.where(mask, distances, 999.0)

    # Get top-k indices
    n = min(n_results, int(mask.sum()))
    if n == 0:
        return {"ids": [], "documents": [], "metadatas": [], "distances": [], "embeddings": []}

    top_indices = np.argsort(distances)[:n]

    return {
        "ids": [_store["ids"][i] for i in top_indices],
        "documents": [_store["documents"][i] for i in top_indices],
        "metadatas": [_store["metadatas"][i] for i in top_indices],
        "distances": [float(distances[i]) for i in top_indices],
        "embeddings": [embeddings[i].tolist() for i in top_indices],
    }


def get_collection_count() -> int:
    """Return how many documents are in the collection."""
    _ensure_init()
    return len(_store["ids"])
