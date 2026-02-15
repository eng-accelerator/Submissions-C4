# 🛡️ Agentic Cybersecurity Orchestrator

A **RAG-powered cybersecurity platform** that combines retrieval-augmented generation with ChromaDB vector store to deliver:

- **Threat Detection & Analysis** - Monitor logs, detect anomalies, enrich with CVE intelligence
- **Vulnerability Analysis** - Scan hosts, correlate with CVEs, prioritize remediation
- **Incident Response** - Generate playbooks, retrieve historical context, guide recovery
- **Compliance Evaluation** - Assess policies (ISO27001, NIST-CSF, SOC2), identify violations
- **Full Auditability** - Complete audit trails, evidence-based decisions, explainability

## 🏗️ Project Structure

```
cyberSec_ai/
├── agents/
│   ├── log_monitor.py          # Log analysis & anomaly detection
│   ├── threat_intel.py         # CVE enrichment & threat assessment
│   ├── vuln_scanner.py         # Vulnerability analysis & correlation
│   ├── incident_response.py    # Playbook generation & response workflow
│   ├── policy_checker.py       # Compliance evaluation & policy checks
│   └── __init__.py
│
├── orchestrator/
│   ├── supervisor.py           # Master orchestrator coordinates all agents
│   └── __init__.py
│
├── vectorstore/
│   ├── chroma_client.py       # Unified ChromaDB interface
│   └── __init__.py
│
├── evaluation/
│   ├── simulator.py            # Evaluation scenarios & testing
│   └── __init__.py
│
├── cyber_demo/                 # Demo datasets
│   ├── cve_data.json          # CVE records (JSON array)
│   ├── incident_alerts.csv    # Security incidents
│   ├── policy_checks.csv      # Compliance records
│   ├── syslog_large.csv       # System logs (~500k records)
│   ├── vuln_scan.csv          # Vulnerability scans
│   └── metadata_schema.json   # Field definitions
│
├── app.py                      # Streamlit Web UI
├── main.py                     # FastAPI REST API
├── embedding_vectorstore_setup.py  # Vector store initialization
├── test_semantic_search.py    # RAG testing
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
echo "BASE_PATH=./cyber_demo" >> .env
```

### 2. Initialize Vector Store

Embed the demo datasets into ChromaDB:

```bash
python embedding_vectorstore_setup.py
```

This loads:
- **CVE Records** (260k+ documents)
- **Incident Alerts** (100k+ documents)
- **Vulnerability Scans** (15k+ documents)
- **Policy Checks** (8k+ documents)
- **System Logs** (500k+ documents - optional, commented by default)

### 3. Run the Orchestrator

Choose your interface:

#### **Option A: Web UI (Streamlit)**
```bash
streamlit run app.py
```
Opens interactive dashboard at `http://localhost:8501`

#### **Option B: REST API (FastAPI)**
```bash
python main.py
```
API available at `http://localhost:8000/docs`

#### **Option C: CLI (Direct Python)**
```python
from orchestrator.supervisor import SecurityOrchestrator

orchestrator = SecurityOrchestrator()

# Detect threat
result = orchestrator.detect_threat("Brute force attack on port 22")

# Analyze vulnerabilities
result = orchestrator.analyze_host_vulnerabilities("192.168.1.1")

# Handle incident
result = orchestrator.handle_incident(threat="SQL Injection", severity="HIGH")

# Evaluate compliance
result = orchestrator.evaluate_compliance(host="192.168.1.1")
```

## 📊 Core Components

### Agents

Each agent specializes in a security domain and queries the vector store for evidence:

| Agent | Purpose | Collections |
|-------|---------|-------------|
| **LogMonitorAgent** | Detect suspicious patterns, brute force, port scans | logs |
| **ThreatIntelligenceAgent** | Enrich threats with CVE data, assess severity | cve, incident |
| **VulnerabilityAnalysisAgent** | Scan hosts, correlate with CVEs, prioritize | vuln, cve |
| **IncidentResponseAgent** | Generate playbooks, retrieve historical response | incident, policy |
| **PolicyCheckerAgent** | Evaluate compliance, identify violations | policy |

### Orchestrator

The `SecurityOrchestrator` coordinates all agents:

```python
orchestrator.detect_threat(alert)              # Threat detection workflow
orchestrator.analyze_host_vulnerabilities(host) # Vulnerability workflow
orchestrator.handle_incident(threat, severity)  # Incident response workflow
orchestrator.evaluate_compliance(host)         # Compliance workflow
orchestrator.full_security_assessment(host)    # Comprehensive assessment
```

### Vector Store

ChromaDB stores 5 semantic collections:

- **logs_collection** - System and network logs
- **cve_collection** - CVE vulnerability records
- **vuln_collection** - Vulnerability scan results
- **incident_collection** - Historical security incidents
- **policy_collection** - Compliance and policy records

### Evaluation

Run comprehensive evaluation scenarios:

```python
from evaluation.simulator import SecuritySimulator

simulator = SecuritySimulator(orchestrator=orchestrator)
results = simulator.run_full_evaluation()
```

## 🔍 RAG Workflow

All agents follow the RAG (Retrieval-Augmented Generation) pattern:

1. **Formulate Query** - Create semantic search query
2. **Retrieve from Chroma** - Get top-k relevant documents (top_k=5-8)
3. **Analyze Evidence** - Extract insights from retrieved documents
4. **Generate Response** - LLM provides grounded analysis with citations
5. **Maintain Certainty** - Explicitly state if no evidence found

Example:
```python
# RAG query
documents, metadatas = vectorstore.query(
    query_text="Brute force attack patterns",
    collection_name="logs",
    top_k=5
)

# Analyze
for doc in documents[:2]:
    print(f"Evidence: {doc}")

# Generate with MMM (Most Minimal Model)
response = llm.invoke(f"""
Based on these retrieved documents:
{documents}

Assess the threat level and provide recommendations.
CRITICAL: Only cite evidence from the documents above.
If no evidence found, state explicitly.
""")
```

## 📡 API Endpoints

### FastAPI (port 8000)

```
POST   /api/threat/detect           - Detect and analyze threats
POST   /api/vulnerabilities/analyze - Analyze host vulnerabilities
POST   /api/incident/respond        - Generate incident response playbook
POST   /api/compliance/evaluate     - Evaluate security compliance
POST   /api/assessment/full         - Run full security assessment
GET    /api/audit/trail             - Retrieve audit trail
POST   /api/audit/export            - Export audit report
POST   /api/evaluation/run          - Run evaluation suite
GET    /api/health                  - Health check
```

Example requests:

```bash
# Detect threat
curl -X POST http://localhost:8000/api/threat/detect \
  -H "Content-Type: application/json" \
  -d '{"alert":"Brute force attack from 122.161.239.59"}'

# Analyze host
curl -X POST http://localhost:8000/api/vulnerabilities/analyze \
  -H "Content-Type: application/json" \
  -d '{"host":"192.168.1.1"}'

# Handle incident
curl -X POST http://localhost:8000/api/incident/respond \
  -H "Content-Type: application/json" \
  -d '{"threat":"SQL Injection","severity":"HIGH"}'
```

## 🎯 Use Cases

### Scenario 1: Detect & Respond to Brute Force

```python
result = orchestrator.detect_threat(
    "Brute force attack detected on port 22 from 122.161.239.59"
)
# RAG retrieves similar logs and incidents
# LLM assesses severity: CRITICAL
# Generates immediate response actions
```

### Scenario 2: Host Security Assessment

```python
result = orchestrator.analyze_host_vulnerabilities("192.168.1.100")
# Scans vulnerabilities
# Correlates with CVE database
# Identifies remediation priorities
# Checks compliance status
```

### Scenario 3: Incident Playbook Generation

```python
result = orchestrator.handle_incident(
    threat="SQL Injection Attack",
    severity="CRITICAL"
)
# Retrieves historical similar incidents
# Generates step-by-step playbook
# Provides recovery procedures
# Validates recovery checklist
```

## 📋 Audit & Compliance

Every action is logged for full transparency:

```python
# View audit trail
trail = orchestrator.get_audit_trail(last_n=20)

# Export report
orchestrator.export_report(filename="security_audit_2026.json")
```

Report includes:
- Timestamps for all actions
- Details of queries and decisions
- Evidence sourced from vector store
- Confidence scores and explanations

## 🔐 Security Principles

✅ **Evidence-Based** - No fabricated findings; all decisions backed by vector store  
✅ **Explainable** - Complete audit trail and reasoning  
✅ **Grounded** - LLM responses cite specific retrieved documents  
✅ **Transparent** - Explicit uncertainty when evidence insufficient  
✅ **Auditable** - Full action history for compliance  

## 🧪 Testing & Evaluation

```bash
# Run evaluation suite
python -c "
from evaluation.simulator import SecuritySimulator
from orchestrator.supervisor import SecurityOrchestrator

orchestrator = SecurityOrchestrator()
simulator = SecuritySimulator(orchestrator)
results = simulator.run_full_evaluation()
print(f'Pass Rate: {results[\"pass_rate\"]:.1f}%')
"
```

## 📚 Dependencies

- **langchain** - LLM orchestration
- **chromadb** - Vector store
- **pandas** - Data processing
- **fastapi** - REST API
- **streamlit** - Web UI
- **python-dotenv** - Environment config
- **openai** - LLM interface

## 🛠️ Configuration

Edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
BASE_PATH=./cyber_demo
API_PORT=8000
STREAMLIT_PORT=8501
```

## 📝 License

MIT License - Open for research and commercial use

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional security agents
- More vector collections
- Advanced analysis algorithms
- Integration with SIEM platforms
- Machine learning threat scoring

---

**Built with ❤️ for cybersecurity defenders**
