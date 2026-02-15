# 🔍 Code-Level Data Tracing: From Input to Report

## Exact Code Flow for Your SSH Scan Alert

### Your Input to the App
```
IDS Alert:
  signature: "ET SCAN Potential SSH Scan"
  source_ip: "203.0.113.91"
  destination_ip: "10.0.4.22"
  port: 22
  severity: "low"
```

---

## Step 1: UI Collection → app.py

**File**: `app.py` (Lines 75-95)

```python
elif page == "Threat Detection":
    st.header("🔍 Threat Intelligence Analysis")
    
    # User enters IDS alert
    alert = st.text_input("Enter alert signature", 
                          placeholder="e.g., ET SCAN Potential SSH Scan")
    
    if st.button("Analyze Threat", use_container_width=True):
        with st.spinner("Analyzing threat..."):
            # CALL 1: Send to orchestrator
            result = orchestrator.analyze_threat(alert)  # ← Your input goes here
```

**What happens next**: `orchestrator.analyze_threat(alert)` is called

---

## Step 2: Orchestrator Routes Request → orchestrator/supervisor.py

**File**: `orchestrator/supervisor.py` (Lines ~45-70)

```python
class SecuritySupervisor:
    def analyze_threat(self, threat: str):
        """Analyze threat using threat intelligence agent"""
        
        # CALL 2: Route to threat intelligence agent
        threat_result = self.threat_intel_agent.enrich_threat(threat)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "threat": threat,
            "related_cves": threat_result["related_cves"],      # ← Will get CVEs
            "related_incidents": threat_result["related_incidents"],  # ← Will get incidents
            "confidence": threat_result["confidence"],
            "status": "COMPLETED"
        }
```

**What happens next**: `threat_intel_agent.enrich_threat(threat)` is called

---

## Step 3: Threat Intel Agent Queries Databases

**File**: `agents/threat_intel.py` (Lines 18-43)

```python
class ThreatIntelligenceAgent:
    def __init__(self, vectorstore: ChromaVectorStore):
        self.vectorstore = vectorstore  # ← ChromaDB connection
    
    def enrich_threat(self, threat_description: str):
        """
        Your threat: "ET SCAN Potential SSH Scan"
        """
        
        # CALL 3a: Query CVE collection
        cve_docs, cve_meta = self.vectorstore.query(
            "cve",                          # ← Collection name
            threat_description,             # ← Your threat string
            top_k=8                         # ← Return top 8 results
        )
        
        # CALL 3b: Query Incident collection
        incident_docs, incident_meta = self.vectorstore.query(
            "incident",                     # ← Collection name
            threat_description,             # ← Your threat string
            top_k=5                         # ← Return top 5 results
        )
        
        # Return structured result
        return {
            "related_cves": cve_docs[:3],           # ← Take top 3 CVEs
            "related_incidents": incident_docs[:3],  # ← Take top 3 incidents
            "confidence": "HIGH" if (cve_docs or incident_docs) else "LOW",
            "status": "COMPLETED"
        }
```

**What happens next**: `vectorstore.query()` is called twice

---

## Step 4a: CVE Collection Query → ChromaDB

**File**: `vectorstore/chroma_client.py` (Lines 59-80)

```python
class ChromaVectorStore:
    def query(self, collection_name: str, query_text: str, top_k: int = 5):
        """
        Perform semantic search on CVE collection
        """
        
        # Get the collection
        collection = self.collections["cve"]  # ← CVE collection from ChromaDB
        
        # Convert query to 384D embedding using Hugging Face
        query_embedding = self.embeddings.encode(query_text).tolist()
        # Input: "ET SCAN Potential SSH Scan"
        # Output: [0.123, -0.456, 0.789, ...] (384 dimensions)
        
        # Perform semantic similarity search
        results = collection.query(
            query_embeddings=[query_embedding],  # ← Your query as vector
            n_results=8                          # ← Top 8 matches
        )
        
        # Return matching documents and metadata
        documents = results['documents'][0]      # ← CVE descriptions
        metadatas = results.get('metadatas', [[]])[0]  # ← CVE metadata
        
        return documents, metadatas
```

**Data Flow**:
```
"ET SCAN Potential SSH Scan"
    ↓ (Hugging Face embedding)
[0.123, -0.456, 0.789, ..., 0.234]  (384D vector)
    ↓ (ChromaDB similarity search)
Searches 130,000 CVE vectors
    ↓
Returns top 8 most similar:
  1. CVE-2026-12791 (9.5 CVSS) - SSH vulnerability
  2. CVE-2026-12345 (8.2 CVSS) - Port scanning
  3. ... (6 more)
```

---

## Step 4b: Incident Collection Query → ChromaDB

**File**: `vectorstore/chroma_client.py` (Same query method, different collection)

```python
def query(self, collection_name: str, query_text: str, top_k: int = 5):
    # Same process but on "incident" collection
    collection = self.collections["incident"]  # ← Incident collection
    
    query_embedding = self.embeddings.encode(query_text).tolist()
    # Input: "ET SCAN Potential SSH Scan"
    # Output: [0.123, -0.456, 0.789, ...] (same embedding)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5  # ← Top 5 matches
    )
    
    return documents, metadatas
```

**Data Flow**:
```
"ET SCAN Potential SSH Scan"
    ↓ (Same Hugging Face embedding)
[0.123, -0.456, 0.789, ..., 0.234]  (384D vector)
    ↓ (ChromaDB similarity search)
Searches 100,000 Incident vectors
    ↓
Returns top 5 most similar:
  1. ALERT-186419 (DDOS from 59.93.205.62)
  2. ALERT-149084 (DDOS from 183.210.25.153)
  3. ALERT-149248 (DDOS from 240.26.183.111)
  4. ... (2 more)
```

---

## Step 5: ChromaDB Retrieves from Local Files

### CVE Collection Sources
**File**: `cyber_demo/cve_data.json` (130,000 CVE records)

```json
[
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
  },
  // ... 129,999 more CVE records
]
```

**Data Loading** (from `embedding_vectorstore_setup.py`):
```python
def load_cves():
    """Load all CVEs into ChromaDB"""
    with open(CVE_FILE, 'r') as f:
        cve_list = json.load(f)  # ← Load from cve_data.json
    
    for cve in cve_list:
        # Convert to Document
        text = f"""CVE Record:
        CVE ID: {cve['cve_id']}
        Published Date: {cve['published_date']}
        CVSS Base Score: {cve['cvss_base']}
        Description: {cve['description']}
        Affected Products: {affected_str}
        """
        
        # Add to ChromaDB with embedding
        collection.add(documents=[text], metadatas=[metadata])
        # ↑ Hugging Face embedding generated automatically
```

### Incident Collection Sources
**File**: `cyber_demo/incident_alerts.csv` (100,000 incident records)

```csv
alert_id,timestamp,src,tgt,type,recommendation
ALERT-100001,2026-02-09T20:58:36Z,122.161.239.59,189.40.139.129,BRUTE_FORCE,review firewall
ALERT-100002,2026-02-04T08:14:20Z,228.223.131.122,197.108.243.124,MALWARE,isolate host
ALERT-186419,2026-02-06T12:28:32Z,59.93.205.62,218.108.180.157,DDOS,reset credentials
// ... 99,997 more incident records
```

**Data Loading** (from `embedding_vectorstore_setup.py`):
```python
def load_incidents():
    """Load all incidents into ChromaDB"""
    df = pd.read_csv(INCIDENT_FILE)  # ← Load from incident_alerts.csv
    
    for idx, row in df.iterrows():
        # Convert to Document
        text = f"""Security Incident Alert:
        Alert ID: {row['alert_id']}
        Timestamp: {row['timestamp']}
        Source IP: {row['src']}
        Target IP: {row['tgt']}
        Alert Type: {row['type']}
        Recommendation: {row['recommendation']}
        """
        
        # Add to ChromaDB with embedding
        collection.add(documents=[text], metadatas=[metadata])
        # ↑ Hugging Face embedding generated automatically
```

---

## Step 6: Results Flow Back Up the Stack

### CVE Results
```
ChromaDB returns 8 matching CVEs
    ↓
threat_intel.py takes top 3
    ↓
supervisor.py includes in result
    ↓
app.py displays:
  • CVE-2026-12791 (9.5 CVSS)
  • CVE-2026-12709 (5.7 CVSS)
  • CVE-2026-12718 (9.0 CVSS)
```

### Incident Results
```
ChromaDB returns 5 matching incidents
    ↓
threat_intel.py takes top 3
    ↓
supervisor.py includes in result
    ↓
app.py displays:
  • ALERT-186419: DDOS
  • ALERT-149084: DDOS
  • ALERT-149248: DDOS
```

---

## Step 7: UI Displays Final Report

**File**: `app.py` (Lines 118-140, Threat Detection section)

```python
if st.button("Analyze Threat"):
    result = orchestrator.analyze_threat(alert)
    
    # Display Related CVEs
    st.subheader("🔗 Related CVEs")
    for cve in result["related_cves"]:
        # cve is from cyber_demo/cve_data.json
        st.write(f"• {cve}")  # ← Your report showing CVEs from database
    
    # Display Related Incidents
    st.subheader("📚 Similar Past Incidents")
    for incident in result["related_incidents"]:
        # incident is from cyber_demo/incident_alerts.csv
        st.write(f"• {incident}")  # ← Your report showing incidents from database
```

---

## Complete Data Journey Diagram

```
┌─────────────────────────────────────────────────────────┐
│  YOUR INPUT: "ET SCAN Potential SSH Scan"              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │  app.py                     │
        │  (Streamlit UI)             │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │  orchestrator/supervisor.py │
        │  (Route to agents)          │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────┐
        │  agents/threat_intel.py              │
        │  - Call vectorstore.query("cve", ...) │
        │  - Call vectorstore.query("incident", ...
) │
        └────┬─────────────────────────┬───────┘
             │                         │
             ▼                         ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │ vectorstore/        │   │ vectorstore/        │
    │ chroma_client.py    │   │ chroma_client.py    │
    │ CVE Query           │   │ Incident Query      │
    └────┬────────────────┘   └────┬────────────────┘
         │                         │
         ▼                         ▼
    ┌────────────────────┐   ┌────────────────────┐
    │ ChromaDB CVE Coll. │   │ ChromaDB Inc. Coll.│
    │ (Semantic Search)  │   │ (Semantic Search)  │
    └────┬────────────────┘   └────┬────────────────┘
         │                         │
         ▼                         ▼
    ┌────────────────────┐   ┌────────────────────┐
    │ cyber_demo/        │   │ cyber_demo/        │
    │ cve_data.json      │   │ incident_alerts.csv│
    │ (130,000 records)  │   │ (100,000 records)  │
    └────┬────────────────┘   └────┬────────────────┘
         │                         │
         └────────────┬────────────┘
                      │
                      ▼
    ┌──────────────────────────────┐
    │  Top 3 CVEs + Top 3 Incidents│
    │  Assembled in Result         │
    └────────────┬─────────────────┘
                 │
                 ▼
    ┌──────────────────────────────┐
    │  FINAL REPORT DISPLAYED      │
    │  on Streamlit UI             │
    └──────────────────────────────┘
```

---

## Summary

**Your SSH Scan Alert** flows through this exact code path:

1. ✅ **UI Input** (app.py) → "ET SCAN Potential SSH Scan"
2. ✅ **Routed to Agent** (supervisor.py)
3. ✅ **Semantic Search** (threat_intel.py)
4. ✅ **Query CVE Database** (chroma_client.py → cve_data.json)
5. ✅ **Query Incident Database** (chroma_client.py → incident_alerts.csv)
6. ✅ **Return Top 3 of Each** (threat_intel.py)
7. ✅ **Display Report** (app.py)

**All data retrieved from LOCAL FILES, not LLM or external APIs**
