# Group 14 Hackathon Submission - Astraeus Multi-Agent AI Deep Researcher

**Submitted by:** Deepti Parrikar  
**Project Name:** Astraeus - Multi-Agent AI Deep Researcher  
**Team:** Group 14

---

## 🚀 Executive Summary

Astraeus is an autonomous multi-agent AI research system that plans, investigates, and synthesizes knowledge through a sequential pipeline of 6 specialized agents. It addresses the fundamental challenge of modern research: scattered truth across academic papers, live web results, technical docs, and contradictory viewpoints.

---

## 🔗 Key Submission Links

- **💻 GitHub Repository:** https://github.com/deeptiparrikar/Astraeus-Multi-Agent-AI-Researcher
- **📊 Live Dashboard:** Streamlit-based interactive research pipeline
- **📄 Documentation:** See README.md in repository
- **🎨 Agent Pipeline Visualization:** ![Agent Orchestration](https://raw.githubusercontent.com/deeptiparrikar/Astraeus-Multi-Agent-AI-Researcher/main/assets/agent_orchestration_chart.png)

---

## ❗ Problem Statement

Research teams face:
- **Scattered Information:** Truth fragmented across multiple sources
- **Confirmation Bias:** Manual research vulnerable to biased selection
- **Slow Synthesis:** Time-consuming evidence gathering and analysis
- **Lack of Transparency:** No confidence scoring or source credibility tracking
- **Cost Blindness:** Unknown token/API costs during research

---

## 💡 Solution

A **6-agent sequential pipeline** where each agent has specialized responsibilities:

1. **Research Coordinator** - Query analysis and expansion
2. **Contextual Retriever** - Multi-source evidence collection (RAG + Web)
3. **Critical Analysis** - Contradiction detection and claim extraction
4. **Fact-Checking** - Source credibility scoring and verification
5. **Insight Generation** - Pattern recognition and hypothesis creation
6. **Report Builder** - Executive summary and markdown report generation

**Key Innovation:** Not just "ask an LLM and hope" - demonstrates production-ready AI engineering patterns including agent orchestration, RAG, multi-source evidence handling, contradiction detection, confidence scoring, and real-time cost observability.

---

## 🛠 Technology Stack

**Core Framework:**
- Python 3.10+
- Streamlit (interactive UI/dashboard)

**AI & LLM:**
- OpenRouter (multi-model gateway)
- Anthropic Claude / OpenAI models
- Local sentence-transformers embeddings (all-MiniLM-L6-v2)
- Custom state machine orchestration (LangGraph-style flow)

**RAG & Retrieval:**
- Local persistent vector store (numpy + JSON)
- Multi-query retrieval + reciprocal-rank fusion
- Tavily web search for live evidence
- Chunking and hybrid retrieval modes

**Analytics:**
- NumPy, Pandas, scikit-learn
- Plotly visualizations
- Per-agent token/cost telemetry

---

## ✨ Key Features

🤖 **6 Specialized AI Agents** working in sequence  
🗄️ **Multi-Vector Database RAG** (extensible to Pinecone/Weaviate/Chroma/Qdrant)  
🔍 **Multi-source retrieval** (indexed docs + live web search)  
⚖️ **Contradiction detection** and source credibility scoring  
💡 **Automated insights** - themes, hypotheses, knowledge-gap detection  
📊 **Real-time token and cost tracking** per agent  
🎨 **Live animated pipeline visualization** with state transitions  
📈 **Post-run analytics panels** (embeddings, retrieval waterfall, claims-evidence)  
💰 **Budget-aware operation** through token visibility  
📄 **Decision-ready markdown reports** with citations and downloads  

---

## 🏗 Agent Architecture

### Pipeline Flow

```
User Query → Coordinator → Retriever → Critical Analysis → Fact-Checking → Insights → Report
                            ↓               ↓                    ↓
                    [Shared Pipeline State & Token Telemetry]
                            ↑               ↑
                     [Feedback loops for contradictions/insufficient evidence]
```

### Agent Details

**1. Research Coordinator Agent**
- Role: Master orchestrator
- Responsibilities: Query analysis, query expansion, routing hints
- Tech: Rule-based + optional LLM expansion, shared context initialization

**2. Contextual Retriever Agent**
- Role: Multi-source evidence collector
- Responsibilities: Vector retrieval + web search, reranking, chunk assembly
- Tech: Multi-query retrieval, fusion ranking, Tavily integration

**3. Critical Analysis Agent**
- Role: Evidence analyzer
- Responsibilities: Claim extraction, contradiction detection, evidence chains
- Tech: LLM JSON extraction + regex fallback + semantic conflict heuristics

**4. Fact-Checking Agent**
- Role: Claim verifier
- Responsibilities: Source credibility scoring, support-count validation, verdicting
- Tech: Tiered credibility map + cross-source overlap logic

**5. Insight Generation Agent**
- Role: Pattern recognizer
- Responsibilities: Theme clustering, gap identification, hypothesis creation
- Tech: LLM-driven synthesis + stats-based fallback

**6. Report Builder Agent**
- Role: Final synthesis
- Responsibilities: Executive summary, key findings, citations, markdown report
- Tech: LLM summarization + structured report assembly + downloadable output

---

## 🎯 Innovation Highlights

1. **Sequential Agent Pipeline** - Each agent adds structured output to shared state (banking approval flow pattern)
2. **Contradiction-Aware Research** - Actively detects and highlights conflicting evidence
3. **Transparent Cost Tracking** - Real-time token and dollar cost per agent and per call
4. **Multi-Source Evidence** - Combines vector RAG with live web search
5. **Production-Ready Patterns** - Demonstrates scalable enterprise workflow architecture
6. **Visual Pipeline** - Live animated status with per-agent progress tracking

---

## 📊 Dashboard Components

- **Agent Pipeline Visualization:** Horizontal 6-card agent lane with visual states (Pending, Waiting, Running, Complete, Error)
- **Token Usage Dashboard:** Input/output/total tokens, per-agent cost breakdown
- **RAG Visualization:** Embedding space view, retrieval waterfall, claims & evidence panel
- **Results & Analytics:** Fact-check totals, theme strength summaries, contradiction-aware evidence reporting

---

## 🎓 Use Cases

**Target Users:**
- Researchers and academics
- Business analysts and consultants
- Students conducting literature reviews
- Decision-makers needing source-backed insights
- Compliance and risk assessment teams

**Applications:**
- Market research and competitive analysis
- Academic literature reviews
- Due diligence and fact-checking
- Policy research and impact analysis
- Technical documentation synthesis

---

## 🚀 Getting Started

```bash
# Clone repository
git clone https://github.com/deeptiparrikar/Astraeus-Multi-Agent-AI-Researcher.git
cd Astraeus-Multi-Agent-AI-Researcher

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure .env with API keys
# OPENROUTER_API_KEY=your_key
# TAVILY_API_KEY=your_key

# Launch application
streamlit run app.py
```

---

## 📈 Future Roadmap

- LangChain / LangGraph integration
- LlamaIndex query engines
- Cloud vector database connectors (Pinecone, Weaviate, Chroma, Qdrant)
- HuggingFace model alternatives
- Citation export formats (BibTeX, APA, MLA)
- Collaborative research sessions
- Export to various formats (PDF, DOCX, JSON)

---

## 🏆 Competition Relevance

This project showcases:
- **Advanced AI Engineering:** Multi-agent orchestration with state management
- **Production Patterns:** Scalable architecture suitable for enterprise deployment
- **Cost Awareness:** Budget-conscious design with full observability
- **User Experience:** Interactive dashboard with real-time feedback
- **Practical Application:** Solves real research pain points
- **Technical Depth:** RAG, vector search, LLM integration, contradiction detection

---

## 👥 Team

**Deepti Parrikar** - Group 14  
*Background:* QA & Banking Domain Experience

---

**Repository:** https://github.com/deeptiparrikar/Astraeus-Multi-Agent-AI-Researcher  
**Submission Date:** February 15, 2026  
**Hackathon:** Engineering Accelerator C4 Group Projects
