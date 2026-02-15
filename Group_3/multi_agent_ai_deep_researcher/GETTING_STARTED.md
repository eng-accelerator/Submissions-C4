# Getting Started - Multi-Agent AI Deep Researcher

This guide will get you up and running with the Multi-Agent AI Deep Researcher system in less than 10 minutes.

## ⚡ Quick Start (5 minutes)

### 1. Prerequisites Check
```bash
# Check Python version (3.10+)
python --version

# Check Ollama is installed
ollama --version
```

### 2. Install & Configure
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1
# OR activate (Unix/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Tavily API key (get from https://tavily.com)
```

### 3. Start Ollama
```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Pull a model (while Ollama runs)
ollama pull mistral
```

### 4. Launch UI
```bash
# Terminal 3: Run Streamlit app
streamlit run ui/app.py

# Opens at: http://localhost:8501
```

### 5. Run Your First Research
1. Go to http://localhost:8501 (Streamlit UI)
2. Enter a query: "What are the latest AI developments?"
3. Adjust sliders if desired (default: 10 sources, 2 refinement passes)
4. Click "🚀 Start Research"
5. Watch the 5-step pipeline execute in real-time
6. View results in the "Results" tab
7. Download report as Markdown

---

## 🏗️ System Architecture

### The 5-Agent Pipeline

```
Query Input
    ↓
[1] Retriever Agent → Searches web via Tavily, extracts content, scores sources
    ↓
[2] Summarizer Agent → Condenses documents into coherent summary
    ↓
[3] Critic Agent → Assesses quality, calculates coverage score
    ↓
[4] Decision → Needs refinement? Loop back to [1] or proceed?
    (Max 3 passes to prevent infinite loops)
    ↓
[5] Insight Agent → Extracts key findings with confidence scores
    ↓
[6] Reporter Agent → Generates professional 7-section markdown report
    ↓
[7] Streamlit UI → Displays results with 4 tabs and export options
```

### Key Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Retriever** | Finds relevant sources | Tavily API + BeautifulSoup |
| **Summarizer** | Consolidates information | LLM (Ollama) with temperature=0.3 |
| **Critic** | Quality assessment | Deterministic scoring algorithm |
| **Insight** | Extract key findings | LLM with temperature=0.4 |
| **Reporter** | Generate report | Markdown templating |
| **UI** | User interface | Streamlit (4 tabs) |
| **Orchestration** | Agent coordination | LangGraph StateGraph |

---

## 📊 UI Overview

### Research Tab
- **Query Input**: Enter research question
- **Configuration**: 
  - Max Sources (1-50): How many web sources to retrieve
  - Max Refinement (1-3): How many times to loop back for better results
- **Progress Display**: Real-time step indicators as pipeline executes

### Results Tab
- **Summary Section**: AI-condensed findings from all sources
- **Quality Assessment**: 
  - Coverage Score: % of topic covered (0-100%)
  - Quality Status: Adequate or Needs Refinement
  - Flagged Sources: Count of low-confidence sources
- **Key Insights**: Top findings with confidence bars
- **Full Report**: 7-section markdown document
- **Download**: Save report as Markdown

### Sources Tab
- **Source Table**: All retrieved sources with:
  - Title
  - Domain
  - Confidence score (%)
  - URL (clickable)
- **Domain Breakdown**: Bar chart showing source distribution

### History Tab
- **Execution Metrics**: Total sources, iterations, timestamp
- **Agent Timeline**: Bar chart showing how long each agent took

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=300

# Tavily Search API
TAVILY_API_KEY=your_api_key_here

# Graph State
FAISS_INDEX_PATH=./data/faiss_index
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Key Settings in Code

**agents/summarizer.py**
- Temperature: 0.3 (focused summaries)
- Max summary length: 2000 characters

**agents/critic.py**
- Coverage threshold: 0.8 (need ≥80% coverage)
- Source confidence threshold: 0.6 (flag below this)
- Refinement enabled: True (will loop if needed)

**agents/insight.py**
- Temperature: 0.4 (balanced extraction)
- Max insights: 5 per research

---

## 🚀 Running Programmatically

For automation or testing, run directly in Python:

```python
from main import build_research_graph, run_research
import uuid

# Create session
session_id = str(uuid.uuid4())

# Build graph
graph = build_research_graph()

# Run research
result = run_research(
    query="What is quantum computing?",
    session_id=session_id,
    graph=graph,
    max_iterations=2
)

# Access results
print(result['final_report'])
print(f"Sources used: {len(result['source_metadata'])}")
print(f"Coverage: {result['critique']['coverage_score']:.1%}")
```

---

## 🔍 Debugging

### Check Installation
```bash
# Test each module
python -c "from agents.retriever import RetrieverAgent; print('✓ Retriever')"
python -c "from agents.summarizer import SummarizerAgent; print('✓ Summarizer')"
python -c "from agents.critic import CriticAgent; print('✓ Critic')"
python -c "from agents.insight import InsightAgent; print('✓ Insight')"
python -c "from agents.reporter import ReporterAgent; print('✓ Reporter')"
python -c "from main import build_research_graph; print('✓ Graph')"
```

### Check Ollama
```bash
# Test Ollama connection
ollama list

# Verify model is running
curl http://localhost:11434/api/tags
```

### Check Tavily API
```bash
# Verify API key works
python -c "
from config import settings
from tavily import TavilyClient
client = TavilyClient(api_key=settings.tavily_api_key)
result = client.search('test')
print(f'✓ Tavily API working: {len(result[\"results\"])} results')
"
```

### View Logs
```bash
# Logs are JSON formatted with correlation IDs
tail -f nohup.out

# Filter by session
grep session_id nohup.out | jq .
```

---

## ⚠️ Common Issues

### "Connection refused" (Ollama)
```bash
# Ollama not running?
ollama serve

# Still not working?
# Check if port 11434 is in use:
netstat -an | grep 11434
```

### "TAVILY_API_KEY not found"
```bash
# Edit .env file
# Get key from https://tavily.com

cat .env
# Should show: TAVILY_API_KEY=your_key
```

### "No module named 'agents'"
```bash
# Make sure you're in project root directory
pwd  # Should end with: multi_agent_ai_deep_researcher

# Or add to PYTHONPATH
set PYTHONPATH=%PYTHONPATH%;.
```

### Streamlit "ModuleNotFoundError"
```bash
# Make sure venv is activated
.\.venv\Scripts\Activate.ps1

# Then run again
streamlit run ui/app.py
```

### FAISS index errors
```bash
# Clear faiss index cache
rm -rf data/faiss_index

# It will rebuild on next run
streamlit run ui/app.py
```

---

## 📈 Performance Tips

### Faster Research
- **Reduce max_sources**: From 10 to 5 (default execution ~60 sec)
- **Disable refinement**: Set max_refinement to 1 (skips loop-back)
- **Use faster model**: mistral-light instead of mistral

### Better Results
- **More sources**: Increase max_sources to 15-20
- **Enable refinement**: Keep max_refinement at 2-3
- **Specific queries**: "Latest AI developments in 2024" vs "AI"

### Monitor Resource Usage
```bash
# Watch GPU/CPU
nvidia-smi  # GPU
htop         # CPU & Memory
```

---

## 📚 Next Steps

1. **Try different queries**: Test with various research topics
2. **Adjust configuration**: Experiment with sliders and settings
3. **Review documentation**: See [README.md](README.md) for deep dives
4. **Read architecture**: See [PHASE_3_4_IMPLEMENTATION.md](PHASE_3_4_IMPLEMENTATION.md)
5. **Check agent code**: Each agent in `agents/` folder has full docstrings

---

## 🤝 Contributing

To extend the system:

1. **Add new agent**: Copy `agents/base.py` structure
2. **Modify prompt**: Edit LLM prompts in agent files
3. **Change model**: Update `OLLAMA_MODEL` in .env
4. **Adjust UI**: Edit `ui/app.py` and `ui/components.py`

See README.md for full development guidelines.

---

## 📞 Support

- **Issues**: Check logs (JSON formatted)
- **Configuration**: Review .env.example
- **API Limits**: Check Tavily rate limits
- **Performance**: Monitor Ollama resource usage

Happy researching! 🎉
