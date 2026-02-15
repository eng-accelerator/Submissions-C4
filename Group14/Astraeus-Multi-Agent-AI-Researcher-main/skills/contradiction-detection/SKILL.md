---
name: contradiction-detection
description: Identifies contradictions and conflicting claims across retrieved evidence. Use when the Critical Analysis agent needs to detect disagreements between sources and flag low-confidence information.
---

# Contradiction Detection

Extract discrete claims from evidence chunks and identify conflicts between them.

## Claim Extraction

Parse each chunk into atomic claims — single factual statements that can be independently verified.

Format: `{"claim": str, "source": str, "chunk_index": int}`

## Conflict Detection Strategy

1. **Semantic grouping** — Group claims by topic using keyword overlap (>30% shared non-stop-words).
2. **Negation check** — Within each group, detect pairs where one claim negates the other (contains "not", "never", "false", antonyms).
3. **Numeric disagreement** — Flag pairs that cite different numbers for the same metric (e.g., "accuracy of 95%" vs "accuracy of 87%").
4. **Temporal conflict** — Flag pairs that assign different dates or timelines to the same event.

## Output

For each contradiction found:
- `claim_a`: First claim text and source
- `claim_b`: Conflicting claim text and source
- `conflict_type`: One of "negation", "numeric", "temporal", "semantic"
- `confidence`: Float 0-1 indicating detection confidence

## Constraints

- Only flag contradictions with confidence > 0.6
- A single claim can participate in multiple contradiction pairs
- Preserve all claims even if no contradictions are found
