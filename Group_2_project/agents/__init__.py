"""
agents/
=======
Specialized AI agents for the multi-agent research pipeline.

Each agent has a single responsibility:
    decomposer_agent.py   — Breaks complex queries into atomic sub-queries.
    retriever_agent.py    — Searches the web and collects sources (Tavily API).
    analysis_agent.py     — Summarizes findings, detects contradictions.
    fact_checker_agent.py — Cross-validates claims, assigns confidence scores.
    insight_agent.py      — Generates hypotheses and identifies trends.
    report_agent.py       — Compiles structured report, evaluates quality.

Each agent exposes:
    - A result dataclass (e.g., SourceDocument, AnalysisResult)
    - An Agent class with a run(state) method
"""
