"""
Agents package for Multi-Agent AI Deep Researcher.

Agents:
- base.py - Abstract BaseAgent class
- retriever.py - Web search and document retrieval
- summarizer.py - Content summarization
- critic.py - Quality assessment and critique
- insight.py - Key insight extraction
- reporter.py - Report generation
- supervisor.py - Deterministic routing
"""

from agents.base import BaseAgent
from agents.retriever import RetrieverAgent
from agents.summarizer import SummarizerAgent
from agents.critic import CriticAgent
from agents.insight import InsightAgent
from agents.reporter import ReporterAgent
from agents.supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "RetrieverAgent",
    "SummarizerAgent",
    "CriticAgent",
    "InsightAgent",
    "ReporterAgent",
    "SupervisorAgent",
]
