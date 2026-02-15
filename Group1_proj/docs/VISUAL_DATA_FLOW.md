# 📊 Visual Data Flow Diagram

## Your SSH Scan Alert → Threat Intelligence Report

```
╔════════════════════════════════════════════════════════════════╗
║  INPUT: IDS ALERT - ET SCAN Potential SSH Scan                ║
║  Port: 22 | Severity: low                                      ║
╚════════════════════════════════════════════════════════════════╝
                              │
                              ▼
                    ┌─────────────────────┐
                    │  STREAMLIT UI       │
                    │  (app.py)           │
                    │  Takes your input   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │  ORCHESTRATOR           │
                    │  (supervisor.py)        │
                    │  Routes to agents       │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────────┐
                    │  THREAT INTEL AGENT         │
                    │  (agents/threat_intel.py)   │
                    │  Queries both databases     │
                    └──┬──────────────────────┬──┘
                       │                      │
            ┌──────────┘                      └──────────┐
            │                                            │
            ▼                                            ▼
   ┌────────────────────────┐              ┌────────────────────────┐
   │ QUERY: "CVE Database"  │              │ QUERY: Incidents DB    │
   │ Collection: "cve"      │              │ Collection: "incident" │
   │ ChromaDB Semantic      │              │ ChromaDB Semantic      │
   │ Search                 │              │ Search                 │
   │ Top 8 Results          │              │ Top 5 Results          │
   └────────────┬───────────┘              └────────────┬───────────┘
                │                                       │
                ▼                                       ▼
   ┌──────────────────────────────┐    ┌──────────────────────────────┐
   │ LOCAL FILE:                  │    │ LOCAL FILE:                  │
   │ cyber_demo/cve_data.json     │    │ cyber_demo/incident_*csv     │
   │ ├─ 130,000 CVE records       │    │ ├─ 100,000 incident records  │
   │ ├─ Sample CVEs (CVE-2026-*)  │    │ ├─ Alert types: DDOS, PORT_  │
   │ ├─ CVSS scores               │    │ │  SCAN, BRUTE_FORCE, etc.   │
   │ ├─ Affected products         │    │ ├─ Source/Target IPs         │
   │ └─ Published dates           │    │ ├─ Timestamps               │
   │                              │    │ └─ Recommendations           │
   │ SELECTED FOR YOUR REPORT:    │    │                              │
   │ • CVE-2026-12791 (9.5)       │    │ SELECTED FOR YOUR REPORT:    │
   │ • CVE-2026-12709 (5.7)       │    │ • ALERT-186419 (DDOS)        │
   │ • CVE-2026-12718 (9.0)       │    │ • ALERT-149084 (DDOS)        │
   └──────────────┬───────────────┘    │ • ALERT-149248 (DDOS)        │
                  │                     └──────────────┬───────────────┘
                  │                                    │
                  └────────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────────┐
                    │  COMBINE & FORMAT RESULTS      │
                    │  (threat_intel.py)             │
                    │  Return:                       │
                    │  - Top 3 CVEs                  │
                    │  - Top 3 Incidents             │
                    │  - Confidence Level            │
                    │  - Timestamp                   │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  DISPLAY IN STREAMLIT UI       │
                    │  (app.py)                      │
                    │  Format for readability        │
                    │  Show all details              │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════╗
║  OUTPUT: THREAT INTELLIGENCE REPORT                           ║
║                                                                ║
║  Related CVEs:                                                 ║
║  • CVE-2026-12791 (9.5) - SSH vulnerability                  ║
║  • CVE-2026-12709 (5.7) - Related vulnerability              ║
║  • CVE-2026-12718 (9.0) - Port scanning                      ║
║                                                                ║
║  Similar Past Incidents:                                      ║
║  • Alert: ALERT-186419 (DDOS)                                ║
║  • Alert: ALERT-149084 (DDOS)                                ║
║  • Alert: ALERT-149248 (DDOS)                                ║
║                                                                ║
║  Confidence: HIGH                                              ║
║  Status: COMPLETED                                             ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Data Source Breakdown

```
┌─────────────────────────────────────────────────────────┐
│           WHERE EACH PIECE OF DATA COMES FROM           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ RELATED CVEs:                                           │
│ └─→ Source: cyber_demo/cve_data.json                   │
│     └─→ Retrieved via: ChromaDB semantic search        │
│         └─→ Method: Vector similarity (embeddings)     │
│             └─→ Returns: Top 3 matching CVEs           │
│                                                         │
│ SIMILAR INCIDENTS:                                      │
│ └─→ Source: cyber_demo/incident_alerts.csv            │
│     └─→ Retrieved via: ChromaDB semantic search        │
│         └─→ Method: Vector similarity (embeddings)     │
│             └─→ Returns: Top 3 matching incidents      │
│                                                         │
│ CVE DETAILS (CVSS, Date, Affected Products):           │
│ └─→ Source: cyber_demo/cve_data.json structure        │
│     └─→ Formatted by: threat_intel.py                 │
│         └─→ Displayed by: app.py                       │
│                                                         │
│ INCIDENT DETAILS (Alert ID, Type, Recommendation):     │
│ └─→ Source: cyber_demo/incident_alerts.csv structure  │
│     └─→ Formatted by: threat_intel.py                 │
│         └─→ Displayed by: app.py                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack Used

```
┌──────────────────────────────────────────────┐
│         TECHNOLOGY COMPONENTS               │
├──────────────────────────────────────────────┤
│                                              │
│ INPUT LAYER:                                 │
│ └─ Streamlit (st.text_input)                │
│                                              │
│ ORCHESTRATION LAYER:                         │
│ └─ SecuritySupervisor (supervisor.py)       │
│                                              │
│ AGENT LAYER:                                 │
│ └─ ThreatIntelligenceAgent (threat_intel.py)│
│                                              │
│ VECTOR SEARCH LAYER:                         │
│ └─ ChromaVectorStore (chroma_client.py)     │
│    └─ Embedding: Hugging Face (free)       │
│    └─ Database: ChromaDB (local)            │
│                                              │
│ DATA LAYER:                                  │
│ ├─ cve_data.json (130K CVEs)               │
│ ├─ incident_alerts.csv (100K incidents)    │
│ ├─ syslog_large.csv (logs)                 │
│ ├─ vuln_scan.csv (vulnerabilities)         │
│ └─ policy_checks.csv (policies)            │
│                                              │
│ OUTPUT LAYER:                                │
│ └─ Streamlit UI (formatted report)          │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Request → Response Timeline

```
┌─────────────────────────────────────────────────────────┐
│         HOW YOUR REQUEST IS PROCESSED                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  T+0ms   User enters threat (SSH scan) in UI            │
│          ↓                                               │
│  T+1ms   Orchestrator routes to Threat Intel Agent     │
│          ↓                                               │
│  T+5ms   Agent queries CVE database (semantic)         │
│          ↓                                               │
│  T+10ms  ChromaDB converts query to 384D vector        │
│          ↓                                               │
│  T+15ms  Searches 130,000 CVE vectors for matches     │
│          ↓                                               │
│  T+20ms  Agent queries incident database (semantic)    │
│          ↓                                               │
│  T+25ms  ChromaDB searches 100,000 incident vectors    │
│          ↓                                               │
│  T+30ms  Combines top 3 CVEs + top 3 incidents        │
│          ↓                                               │
│  T+35ms  Formats results with metadata                  │
│          ↓                                               │
│  T+40ms  Returns to UI for display                      │
│          ↓                                               │
│  T+45ms  Streamlit renders final report                │
│                                                          │
│  ✅ TOTAL TIME: ~50ms (completely local, no network)   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## No External Calls - Fully Local

```
                    YOUR APPLICATION
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
            LOCAL FILES            LOCAL VECTOR DB
            ├─ cve_data.json        ├─ ChromaDB
            ├─ incident_*.csv       ├─ Embeddings
            ├─ syslog_*.csv         └─ Collections
            ├─ vuln_*.csv
            └─ policy_*.csv
                │                       │
                └───────────┬───────────┘
                            │
                    NO NETWORK CALLS
                    NO API REQUESTS
                    NO LLM USAGE
                    NO EXTERNAL DATA
                            │
                    100% LOCAL PROCESSING
```

---

## Data Flow Summary

```
INPUT
  ↓
Query CVE Collection          Query Incident Collection
  ↓                           ↓
Search 130,000 CVE records    Search 100,000 incidents
  ↓                           ↓
Get top 8 matches             Get top 5 matches
  ↓                           ↓
Take top 3 CVEs               Take top 3 incidents
  ↓                           ↓
  └─────────────┬─────────────┘
                ▼
        Combine & Format
                ▼
         Display Report
```

---

**Key Insight**: Every piece of data in your threat intelligence report comes from local files stored in `cyber_demo/` and searched through ChromaDB. No external data, no LLM, no API calls.
