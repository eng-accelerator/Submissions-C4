"""
Document ingestion helpers for user-uploaded files.
Parses file content, chunks it, and indexes chunks in the vector store.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple, Dict, Any
from datetime import datetime
import hashlib
import io
import os

import config
from rag.vector_store import index_documents


def index_uploaded_files(uploaded_files: Iterable[Any]) -> Dict[str, Any]:
    """
    Parse, chunk, and index uploaded files into the vector store.

    Returns:
      {
        "files_processed": int,
        "files_failed": int,
        "chunks_indexed": int,
        "errors": List[str],
      }
    """
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []
    errors: List[str] = []
    files_processed = 0
    files_failed = 0
    total_bytes = 0

    for uploaded in uploaded_files or []:
        filename = uploaded.name
        file_bytes = uploaded.getvalue()
        file_size = len(file_bytes)
        total_bytes += file_size
        file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
        ext = os.path.splitext(filename)[1].lower()

        try:
            if file_size > _mb_to_bytes(config.MAX_UPLOAD_FILE_MB):
                raise ValueError(
                    f"File too large ({round(file_size / (1024 * 1024), 2)} MB). "
                    f"Max per file is {config.MAX_UPLOAD_FILE_MB} MB."
                )
            if total_bytes > _mb_to_bytes(config.MAX_UPLOAD_TOTAL_MB):
                raise ValueError(
                    f"Total upload size exceeded {config.MAX_UPLOAD_TOTAL_MB} MB limit."
                )
            text = _extract_text(file_bytes, ext)
            chunks = _chunk_text(
                text,
                chunk_size=config.UPLOAD_CHUNK_SIZE,
                overlap=config.UPLOAD_CHUNK_OVERLAP,
            )
            if not chunks:
                raise ValueError("No extractable text found.")

            uploaded_at = datetime.utcnow().isoformat()
            for idx, chunk in enumerate(chunks):
                chunk_id = f"upload_{file_hash}_{idx}"
                texts.append(chunk)
                ids.append(chunk_id)
                metadatas.append(
                    {
                        "source": "user_upload",
                        "doc_type": "uploaded_document",
                        "filename": filename,
                        "file_hash": file_hash,
                        "chunk_index": idx,
                        "uploaded_at": uploaded_at,
                        "year": str(datetime.utcnow().year),
                    }
                )

            files_processed += 1
        except Exception as exc:
            files_failed += 1
            errors.append(f"{filename}: {exc}")

    chunks_indexed = index_documents(texts, metadatas=metadatas, ids=ids) if texts else 0
    return {
        "files_processed": files_processed,
        "files_failed": files_failed,
        "chunks_indexed": chunks_indexed,
        "errors": errors,
    }


def _extract_text(file_bytes: bytes, ext: str) -> str:
    """Extract plain text from a supported file type."""
    if ext in {".txt", ".md", ".csv", ".json", ".log"}:
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        if len(reader.pages) > config.MAX_PDF_PAGES:
            raise ValueError(
                f"PDF has {len(reader.pages)} pages. Max allowed is {config.MAX_PDF_PAGES}."
            )
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    raise ValueError(f"Unsupported file type: {ext or '(no extension)'}")


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Create overlapping character-based chunks with basic cleanup."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunk_size = max(200, int(chunk_size))
    overlap = max(0, min(int(overlap), chunk_size - 50))
    step = max(1, chunk_size - overlap)

    chunks: List[str] = []
    for start in range(0, len(cleaned), step):
        chunk = cleaned[start:start + chunk_size].strip()
        if len(chunk) >= 80:
            chunks.append(chunk)
        if start + chunk_size >= len(cleaned):
            break
    return chunks


def _mb_to_bytes(size_mb: int) -> int:
    return int(size_mb) * 1024 * 1024
