---
name: source-credibility
description: Scores source credibility using a tiered trust model and cross-validates claims against multiple sources. Use when the Fact-Checker agent needs to assign confidence scores and verification verdicts to extracted claims.
---

# Source Credibility Scoring

Evaluate claim reliability by combining source trustworthiness with cross-source validation.

## Credibility Tiers

| Tier | Source Type | Base Score | Examples |
|------|-----------|-----------|----------|
| 1 | Peer-reviewed / academic | 0.95 | arxiv, PubMed, IEEE, ACM |
| 2 | Official documentation | 0.90 | docs.python.org, RFC, API docs |
| 3 | Established tech publication | 0.80 | Nature, MIT Tech Review |
| 4 | Quality blog / tutorial | 0.65 | Towards Data Science, official blogs |
| 5 | General web / unknown | 0.45 | Unverified web results |
| 6 | User-uploaded document | 0.50 | PDFs, notes (credibility unknown) |

## Cross-Validation

For each claim, count how many independent sources support it:
- **3+ sources**: Strong support → verdict "Supported"
- **2 sources**: Moderate support → verdict "Likely"
- **1 source, high tier**: Conditional → verdict "Plausible"
- **1 source, low tier**: Weak → verdict "Unverified"
- **Contradicted by higher-tier source**: → verdict "Disputed"

## Final Confidence Score

```
confidence = base_credibility * support_multiplier
support_multiplier = min(1.0, 0.5 + 0.2 * supporting_source_count)
```

## Output Per Claim

- `claim`: Original claim text
- `verdict`: One of "Supported", "Likely", "Plausible", "Unverified", "Disputed"
- `confidence`: Float 0-1
- `supporting_sources`: List of source identifiers
- `contradicting_sources`: List of source identifiers (if any)
