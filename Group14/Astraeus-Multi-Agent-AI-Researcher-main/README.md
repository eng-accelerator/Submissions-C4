# Astraeus - Multi-Agent AI Deep Researcher

**An autonomous AI research assistant powered by specialized agents, RAG, and real-time collaboration**

[Image: Hero banner showing 6-agent research pipeline with live status animation]

┌──────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐
│ Coordinator  │→→│  Retriever   │→→│ Critical Check │→→│ Fact Checker │→→│ Insight Engine │→→│ Report Builder│
└──────────────┘   └──────────────┘   └────────────────┘   └──────────────┘   └────────────────┘   └──────────────┘
       Query            Sources + RAG         Contradictions         Verification        Patterns + Gaps       Final Dossier


**Executive Summary:** 
Astraeus is a multi-agent AI research system that plans, investigates, and synthesizes knowledge autonomously.

Modern research is hard for one simple reason: the truth is scattered. Teams must manually combine academic references, live web results, technical docs, and contradictory viewpoints. This is slow, expensive, and vulnerable to confirmation bias.

Multi-Agent AI Deep Researcher solves this with a sequential swarm of 6 specialized agents. Each agent has a clear role (orchestration, retrieval, analysis, verification, insight generation, and reporting), and each stage adds structured output to a shared pipeline state. Think of it like a banking approval flow: each desk adds checks before the next desk signs off.

The key innovation is not just “ask an LLM and hope.” This project demonstrates practical AI engineering patterns: agent orchestration, retrieval-augmented generation (RAG), multi-source evidence handling, contradiction detection, transparent confidence scoring, and real-time cost/token observability.

This system is designed for researchers, analysts, students, consultants, and decision-makers who need deeper, more balanced, and source-backed answers. As a hackathon submission, it showcases production-ready architecture patterns that can scale into enterprise workflows.



**Key Features:**
🤖 6 Specialized AI Agents working in sequence
🗄️ Multi-Vector Database RAG architecture (current MVP uses local vector store; connectors can extend to Pinecone/Weaviate/Chroma/Qdrant)
🔍 Multi-source retrieval (indexed docs + live web search)
⚖️ Contradiction detection and source credibility scoring
💡 Automated insights, themes, hypotheses, and knowledge-gap detection
📊 Real-time token and cost tracking per agent
🎨 Live animated pipeline visualization with state transitions
📈 Post-run analytics panels (embeddings, retrieval waterfall, claims-evidence)
💰 Budget-aware operation through token visibility and model controls
📄 Decision-ready markdown report with citations and downloadable output


**Technology Stack:**

Core Framework:
# Python 3.10+
# Streamlit (interactive UI/dashboard)

AI & LLM:
# OpenRouter (multi-model gateway)
A# nthropic Claude / OpenAI model support via OpenRouter model IDs
# Local sentence-transformers embeddings (all-MiniLM-L6-v2)
# Agent pipeline orchestration (custom state machine; LangGraph-style flow)

RAG & Retrieval:
* Local persistent vector store (numpy + JSON persistence)
* Multi-query retrieval + reciprocal-rank fusion
* Tavily web search integration for live evidence
* Chunking, ingestion, and hybrid retrieval modes

Data & Analytics:
# NumPy, Pandas, scikit-learn
# Plotly (visual analytics)
# Token/cost telemetry with per-agent breakdown

Optional/Pluggable Ecosystem (Hackathon Roadmap):
# LangChain / LangGraph integration
# LlamaIndex query engines
# Pinecone, Weaviate, Chroma, Qdrant connectors
# HuggingFace hosted/local model alternatives


**Agent Architecture**

1) Research Coordinator Agent
Role: Master orchestrator
Responsibilities: Query analysis, query expansion, routing hints
Tech: Rule-based + optional LLM expansion, shared context initialization

2) Contextual Retriever Agent
Role: Multi-source evidence collector
Responsibilities: Vector retrieval + web search, reranking, chunk assembly
Tech: Multi-query retrieval, fusion ranking, Tavily integration

3) Critical Analysis Agent
Role: Evidence analyzer
Responsibilities: Claim extraction, contradiction detection, evidence chains
Tech: LLM JSON extraction + regex fallback + semantic conflict heuristics

4) Fact-Checking Agent
Role: Claim verifier
Responsibilities: Source credibility scoring, support-count validation, verdicting
Tech: Tiered credibility map + cross-source overlap logic

5) Insight Generation Agent
Role: Pattern recognizer
Responsibilities: Theme clustering, gap identification, hypothesis creation
Tech: LLM-driven synthesis + stats-based fallback

6) Report Builder Agent
Role: Final synthesis
Responsibilities: Executive summary, key findings, citations, markdown report
Tech: LLM summarization + structured report assembly + downloadable output

Dashboard Sections
A. Top Navigation Bar : Query input with validation , Launch/Reset controls, Advanced options expander, Live summary cards (docs indexed, model, top-k, expansions)

B. Agent Pipeline Visualization: Horizontal 6-card agent lane, Visual states: Pending, Waiting, Running, Complete, Error, Animated connectors and progress fill, Per-agent elapsed time and tooltips

C. Overall Progress Tracker: Segmented progress strip, Complete/total count, Active pipeline status

D. Token Usage Dashboard: Input/output/total tokens, Total LLM , Per-agent cost + call count + elapsed time, Advanced efficiency stats

E. RAG Visualization Panel: Embedding space view, Retrieval waterfall, Claims & evidence panel
(When enabled) token/cost analytics tab

F. Results Section: Pipeline result metrics, Fact-check totals, Themes and insights, Contradiction-aware evidence reporting

G. Analytics & Insights: Theme strength summaries, Verification distribution, Evidence quality, indicators, Source-level confidence signals

H. Cost Optimization Panel: Most expensive agent identification, Average cost per call / per 1K token
Context-token estimate guidance, Model-level cost awareness

I. Export Options: Download report as Markdown


**Setup Instructions**

Prerequisites: Python 3.10+, pip, Git

API keys/accounts: OpenRouter (required for LLM features), Tavily (For live web search)

Installation:
1) Clone git clone <YOUR_REPO_URL>cd Hackathon_MutiAgent_AI_researcher
2) Create virtual envpython -m venv .venv
3) Activate env# Windows (PowerShell).venv\Scripts\Activate.ps1 ; macOS/Linux# source .venv/bin/activate# 
4) Install dependenciespip install -r requirements.txt
5) Configure .env
6) Launch appstreamlit run app.py

Environment Variables & API Keys
OPENROUTER_API_KEY
TAVILY_API_KEY

**Contact & Demo**
Video Walkthrough: <https://your-video-link.com>
GitHub Repository: <https://github.com/your-username/your-repo>