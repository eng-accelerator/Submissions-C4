"""
Embedding model wrapper.
Uses sentence-transformers for local embeddings.
Think of this like a translator that converts human text into numbers
that a computer can compare for similarity.
"""

from __future__ import annotations
from typing import List
import numpy as np

_model = None


def _get_model():
    """Lazy-load the sentence-transformers model (heavy import)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        import config
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of texts and return an (N, dim) numpy array."""
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string and return a 1-D vector."""
    return embed_texts([query])[0]
