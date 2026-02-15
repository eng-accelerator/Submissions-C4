---
name: theme-synthesis
description: Clusters verified claims into themes, identifies knowledge gaps, and generates hypotheses. Use when the Insight Generator agent needs to find patterns across evidence and surface what the research does not cover.
---

# Theme Synthesis

Analyze verified claims to discover overarching themes, knowledge gaps, and testable hypotheses.

## Theme Clustering

1. Group claims by shared topics (keyword overlap > 40%).
2. For each group of 3+ claims, assign a theme label — a concise noun phrase summarizing the group.
3. Compute theme strength: `strength = claim_count * avg_confidence`.
4. Rank themes by strength descending.

## Knowledge Gap Detection

Identify areas where evidence is thin:
- Topics mentioned in the query but with fewer than 2 supporting claims
- Themes where all sources are low-tier (tier 4+)
- Contradictions without a high-confidence resolution
- Sub-questions from query expansion that returned zero relevant chunks

## Hypothesis Generation

For the top 3 themes, generate one hypothesis each:
- Must be a testable statement (not a question)
- Must be grounded in the evidence (cite at least 2 supporting claims)
- Should address a gap or extend a pattern

## Output Format

```json
{
  "themes": [{"label": str, "strength": float, "claim_ids": [int]}],
  "knowledge_gaps": [{"topic": str, "reason": str}],
  "hypotheses": [{"statement": str, "supporting_claims": [int], "confidence": float}]
}
```
