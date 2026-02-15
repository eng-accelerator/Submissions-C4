---
name: query-expansion
description: Expands a single research query into multiple search variants for multi-query retrieval. Use when the Coordinator agent needs to generate diverse phrasings of the user's question to maximize recall from the vector store and web search.
---

# Query Expansion

Generate 3-5 alternative phrasings of the original query to improve retrieval coverage.

## Strategy

1. **Rephrase** the original query using synonyms and alternative structures
2. **Decompose** complex queries into simpler sub-questions
3. **Generalize** one variant to capture broader context
4. **Specialize** one variant to target precise technical terms

## Output Format

Return a list of strings, one query per entry. Always include the original query as the first entry.

## Examples

Original: "How does retrieval-augmented generation work?"

Expanded:
- How does retrieval-augmented generation work?
- RAG architecture pipeline explanation
- combining vector search with LLM generation
- retrieval augmented generation vs fine-tuning approaches
- how do RAG systems retrieve and inject context into prompts

## Constraints

- Maximum 5 expanded queries
- Each variant must be a standalone search query (not a sentence fragment)
- Avoid redundant variants that would return the same results
- Preserve the original intent across all variants
