---
name: report-generation
description: Synthesizes the full pipeline output into a structured markdown research report with citations. Use when the Report Builder agent needs to produce the final deliverable from themes, verified claims, contradictions, and insights.
---

# Report Generation

Produce a decision-ready markdown report from the complete pipeline context.

## Report Structure

1. **Executive Summary** (3-5 sentences) — Key finding, confidence level, and scope.
2. **Key Findings** — Bullet list of top verified claims with confidence badges.
3. **Detailed Analysis** — One section per major theme. Each section includes supporting evidence with inline citations.
4. **Contradictions and Caveats** — List all detected contradictions with both sides presented fairly.
5. **Knowledge Gaps** — Areas where evidence was insufficient.
6. **Sources** — Numbered reference list with source type labels.

## Citation Format

Use inline numbered citations: `[1]`, `[2]`. Each number maps to the Sources section at the end.

## Confidence Badges

- High (>0.8): Present as established finding
- Medium (0.5-0.8): Present with qualifier ("evidence suggests")
- Low (<0.5): Present as preliminary or contested

## Constraints

- Report must be valid markdown
- Maximum 3000 words for the body (excluding sources)
- Every factual statement must have at least one citation
- Contradictions must present both sides without editorial bias
- Knowledge gaps must be explicit, not hidden
