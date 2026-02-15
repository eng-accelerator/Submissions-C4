---
name: evidence-retrieval
description: Multi-source evidence collection strategy combining vector store search with live web results. Use when the Retriever agent needs to gather and rank evidence chunks from heterogeneous sources.
---

# Evidence Retrieval

Collect and rank evidence from multiple sources using reciprocal-rank fusion.

## Pipeline

1. **Vector search** — Run each expanded query against the local ChromaDB store. Collect top-k chunks per query.
2. **Web search** (if hybrid/web mode) — Query Tavily with the top 2 expanded queries. Parse results into chunks with source URLs.
3. **Deduplication** — Remove chunks with >85% text overlap (Jaccard on word sets).
4. **Reciprocal-rank fusion** — For each chunk appearing in multiple result lists, compute RRF score: `sum(1 / (k + rank))` where k=60.
5. **Final ranking** — Sort by fused score descending. Return top-k.

## Chunk Metadata

Each returned chunk must include:
- `text`: The chunk content
- `source`: Origin identifier (filename, URL, or "web")
- `score`: Fusion score (0-1 normalized)
- `source_type`: One of "document", "web", "uploaded"

## Constraints

- Never return more than 2x top_k chunks
- Web results are limited to 5 per query to control latency
- Chunks exceeding 1500 tokens should be split at paragraph boundaries
