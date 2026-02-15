# 🎯 Quick Reference: Where Threat Intelligence Data Comes From

## TL;DR - Direct Answer to Your Question

**Q: How is threat intelligence retrieved - from database or LLM?**

**A: FROM LOCAL DATABASE (Not LLM)**

```
Your IDS Alert
    ↓
Semantic Search
    ↓
ChromaDB Vector Store
    ↓
┌─────────────────────┐
│ CVE Data (JSON)     │ → Returns 3 matching CVEs
│ Incident Data (CSV) │ → Returns 3 matching Incidents
└─────────────────────┘
    ↓
Your Report
```

---

## The Complete Picture

### Your Input Example
```
ET SCAN Potential SSH Scan
├─ Source: 203.0.113.91
├─ Destination: 10.0.4.22
├─ Port: 22
└─ Severity: low
```

### Data Retrieved From

#### 1. **CVE Data** 📋
- **Source File**: `cyber_demo/cve_data.json`
- **Total Records**: 130,000 synthetic CVEs
- **Search Type**: Semantic similarity search
- **Result**: Top 3 most relevant CVEs
- **Example Result**:
  ```
  CVE-2026-12791 (CVSS: 9.5) - SSH vulnerability
  CVE-2026-12709 (CVSS: 5.7) - Related vulnerability
  CVE-2026-12718 (CVSS: 9.0) - Port scanning vulnerability
  ```

#### 2. **Incident Data** 📊
- **Source File**: `cyber_demo/incident_alerts.csv`
- **Total Records**: 100,000 historical incidents
- **Search Type**: Semantic similarity search
- **Result**: Top 3 most relevant past incidents
- **Example Result**:
  ```
  ALERT-186419: DDOS from 59.93.205.62
  ALERT-149084: DDOS from 183.210.25.153
  ALERT-149248: DDOS from 240.26.183.111
  ```

---

## Technology Stack

### Vector Database
```
ChromaDB (Local Vector Store)
├─ Collection 1: CVE Database (130K records)
├─ Collection 2: Incident Database (100K records)
├─ Collection 3: Logs Database
├─ Collection 4: Vulnerability Database
└─ Collection 5: Policy Database
```

### Embedding Engine
```
Hugging Face: all-MiniLM-L6-v2
├─ Converts text to 384D vectors
├─ Uses semantic understanding
├─ Zero cost (open-source)
└─ Local processing (no API calls)
```

### Search Method
```
NOT: Keyword matching
YES: Semantic similarity
    ├─ Converts query to 384D vector
    ├─ Compares to all database vectors
    ├─ Returns most similar matches
    └─ Top results shown in report
```

---

## File Structure

```
cyberSec_ai/
├── cyber_demo/
│   ├── cve_data.json          ← CVE Database (130,000 records)
│   ├── incident_alerts.csv    ← Incident Database (100,000 records)
│   ├── syslog_large.csv       ← Log Database
│   ├── vuln_scan.csv          ← Vulnerability Database
│   └── policy_checks.csv      ← Policy Database
│
├── cyber_vector_db/           ← ChromaDB Vector Store (persisted)
│   └── [Vector embeddings stored here]
│
├── vectorstore/
│   └── chroma_client.py       ← Search engine interface
│
└── agents/
    └── threat_intel.py        ← Agent that queries data
```

---

## How Data Gets Into the Report

### Step 1: Input Processing
```python
threat_description = "ET SCAN Potential SSH Scan"
```

### Step 2: Agent Query (threat_intel.py)
```python
cve_docs, _ = vectorstore.query("cve", threat_description, top_k=8)
incident_docs, _ = vectorstore.query("incident", threat_description, top_k=5)
```

### Step 3: ChromaDB Search
```
Query: "ET SCAN Potential SSH Scan"
    ↓
Convert to 384D embedding
    ↓
Search all 130,000 CVE embeddings
    ↓
Return top 8 most similar
    ↓
Also search 100,000 incidents
    ↓
Return top 5 most similar
```

### Step 4: Report Assembly
```python
return {
    "related_cves": cve_docs[:3],        # Take top 3 CVEs
    "related_incidents": incident_docs[:3],  # Take top 3 incidents
    "confidence": "HIGH",
    "status": "COMPLETED"
}
```

### Step 5: UI Display
- Format results as readable report
- Show CVE details, incident history, recommendations
- Display severity scores, affected products, etc.

---

## Data Sources Comparison

| Aspect | Details |
|--------|---------|
| **Source Type** | Local File System (not external API) |
| **CVE Data** | `cyber_demo/cve_data.json` |
| **Incident Data** | `cyber_demo/incident_alerts.csv` |
| **Storage** | ChromaDB vector database |
| **Search Method** | Semantic similarity (embeddings) |
| **Embedding Model** | Hugging Face free model |
| **Update Frequency** | On app startup (from files) |
| **Response Time** | Milliseconds (no network latency) |
| **Cost** | Free (no API calls) |
| **Data Type** | Demonstration/Sample (synthetic) |

---

## Key Points

### ✅ This System Uses
- **Local databases** (JSON + CSV files)
- **Vector search** (semantic similarity)
- **Free embeddings** (Hugging Face)
- **In-memory storage** (ChromaDB)

### ❌ This System Does NOT Use
- ChatGPT or OpenAI LLM
- External APIs or cloud services
- Keyword-based matching
- Real CVE/incident data (it's sample data)

### 🔧 You Can Change Data By
1. Editing `cyber_demo/cve_data.json`
2. Editing `cyber_demo/incident_alerts.csv`
3. Restarting the app
4. New data automatically indexed into ChromaDB

---

## Real-World Production Integration

To replace sample data with real data:

```python
# Instead of cve_data.json (sample), could integrate:
- NIST National Vulnerability Database (NVD)
- CVE Details API
- Shodan threat feed
- MITRE CVE Database

# Instead of incident_alerts.csv (sample), could integrate:
- SIEM platforms (Splunk, ELK Stack)
- Incident response systems
- Threat intelligence platforms
- Real-time log aggregators
```

---

## Summary Table

| Component | Source | Type | Records | Purpose |
|-----------|--------|------|---------|---------|
| **CVEs** | cyber_demo/cve_data.json | JSON | 130,000 | Vulnerability lookup |
| **Incidents** | cyber_demo/incident_alerts.csv | CSV | 100,000 | Historical context |
| **Embeddings** | Hugging Face | Model | 384D | Semantic search |
| **Storage** | cyber_vector_db/ | ChromaDB | Indexed | Fast retrieval |
| **Search** | Semantic | Algorithm | N/A | Relevance matching |

---

**Answer**: All threat intelligence is retrieved from your **LOCAL DATABASE**, specifically:
- CVEs from `cyber_demo/cve_data.json`
- Incidents from `cyber_demo/incident_alerts.csv`
- Searched using ChromaDB with Hugging Face embeddings
- **No LLM, no external APIs, fully local processing**
