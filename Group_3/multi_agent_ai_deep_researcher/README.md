# Multi-Agent AI Deep Researcher

## About
Multi-Agent AI Deep Researcher is a production-style research system that converts a user question into a structured report using a coordinated set of specialized agents. The system combines web retrieval, iterative quality review, insight extraction, and report generation using LangGraph orchestration.

## Architecture
```mermaid
flowchart LR
    U[User / API Request] --> UI[Streamlit UI<br/>ui/app.py]
    UI --> G[LangGraph Pipeline<br/>main.py]

    G --> R[Retriever Agent]
    R --> S[Summarizer Agent]
    S --> C[Critic Agent]
    C --> I[Insight Agent]
    I --> P[Reporter Agent]

    C -. refinement loop .-> R

    R --> TV[Tavily Search + Web Content]
    G --> ST[ResearchState<br/>utils/state.py]
    G --> CP[Checkpointing<br/>MemorySaver]
    P --> OUT[Markdown Research Report]
```

## Request Flow (Agent-to-Agent)
```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Graph as LangGraph
    participant Retriever
    participant Summarizer
    participant Critic
    participant Insight
    participant Reporter

    User->>UI: Submit query
    UI->>Graph: run_research(query, session_id)
    Graph->>Retriever: process(state)
    Retriever-->>Graph: retrieved_docs, source_metadata
    Graph->>Summarizer: process(state)
    Summarizer-->>Graph: summary
    Graph->>Critic: process(state)
    Critic-->>Graph: critique, needs_refinement

    alt needs_refinement && iteration < limit
        Graph->>Retriever: process(state) [refine]
    else continue
        Graph->>Insight: process(state)
        Insight-->>Graph: insights
        Graph->>Reporter: process(state)
        Reporter-->>Graph: final_report
    end

    Graph-->>UI: final state
    UI-->>User: Render report and sources
```

## AI Design Patterns Used
| Pattern | Where Used | Why It Is Used |
|---|---|---|
| Multi-Agent Pipeline | `agents/*.py`, `main.py` | Separates responsibilities across specialized agents. |
| Graph Orchestration | `main.py` (LangGraph `StateGraph`) | Defines deterministic execution order and transitions. |
| Shared State Contract | `utils/state.py` (`ResearchState`) | Standardizes data exchange across all agents. |
| Conditional Routing | `main.py` (`should_refine`) | Supports iterative refinement when quality is insufficient. |
| Retrieval-Augmented Generation (RAG) | `agents/retriever.py` + downstream LLM agents | Grounds generation on external web evidence. |
| Checkpointing | `main.py` (`MemorySaver`) | Preserves graph execution state across steps. |
| Base Agent Abstraction | `agents/base.py` | Enforces common interface, validation, and graceful failure behavior. |

## Core Concepts
| Concept | How It Appears In This Project |
|---|---|
| RAG | Web retrieval first, then LLM summarization/insight/reporting over retrieved context. |
| Multi-Agent System | Retriever, Summarizer, Critic, Insight, Reporter operate as modular agents. |
| Checkpointing | LangGraph checkpointer stores intermediate graph state. |
| Iterative Refinement | Critic can route flow back to Retriever until iteration limit. |
| Deterministic Control Flow | Supervisor and graph edges control routing without LLM-based planning. |

## Run the Project
### Prerequisites
- Python 3.10+
- Ollama installed and running
- Tavily API key

### Setup
```bash
cd Submissions-C4/Group_3/multi_agent_ai_deep_researcher
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure
```bash
cp .env.example .env
# Set at minimum:
# TAVILY_API_KEY=your_key
```

### Start services
```bash
ollama serve
ollama pull mistral
```

### Launch
```bash
streamlit run ui/app.py
```

Open: `http://localhost:8501`