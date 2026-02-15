# System Architecture & Design Documentation

## Multi-Agent DevOps Incident Analysis Suite

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Agent Design Patterns](#agent-design-patterns)
3. [State Management](#state-management)
4. [LangGraph Orchestration](#langgraph-orchestration)
5. [Data Flow](#data-flow)
6. [Integration Points](#integration-points)
7. [Scalability Considerations](#scalability-considerations)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface (Streamlit)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Layer (LangGraph)                │
│  - State Management                                              │
│  - Workflow Coordination                                         │
│  - Conditional Routing                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│   Agent Layer    │ │ Agent Layer  │ │   Agent Layer    │
│  - Log Reader    │ │ - Remediation│ │   - Cookbook     │
│  - JIRA          │ │ - Notification│ │                  │
└──────────────────┘ └──────────────┘ └──────────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Utility Layer                               │
│  - LLM Client (OpenRouter)                                       │
│  - API Clients (Slack, JIRA)                                     │
│  - State Models (Pydantic)                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Stateful Coordination**: Shared state flows through all agents via LangGraph
3. **Fault Tolerance**: Each agent handles errors independently without crashing the pipeline
4. **Modularity**: Agents can be added/removed without affecting others
5. **Observability**: All state changes are tracked and errors are collected

---

## Agent Design Patterns

### 1. Log Classifier Agent

**Pattern**: Parser + Classifier Pattern

```python
Input: Raw log string
  ↓
Regex-based parsing (extract fields)
  ↓
LLM-based classification (semantic understanding)
  ↓
Output: Structured ClassifiedIncident
```

**Key Features:**
- Hybrid approach: regex for structure, LLM for semantics
- Fallback to defaults if parsing fails
- Structured output with Pydantic validation

### 2. Remediation Agent

**Pattern**: RAG (Retrieval-Augmented Generation)

```python
Input: ClassifiedIncident
  ↓
Knowledge Base Lookup (pattern matching)
  ↓
Context Augmentation (add relevant patterns)
  ↓
LLM Generation (with context)
  ↓
Output: RemediationPlan
```

**Knowledge Base Structure:**
```python
{
  "IncidentType": {
    "common_causes": [...],
    "typical_fixes": [...]
  }
}
```

**Benefits:**
- Consistent recommendations based on knowledge base
- LLM adds context-specific details
- Extensible pattern library

### 3. Cookbook Synthesizer Agent

**Pattern**: Template Generator Pattern

```python
Input: RemediationPlan
  ↓
Template Selection (runbook format)
  ↓
LLM Content Generation
  ↓
Markdown Formatting
  ↓
Output: CookbookChecklist + Markdown
```

**Output Structure:**
- Title
- Prerequisites
- Step-by-step checklist
- Validation steps
- Rollback plan

### 4. Notification Agent

**Pattern**: Message Broker Pattern

```python
Input: State (incident + remediation)
  ↓
Content Preparation (format for Slack)
  ↓
Rich Message Construction (blocks API)
  ↓
API Call (webhook)
  ↓
Output: NotificationStatus
```

**Message Format:**
- Severity badge with emoji
- Incident summary
- Top 5 remediation steps
- JIRA ticket link (if exists)
- Timestamp

### 5. JIRA Ticket Agent

**Pattern**: Conditional Executor Pattern

```python
Input: State
  ↓
Condition Check (severity == CRITICAL?)
  ↓ YES
Ticket Preparation
  ↓
JIRA API Call
  ↓
Output: JIRATicketStatus
```

**Conditional Logic:**
- Only executes for CRITICAL incidents
- Gracefully skips otherwise
- Returns status in both cases

---

## State Management

### Pydantic State Models

```python
IncidentAnalysisState
├── raw_log_input: str
├── configuration: dict
├── classified_incident: ClassifiedIncident
├── remediation_plan: RemediationPlan
├── cookbook_checklist: CookbookChecklist
├── notification_status: NotificationStatus
├── jira_ticket_status: JIRATicketStatus
├── should_create_jira: bool
└── errors: list[str]
```

### State Flow

```
Initial State (with raw_log_input)
  ↓
Log Classifier → adds classified_incident
  ↓
Remediation → adds remediation_plan
  ↓
[Conditional] JIRA → adds jira_ticket_status
  ↓
Cookbook → adds cookbook_checklist
  ↓
Notification → adds notification_status
  ↓
Final State (complete)
```

### Benefits of Pydantic State
- Type safety
- Automatic validation
- Clear contracts between agents
- Easy serialization
- IDE autocomplete

---

## LangGraph Orchestration

### Graph Structure

```python
StateGraph(IncidentAnalysisState)
│
├── Node: classify_log
│   └── Edge → generate_remediation
│
├── Node: generate_remediation
│   └── Conditional Edge
│       ├── if CRITICAL → create_jira_ticket
│       └── else → create_cookbook
│
├── Node: create_jira_ticket
│   └── Edge → create_cookbook
│
├── Node: create_cookbook
│   └── Edge → send_notification
│
└── Node: send_notification
    └── Edge → END
```

### Node Implementation

Each node is a wrapper around an agent's `process()` method:

```python
def _classify_log_node(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
    return self.log_classifier.process(state)
```

### Conditional Routing

```python
def _should_create_jira(state: IncidentAnalysisState) -> Literal["jira", "cookbook"]:
    if state.should_create_jira and self.jira_agent:
        return "jira"
    return "cookbook"
```

### Error Handling

Each agent appends errors to `state.errors[]` without raising exceptions:

```python
try:
    # Agent logic
except Exception as e:
    state.errors.append(f"Agent Error: {str(e)}")
```

This allows the workflow to continue even if one agent fails.

---

## Data Flow

### Complete Analysis Flow

```
1. User Input
   └─> Raw log string

2. Log Classifier Agent
   Input:  raw_log_input
   Output: classified_incident
           └─> incident_type, severity, service, summary

3. Remediation Agent
   Input:  classified_incident
   Output: remediation_plan
           └─> root_cause, recommended_fixes, rationale

4. [Conditional] JIRA Agent
   Input:  classified_incident + remediation_plan
   Output: jira_ticket_status
           └─> ticket_key, ticket_url

5. Cookbook Agent
   Input:  classified_incident + remediation_plan
   Output: cookbook_checklist
           └─> title, checklist_items, validation_steps

6. Notification Agent
   Input:  All previous outputs
   Output: notification_status
           └─> sent, message, timestamp

7. Final Output
   └─> Complete state with all results
```

### Data Dependencies

```
classified_incident
  ├─> Required by: remediation_plan
  ├─> Required by: jira_ticket_status
  └─> Required by: cookbook_checklist

remediation_plan
  ├─> Required by: jira_ticket_status
  ├─> Required by: cookbook_checklist
  └─> Required by: notification_status

jira_ticket_status
  └─> Used by: notification_status (for linking)
```

---

## Integration Points

### 1. OpenRouter (LLM Provider)

**Endpoint**: `https://openrouter.ai/api/v1`

**Authentication**: API Key in headers

**Usage:**
```python
ChatOpenAI(
    model="openai/gpt-4o",
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1"
)
```

**Features Used:**
- Structured output with JSON schema
- Low temperature (0.1) for consistency
- Max tokens: 2000 per request

### 2. Slack (via Webhook)

**Endpoint**: Customer-specific webhook URL

**Authentication**: Embedded in webhook URL

**Message Format**: Blocks API
```json
{
  "blocks": [
    {"type": "header", "text": "🚨 Incident Alert"},
    {"type": "section", "text": "Summary..."},
    ...
  ]
}
```

### 3. JIRA (via REST API)

**Endpoint**: `https://{domain}.atlassian.net/rest/api/2/`

**Authentication**: Basic Auth (email + API token)

**Resources Used:**
- POST `/issue` - Create ticket
- Fields: project, summary, description, issuetype, priority

---

## Scalability Considerations

### Horizontal Scaling

**Current Design**: Single-instance Streamlit app

**Scaling Options:**
1. **Multi-instance deployment** behind load balancer
2. **Async processing** with message queue (Celery/RabbitMQ)
3. **Microservices**: Break agents into separate services

### Performance Optimizations

1. **LLM Caching**: Cache common incident patterns
2. **Parallel Agent Execution**: Run independent agents concurrently
3. **Streaming**: Stream LLM responses for faster UX
4. **Batch Processing**: Process multiple logs at once

### Resource Management

**Current Limits:**
- Docker: 2 CPU, 2GB RAM (configurable)
- LLM: 2000 tokens per request
- Concurrent requests: Limited by Streamlit

**Optimization Strategies:**
- Connection pooling for JIRA/Slack
- LLM request batching
- State persistence for long workflows

### High Availability

**Components:**
1. **Stateless Design**: No local state, easy to replicate
2. **Health Checks**: Docker health endpoint
3. **Graceful Degradation**: Agents fail independently
4. **Retry Logic**: Add exponential backoff for API calls

---

## Security Architecture

### Secrets Management

```
Environment Variables (12-factor app)
  ├─> OPENROUTER_API_KEY
  ├─> SLACK_WEBHOOK_URL
  ├─> JIRA_API_TOKEN
  └─> Never in code or logs
```

### Network Security

```
User Browser
  ↓ HTTPS
Streamlit (8501)
  ↓ HTTPS
External APIs (OpenRouter, Slack, JIRA)
```

### Container Security

- Non-root user (appuser)
- Minimal base image (python:3.12-slim)
- No shell access needed
- Read-only filesystem (except /app)

---

## Monitoring & Observability

### Metrics to Track

1. **Agent Performance**
   - Execution time per agent
   - Success/failure rate
   - Error types

2. **LLM Usage**
   - Tokens per request
   - Model selection distribution
   - Response quality scores

3. **Integration Health**
   - Slack delivery rate
   - JIRA ticket creation success
   - API latency

### Logging Strategy

```python
state.errors = []  # Collect all errors

# Each agent appends errors
state.errors.append(f"Agent X: {error}")

# UI displays all errors at end
```

### Future Enhancements

- Structured logging (JSON)
- Distributed tracing (OpenTelemetry)
- Metrics export (Prometheus)
- Alerting on failures

---

## Extension Points

### Adding New Agents

1. Create agent class with `process(state) -> state` method
2. Add node to LangGraph workflow
3. Define edges (sequential or conditional)
4. Update state model if needed

### Adding New Integrations

1. Create client in `utils/api_clients.py`
2. Create agent in `agents/`
3. Add configuration to UI sidebar
4. Update state model and orchestrator

### Customizing Knowledge Base

Edit `agents/remediation.py`:
```python
INCIDENT_PATTERNS = {
    "YourPattern": {
        "common_causes": [...],
        "typical_fixes": [...]
    }
}
```

---

## Production Readiness Checklist

- [x] Structured state management (Pydantic)
- [x] Error handling in all agents
- [x] API authentication
- [x] Docker containerization
- [x] Environment variable configuration
- [x] Health checks
- [x] Non-root container user
- [x] Resource limits
- [ ] Rate limiting for LLM calls
- [ ] Retry logic with backoff
- [ ] Structured logging
- [ ] Metrics collection
- [ ] Integration tests
- [ ] Load testing

---

**Version**: 1.0  
**Last Updated**: 2024-02-14  
**Maintainer**: DevOps AI Team
