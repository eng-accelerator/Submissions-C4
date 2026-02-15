# 🚨 DevOps Incident Analysis Suite

A production-ready **Multi-Agent AI System** for automated DevOps incident analysis and response. Built with LangChain, LangGraph, and Streamlit.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-green.svg)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41+-red.svg)](https://streamlit.io/)

## 🎯 Overview

This system implements a **multi-agent RAG-style architecture** that automatically:
- Parses and classifies incident logs
- Generates remediation plans with root cause analysis
- Creates actionable DevOps runbooks
- Sends Slack notifications
- Auto-creates JIRA tickets for critical incidents

## 🏗️ Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Log Reader/  │      │ Remediation  │      │  Cookbook    │
│ Classifier   │──────│    Agent     │──────│ Synthesizer  │
│    Agent     │      │              │      │    Agent     │
└──────────────┘      └──────────────┘      └──────────────┘
                              │                     │
                    ┌─────────┴─────────┐          │
                    ▼                   ▼          ▼
            ┌──────────────┐    ┌──────────────────────┐
            │ JIRA Ticket  │    │   Notification       │
            │    Agent     │    │      Agent           │
            └──────────────┘    └──────────────────────┘
```

### Workflow Flow

```
Input Log → Classify → Remediate → [JIRA if Critical] → Cookbook → Notify → End
```

## 🤖 Agent Descriptions

### 1️⃣ Log Reader / Classifier Agent
**Purpose:** Parse and classify incident logs

**Capabilities:**
- Extract structured fields (timestamp, service, severity, error code)
- Classify incident type (e.g., DatabaseTimeout, APIFailure)
- Determine severity level (INFO, WARNING, ERROR, CRITICAL)
- Output structured JSON

**Technology:** LLM-powered parsing with regex fallbacks

---

### 2️⃣ Remediation Agent
**Purpose:** Generate remediation plans using RAG-style reasoning

**Capabilities:**
- Map incidents to root causes
- Access knowledge base of common incident patterns
- Recommend specific, actionable fixes
- Provide technical rationale and impact assessment

**Technology:** LLM + built-in knowledge base (RAG pattern)

---

### 3️⃣ Cookbook Synthesizer Agent
**Purpose:** Create DevOps runbook checklists

**Capabilities:**
- Convert remediation plans to step-by-step procedures
- Include prerequisites, validation steps, and rollback plans
- Format as markdown runbooks
- Downloadable and reusable

**Technology:** LLM-powered synthesis

---

### 4️⃣ Notification Agent
**Purpose:** Send alerts to Slack

**Capabilities:**
- Format incident summaries with severity badges
- Include remediation steps
- Link to JIRA tickets
- Rich message formatting with blocks

**Technology:** Slack Webhook API

---

### 5️⃣ JIRA Ticket Agent
**Purpose:** Auto-create tickets for critical incidents

**Capabilities:**
- Activate only for CRITICAL severity
- Populate summary, description, priority
- Attach remediation plan
- Return ticket URL

**Technology:** JIRA REST API

---

### 6️⃣ Orchestrator (LangGraph)
**Purpose:** Coordinate multi-agent workflow

**Capabilities:**
- Maintain shared state across agents
- Conditional branching (JIRA on critical)
- Sequential and parallel execution
- Error handling and recovery

**Technology:** LangGraph state machine

## 📁 Project Structure

```
devops-incident-suite/
├── agents/
│   ├── __init__.py
│   ├── log_classifier.py       # Agent 1: Log parsing & classification
│   ├── remediation.py          # Agent 2: Remediation plan generation
│   ├── cookbook.py             # Agent 3: Runbook synthesis
│   ├── notification.py         # Agent 4: Slack notifications
│   └── jira_ticket.py          # Agent 5: JIRA ticket creation
│
├── orchestrator/
│   ├── __init__.py
│   ├── state.py                # Pydantic state models
│   └── graph.py                # LangGraph orchestrator
│
├── ui/
│   ├── __init__.py
│   └── streamlit_app.py        # Streamlit web interface
│
├── utils/
│   ├── __init__.py
│   ├── llm_client.py           # OpenRouter LLM client
│   └── api_clients.py          # Slack & JIRA clients
│
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ (or Docker)
- OpenRouter API key
- (Optional) Slack Webhook URL
- (Optional) JIRA credentials

### Local Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd devops-incident-suite
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment (optional):**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the application:**
```bash
python main.py
```

6. **Access the UI:**
Open browser to `http://localhost:8501`

### Docker Installation

1. **Build the image:**
```bash
docker build -t devops-incident-suite .
```

2. **Run the container:**
```bash
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=your_key_here \
  devops-incident-suite
```

Or with all configurations:
```bash
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=your_openrouter_key \
  -e SLACK_WEBHOOK_URL=your_slack_webhook \
  -e JIRA_URL=https://your-domain.atlassian.net \
  -e JIRA_USERNAME=your_email \
  -e JIRA_API_TOKEN=your_jira_token \
  devops-incident-suite
```

3. **Access the UI:**
Open browser to `http://localhost:8501`

## 🔧 Configuration

### Required Configuration
- **OpenRouter API Key**: LLM access (required)

### Optional Configuration
- **Slack Webhook URL**: Enable Slack notifications
- **JIRA URL, Username, API Token**: Enable JIRA ticket creation
- **LLM Model**: Choose model (default: `openai/gpt-4o`)

### Supported LLM Models
- `openai/gpt-4o` (recommended)
- `openai/gpt-4-turbo`
- `anthropic/claude-3.5-sonnet`
- `google/gemini-pro`

## 💡 Usage

### Via UI (Streamlit)

1. **Enter Configuration** in sidebar:
   - OpenRouter API Key (required)
   - Slack Webhook URL (optional)
   - JIRA credentials (optional)

2. **Paste Log Data** in text area

3. **Click "Analyze Incident"**

4. **View Results:**
   - Classified Incident
   - Remediation Plan
   - DevOps Runbook
   - JIRA Ticket Status
   - Slack Notification Status

5. **Download Runbook** (optional)

### Programmatic Usage

```python
from orchestrator.state import IncidentAnalysisState
from orchestrator.graph import IncidentAnalysisOrchestrator

# Create state
state = IncidentAnalysisState(
    raw_log_input="2024-02-14 ERROR [api] Connection timeout",
    openrouter_api_key="your-key",
    llm_model="openai/gpt-4o"
)

# Run orchestrator
orchestrator = IncidentAnalysisOrchestrator(state)
final_state = orchestrator.run()

# Access results
print(final_state.classified_incident)
print(final_state.remediation_plan)
print(final_state.cookbook_checklist)
```

## 📊 Example Flow

### Input Log
```
2024-02-14 10:23:45 CRITICAL [payment-service] Database connection timeout after 30s
Connection pool exhausted: max_connections=100, active=100, idle=0
Error code: DB_CONN_TIMEOUT_001
```

### Agent Processing

**Log Classifier Output:**
```json
{
  "incident_type": "DatabaseConnectionTimeout",
  "severity": "CRITICAL",
  "affected_service": "payment-service",
  "summary": "Database connection pool exhaustion"
}
```

**Remediation Plan:**
```json
{
  "root_cause_hypothesis": "Connection pool sized too small for current load",
  "recommended_fixes": [
    "Increase max_connections to 200",
    "Implement connection leak detection",
    "Add circuit breaker pattern"
  ],
  "urgency": "CRITICAL"
}
```

**Cookbook Checklist:**
```markdown
# Database Connection Pool Remediation

## Prerequisites
- Database admin access
- Application restart capability

## Steps
1. Scale connection pool: Edit config.yaml, set max_connections: 200
2. Deploy configuration change
3. Restart payment-service
4. Monitor connection metrics

## Validation
1. Verify max_connections: SHOW VARIABLES LIKE 'max_connections'
2. Check active connections: SELECT COUNT(*) FROM information_schema.processlist
```

**JIRA Ticket:** ✅ Created (CRITICAL severity)

**Slack Notification:** ✅ Sent with summary + remediation steps

## 🔒 Security

- Non-root user in Docker container
- API keys stored as environment variables
- No credentials in code or logs
- HTTPS for all external API calls

## 🧪 Testing

Test with sample logs:
```bash
# In the UI, click "Load Sample Log"
```

Or use custom logs:
```
2024-02-14 15:30:00 ERROR [auth-service] JWT validation failed
Token expired: issued_at=2024-02-13, expires_at=2024-02-14
User session terminated for user_id=12345
```

## 📈 Monitoring

The system tracks:
- Agent execution times
- Error rates per agent
- LLM token usage
- API call success rates

Access via state object:
```python
final_state.errors  # List of errors during processing
```

## 🛠️ Development

### Adding New Agents

1. Create agent file in `agents/`:
```python
class MyAgent:
    def process(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        # Your logic
        return state
```

2. Add to orchestrator in `orchestrator/graph.py`:
```python
workflow.add_node("my_agent", self._my_agent_node)
workflow.add_edge("previous_agent", "my_agent")
```

### Extending Knowledge Base

Edit `agents/remediation.py`:
```python
INCIDENT_PATTERNS = {
    "YourIncidentType": {
        "common_causes": [...],
        "typical_fixes": [...]
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- LangChain for agent framework
- LangGraph for orchestration
- Streamlit for UI
- OpenRouter for LLM access

## 📞 Support

For issues or questions:
- Open GitHub issue
- Check documentation
- Review example logs

## 🔄 Roadmap

- [ ] Add more incident patterns to knowledge base
- [ ] Implement PagerDuty integration
- [ ] Add metrics dashboard
- [ ] Support for multi-log analysis
- [ ] Real-time log streaming
- [ ] ML-based pattern detection

---

**Built with ❤️ for DevOps teams worldwide**
