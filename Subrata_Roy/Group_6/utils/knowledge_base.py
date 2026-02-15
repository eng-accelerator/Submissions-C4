"""
Remediation knowledge base with vector store for RAG.
Stores runbooks and supports semantic search for incident-to-fix matching.
Uses ChromaDB when available; falls back to in-memory store if ChromaDB fails (e.g. Pydantic config error).
"""

import uuid
from typing import Any, Dict, List, Optional

from config import CHROMA_PERSIST_DIR
from config import OPENAI_API_KEY

COLLECTION_NAME = "remediation_runbooks"

# Lazy ChromaDB import to avoid ConfigError at module load (chroma_server_nofile / Pydantic)
_chromadb = None
_embedding_functions = None


def _import_chromadb():
    """Import chromadb and embedding_functions; return (chromadb, embedding_functions) or (None, None) on error."""
    global _chromadb, _embedding_functions
    if _chromadb is not None:
        return _chromadb, _embedding_functions
    try:
        import chromadb
        from chromadb import utils as chroma_utils
        _chromadb = chromadb
        _embedding_functions = getattr(chroma_utils, "embedding_functions", None)
        return _chromadb, _embedding_functions
    except Exception as e:
        # ChromaDB can raise pydantic.v1.errors.ConfigError (e.g. chroma_server_nofile) on import
        _chromadb = None
        _embedding_functions = None
        return None, None


def _get_embedding_function():
    """OpenAI-compatible embedding function for ChromaDB. Only used when ChromaDB is available."""
    chroma, ef_module = _import_chromadb()
    if not ef_module:
        return None
    if OPENAI_API_KEY:
        return ef_module.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name="text-embedding-3-small",
        )
    try:
        return ef_module.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    except Exception:
        pass
    return _FallbackEmbeddingFunction()


class _FallbackEmbeddingFunction:
    """Minimal embedding: fixed-size vector from text hash. For dev when no API/local model."""

    def __call__(self, input: List[str]) -> List[List[float]]:
        import hashlib
        dim = 384
        out = []
        for text in input:
            h = hashlib.sha256((text or "").encode()).digest()
            vec = [((b - 128) / 128.0) for b in h[:dim]] if len(h) >= dim else [0.0] * dim
            if len(vec) < dim:
                vec.extend([0.0] * (dim - len(vec)))
            out.append(vec[:dim])
        return out


class _InMemoryRemediationKB:
    """
    In-memory runbook store used when ChromaDB fails to load (e.g. Pydantic ConfigError).
    Search is keyword-based; no embeddings.
    """

    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = COLLECTION_NAME):
        self._store: List[Dict[str, Any]] = []
        self.persist_directory = str(persist_directory or CHROMA_PERSIST_DIR)
        self.collection_name = collection_name

    def add_runbook(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        runbook_id: Optional[str] = None,
    ) -> str:
        doc_id = runbook_id or str(uuid.uuid4())
        meta = {k: v for k, v in (metadata or {}).items() if v is not None and isinstance(v, (str, int, float, bool))}
        self._store.append({"id": doc_id, "content": content, "metadata": meta})
        return doc_id

    def search_remediation(
        self,
        issue_description: str,
        category: Optional[str] = None,
        k: int = 5,
        n_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        n = n_results or k
        words = set((issue_description or "").lower().split())
        scored = []
        for item in self._store:
            if category and item["metadata"].get("category") != category:
                continue
            text = (item["content"] or "") + " " + " ".join(str(v) for v in item["metadata"].values())
            text_lower = text.lower()
            score = sum(1 for w in words if len(w) > 2 and w in text_lower)
            scored.append((score, item))
        scored.sort(key=lambda x: -x[0])
        return [
            {"id": s[1]["id"], "content": s[1]["content"], "metadata": s[1]["metadata"], "distance": None}
            for s in scored[:n]
        ]

    def update_success_rate(self, runbook_id: str, success: bool) -> None:
        for item in self._store:
            if item["id"] == runbook_id:
                rate = item["metadata"].get("success_rate")
                new_rate = (float(rate) + (1.0 if success else 0.0)) / 2.0 if rate is not None else (1.0 if success else 0.0)
                item["metadata"]["success_rate"] = round(new_rate, 2)
                break

    def get_by_id(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        for item in self._store:
            if item["id"] == runbook_id:
                return {"id": item["id"], "content": item["content"], "metadata": item["metadata"]}
        return None


class RemediationKB:
    """
    Vector-backed knowledge base for runbooks and remediation procedures.
    Uses ChromaDB when it loads successfully; otherwise falls back to in-memory keyword search.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = COLLECTION_NAME,
    ):
        self.persist_directory = str(persist_directory or CHROMA_PERSIST_DIR)
        self.collection_name = collection_name
        self._backend: Any = None
        self._init_backend()

    def _init_backend(self) -> None:
        chroma, ef_module = _import_chromadb()
        if chroma is None:
            self._backend = _InMemoryRemediationKB(
                persist_directory=self.persist_directory,
                collection_name=self.collection_name,
            )
            return
        try:
            self._client = chroma.PersistentClient(path=self.persist_directory)
            self._ef = _get_embedding_function()
            if self._ef is None:
                self._ef = _FallbackEmbeddingFunction()
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            self._backend = "chroma"
        except Exception:
            self._backend = _InMemoryRemediationKB(
                persist_directory=self.persist_directory,
                collection_name=self.collection_name,
            )

    def add_runbook(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        runbook_id: Optional[str] = None,
    ) -> str:
        if self._backend == "chroma":
            return self._add_runbook_chroma(content, metadata, runbook_id)
        return self._backend.add_runbook(content, metadata, runbook_id)

    def _add_runbook_chroma(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        runbook_id: Optional[str] = None,
    ) -> str:
        doc_id = runbook_id or str(uuid.uuid4())
        meta = metadata or {}
        meta_clean = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                meta_clean[k] = v
            else:
                meta_clean[k] = str(v)
        self._collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[meta_clean],
        )
        return doc_id

    def search_remediation(
        self,
        issue_description: str,
        category: Optional[str] = None,
        k: int = 5,
        n_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if self._backend == "chroma":
            return self._search_chroma(issue_description, category, k, n_results)
        return self._backend.search_remediation(issue_description, category, k, n_results)

    def _search_chroma(
        self,
        issue_description: str,
        category: Optional[str],
        k: int,
        n_results: Optional[int],
    ) -> List[Dict[str, Any]]:
        n = n_results or k
        where = {"category": category} if category else None
        try:
            results = self._collection.query(
                query_texts=[issue_description],
                n_results=n,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            results = self._collection.query(
                query_texts=[issue_description],
                n_results=n,
                include=["documents", "metadatas", "distances"],
            )
        out = []
        ids = results["ids"][0] if results["ids"] else []
        docs = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results.get("distances") else []
        for i, doc_id in enumerate(ids):
            out.append({
                "id": doc_id,
                "content": docs[i] if i < len(docs) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            })
        return out

    def update_success_rate(self, runbook_id: str, success: bool) -> None:
        if self._backend == "chroma":
            self._update_success_rate_chroma(runbook_id, success)
        else:
            self._backend.update_success_rate(runbook_id, success)

    def _update_success_rate_chroma(self, runbook_id: str, success: bool) -> None:
        try:
            existing = self._collection.get(ids=[runbook_id], include=["documents", "metadatas"])
            if not existing["ids"]:
                return
            meta = dict(existing["metadatas"][0]) if existing["metadatas"] else {}
            content = existing["documents"][0]
            current_rate = meta.get("success_rate")
            if current_rate is not None:
                new_rate = (float(current_rate) + (1.0 if success else 0.0)) / 2.0
            else:
                new_rate = 1.0 if success else 0.0
            meta["success_rate"] = round(new_rate, 2)
            self._collection.delete(ids=[runbook_id])
            self._collection.add(
                ids=[runbook_id],
                documents=[content],
                metadatas=[{k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))}],
            )
        except Exception:
            pass

    def get_by_id(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        if self._backend == "chroma":
            try:
                r = self._collection.get(ids=[runbook_id], include=["documents", "metadatas"])
                if not r["ids"]:
                    return None
                return {
                    "id": runbook_id,
                    "content": r["documents"][0],
                    "metadata": r["metadatas"][0] if r["metadatas"] else {},
                }
            except Exception:
                return None
        return self._backend.get_by_id(runbook_id)
