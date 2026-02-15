# 📊 Threat Intelligence Data Sources - Complete Documentation

## Overview
The threat intelligence report you received is generated from **LOCAL DATABASE (ChromaDB Vector Store)**, not from an LLM or external APIs. Here's the complete breakdown:

---

## Data Flow Architecture

```
┌─────────────────────────────────┐
│   Your IDS Alert Input          │
│  (SSH Scan: Port 22)            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Threat Intelligence Agent      │
│  (agents/threat_intel.py)       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  ChromaDB Vector Store          │
│  (Semantic Search Query)        │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┬────────────┬─────────────┐
    ▼                 ▼            ▼             ▼
  CVEs         Incidents       Logs          Policies
  (JSON)       (CSV)          (CSV)          (CSV)
```

---

## Data Sources Breakdown

### 1️⃣ **Related CVEs** - SOURCE: LOCAL JSON DATABASE
**File Location**: `cyber_demo/cve_data.json`

**Data Structure**:
```json
{
  "cve_id": "CVE-2026-12791",
  "published_date": "2026-02-13",
  "cvss_base": 9.5,
  "description": "Sample vulnerability #12791",
  "affected_products": [
    {
      "vendor": "Vendor56",
      "product": "Prod370",
      "version": "4.8"
    }
  ]
}
```

**How It's Retrieved**:
1. Your threat input: `"ET SCAN Potential SSH Scan"`
2. **Threat Intelligence Agent** (threat_intel.py, line 26):
   ```python
   cve_docs, cve_meta = self.vectorstore.query("cve", threat_description, top_k=8)
   ```
3. **ChromaDB performs semantic search** using Hugging Face embeddings
4. Matches your SSH scan threat against 130,000+ CVE records in cve_data.json
5. Returns top 3 most relevant CVEs

**Important**: This is **SAMPLE DATA** (all 130,000 CVEs are synthetic with pattern: CVE-2026-XXXXX)

---

### 2️⃣ **Similar Past Incidents** - SOURCE: LOCAL CSV DATABASE
**File Location**: `cyber_demo/incident_alerts.csv`

**Data Structure** (CSV):
```
alert_id,timestamp,src,tgt,type,recommendation
ALERT-186419,2026-02-06T12:28:32Z,59.93.205.62,218.108.180.157,DDOS,reset credentials
ALERT-149084,2026-02-01T15:42:22Z,183.210.25.153,177.98.97.90,DDOS,reset credentials
ALERT-149248,2026-02-09T11:41:31Z,240.26.183.111,40.85.168.126,DDOS,reset credentials
```

**How It's Retrieved**:
1. **Threat Intelligence Agent** (threat_intel.py, line 27):
   ```python
   incident_docs, incident_meta = self.vectorstore.query("incident", threat_description, top_k=5)
   ```
2. **ChromaDB performs semantic search** on 100,000+ historical incidents
3. Matches your SSH scan threat against incident types (BRUTE_FORCE, MALWARE, DDOS, PORT_SCAN, etc.)
4. Returns top 3 most relevant past incidents

**Note**: The incidents show different attack types (DDOS) because semantic search finds related security threats, not exact matches

---

## Complete Technology Stack

### 📚 Vector Database: ChromaDB
**File**: `vectorstore/chroma_client.py`
- **Purpose**: Semantic search engine for threat intelligence
- **Location**: `cyber_vector_db/` (persisted on disk)
- **Embeddings**: Hugging Face `all-MiniLM-L6-v2` (free, open-source)
- **Collections**:
  - ✅ `cve_collection` - 130,000 CVE records
  - ✅ `incident_collection` - 100,000 incident alerts
  - ✅ `logs_collection` - System logs
  - ✅ `vuln_collection` - Vulnerability scans
  - ✅ `policy_collection` - Compliance policies

### 🔍 Semantic Search Process
```python
# From threat_intel.py
def enrich_threat(self, threat_description: str):
    # 1. Query CVE collection semantically
    cve_docs, cve_meta = self.vectorstore.query("cve", threat_description, top_k=8)
    
    # 2. Query incident collection semantically
    incident_docs, incident_meta = self.vectorstore.query("incident", threat_description, top_k=5)
    
    # 3. Return enriched threat data
    return {
        "related_cves": cve_docs[:3],        # Top 3 CVEs
        "related_incidents": incident_docs[:3],  # Top 3 Incidents
        "confidence": "HIGH",
        "status": "COMPLETED"
    }
```

### ⚡ Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384D vector
- **Cost**: FREE (no API calls, no LLM usage)
- **Speed**: Very fast (~milliseconds per query)

---

## Step-by-Step: How Your Alert Became a Report

### Your Input
```
IDS ALERT:
- Signature: ET SCAN Potential SSH Scan
- Source IP: 203.0.113.91
- Destination IP: 10.0.4.22
- Port: 22
- Severity: low
```

### Processing Steps

**Step 1: Input Normalization** (app.py)
```
Threat = "ET SCAN Potential SSH Scan"
```

**Step 2: Semantic Search in CVE Database**
```
Query: "ET SCAN Potential SSH Scan"
↓
ChromaDB converts to 384D embedding
↓
Searches 130,000 CVE records
↓
Returns top 3 matching CVEs
```

**Step 3: Semantic Search in Incident Database**
```
Query: "ET SCAN Potential SSH Scan"
↓
ChromaDB converts to 384D embedding
↓
Searches 100,000 incident records
↓
Returns top 3 matching incidents
```

**Step 4: Format and Display**
```
Combine results into user-friendly report:
- Related CVEs (from cve_data.json)
- Similar Past Incidents (from incident_alerts.csv)
- Timestamp
- Confidence level
```

---

## Data Source Mapping

| Report Section | Data Source | File | Records | Search Method |
|---|---|---|---|---|
| **Related CVEs** | Local JSON DB | `cyber_demo/cve_data.json` | 130,000 synthetic CVEs | Semantic search |
| **Similar Incidents** | Local CSV DB | `cyber_demo/incident_alerts.csv` | 100,000 alerts | Semantic search |
| **CVE Details** | JSON structure | Embedded in CVE records | Metadata | Direct mapping |
| **Incident Types** | CSV columns | Alert types: DDOS, BRUTE_FORCE, etc | CSV rows | Regex + semantic |

---

## Key Facts About Data Sources

### ✅ What You're Getting
1. **Local Data** - All data stored in `cyber_demo/` directory on your machine
2. **Semantic Search** - Not keyword matching, uses AI embeddings for relevance
3. **Synthetic Data** - Sample/demo data for testing (not real CVEs or incidents)
4. **Zero LLM Usage** - No ChatGPT, no external APIs, no costs
5. **Instant Response** - Queries completed in milliseconds (no network latency)

### ⚠️ Important Notes
- This is **DEMONSTRATION DATA** (CVE-2026-XXXXX prefix indicates synthetic data)
- Real deployment would integrate with:
  - Official CVE databases (NVD, MITRE)
  - Real incident management systems
  - Threat feeds (Shodan, Censys, etc.)
  - SOAR platforms

---

## Architecture Diagram: Data Journey

```
Your IDS Alert
    │
    ▼
┌─────────────────────────────────────┐
│  app.py (Streamlit UI)              │
│  - Displays threat                  │
│  - Calls orchestrator               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  orchestrator/supervisor.py         │
│  - Coordinates agents               │
│  - Calls threat_intel agent         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  agents/threat_intel.py             │
│  - Semantic search queries          │
│  - Assembles report                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  vectorstore/chroma_client.py       │
│  - Converts text to 384D embeddings │
│  - Searches 5 collections           │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ CVE Collection   │  │ Incident Coll.   │
│ (cve_data.json)  │  │ (incident_*.csv) │
│ 130,000 records  │  │ 100,000 records  │
└──────────────────┘  └──────────────────┘
    │                     │
    └──────────┬──────────┘
               ▼
    ┌─────────────────────┐
    │ Results Combined    │
    │ & Formatted         │
    └──────────┬──────────┘
               ▼
    Your Threat Intelligence Report
```

---

## Code References

### Threat Intel Agent Query Logic
**File**: `agents/threat_intel.py` (Lines 18-43)
```python
def enrich_threat(self, threat_description: str) -> Dict[str, Any]:
    # Query CVE collection with semantic search
    cve_docs, cve_meta = self.vectorstore.query("cve", threat_description, top_k=8)
    
    # Query incident collection with semantic search
    incident_docs, incident_meta = self.vectorstore.query("incident", threat_description, top_k=5)
    
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "agent": self.name,
        "threat": threat_description,
        "related_cves": cve_docs[:3],           # ← Top 3 CVEs shown
        "related_incidents": incident_docs[:3], # ← Top 3 Incidents shown
        "confidence": "HIGH" if (cve_docs or incident_docs) else "LOW",
        "status": "COMPLETED"
    }
```

### ChromaDB Search Implementation
**File**: `vectorstore/chroma_client.py` (Lines 59-80)
```python
def query(self, collection_name: str, query_text: str, top_k: int = 5):
    collection = self.collections[collection_name]
    
    # Convert query text to 384D embedding using Hugging Face
    query_embedding = self.embeddings.encode(query_text).tolist()
    
    # Search ChromaDB for top_k similar results
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    
    return results['documents'][0], results.get('metadatas', [[]])[0]
```

### Data Loading Process
**File**: `embedding_vectorstore_setup.py`
```python
# Load 130,000 CVEs from JSON
def load_cves():
    with open(CVE_FILE, 'r') as f:
        cve_list = json.load(f)  # ← From cyber_demo/cve_data.json
    # Convert to ChromaDB documents with embeddings

# Load 100,000 incidents from CSV
def load_incidents():
    df = pd.read_csv(INCIDENT_FILE)  # ← From cyber_demo/incident_alerts.csv
    # Convert to ChromaDB documents with embeddings
```

---

## Summary: Your Answer

### Where does threat intelligence come from?
**✅ FROM LOCAL DATABASE** (not LLM or external APIs)

### Specific Sources:
1. **CVEs** → `cyber_demo/cve_data.json` (130,000 synthetic records)
2. **Incidents** → `cyber_demo/incident_alerts.csv` (100,000 synthetic records)

### Search Method:
**Semantic Search** via ChromaDB vector database using Hugging Face embeddings (not keyword matching)

### Processing Flow:
```
Your Alert → Threat Intel Agent → ChromaDB Query → Local Database
                                       ↓
                            Semantic Matching (embeddings)
                                       ↓
                            Top 3 CVEs + Top 3 Incidents
```

### Why This Design:
- ⚡ **Fast**: No network calls, millisecond response times
- 💰 **Free**: No LLM API costs, uses open-source Hugging Face models
- 🔒 **Private**: All data stored locally, no cloud dependency
- 📊 **Scalable**: Can handle millions of records with semantic search
- 🧠 **Smart**: Uses AI embeddings for relevance, not just keywords

---

**Last Updated**: 2025-02-15  
**Data Type**: Demonstration/Sample Data (not production)  
**Status**: ✅ Fully Documented
