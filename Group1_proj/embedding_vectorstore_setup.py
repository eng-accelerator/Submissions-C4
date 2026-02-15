import os
import json
import pandas as pd
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
#from langchain_chroma import Chroma

# Load environment variables
print("[*] Loading environment variables...")
load_dotenv()

print("[✓] Environment variables loaded")

# ===== File Paths =====
BASE_PATH = os.getenv("BASE_PATH", "./cyber_demo")
print(f"[*] Using data path: {BASE_PATH}")

SYSLOG_FILE = f"{BASE_PATH}/syslog_large.csv"
CVE_FILE = f"{BASE_PATH}/cve_data.json"
VULN_FILE = f"{BASE_PATH}/vuln_scan.csv"
INCIDENT_FILE = f"{BASE_PATH}/incident_alerts.csv"
POLICY_FILE = f"{BASE_PATH}/policy_checks.csv"

# Verify files exist
print(f"[*] Verifying data files...")
required_files = [SYSLOG_FILE, CVE_FILE, VULN_FILE, INCIDENT_FILE, POLICY_FILE]
for file_path in required_files:
    if not os.path.exists(file_path):
        print(f"  [!] Optional file not found: {file_path}")
    else:
        print(f"  [✓] Found: {os.path.basename(file_path)}")
print("[✓] Data files verified")

# ===== Embedding Model (Free Hugging Face - Zero Cost) =====
print("[*] Loading free Hugging Face embedding model (all-MiniLM-L6-v2)...")
embeddings = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dimensional, free, fast
print("[✓] Embeddings model loaded (dimension: 384)")

# ===== Helper Function =====
def load_syslogs():
    print("  [*] Loading syslogs...")
    docs = []
    df = pd.read_csv(SYSLOG_FILE)
    for idx, row in df.iterrows():
        text = f"""Syslog Event:
        Timestamp: {row['timestamp']}
        Host: {row['host']}
        Source IP: {row['src_ip']}
        Destination IP: {row['dst_ip']}
        Protocol: {row['protocol']}
        Severity: {row['severity']}
        Action: {row['action']}
        Event: {row['event']}
        """
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "type": "syslog",
                    "host": row["host"],
                    "severity": row["severity"],
                    "action": row["action"]
                }
            )
        )
        if (idx + 1) % 50000 == 0:
            print(f"    [*] Processed {idx + 1} syslog records...")
    print(f"  [✓] Loaded {len(docs)} syslog documents")
    return docs


def load_cves():
    print("  [*] Loading CVE records...")
    docs = []
    with open(CVE_FILE, 'r') as f:
        cve_list = json.load(f)
    
    for idx, cve in enumerate(cve_list):
        affected_str = "; ".join(
            [f"{prod['vendor']} {prod['product']} v{prod['version']}" 
             for prod in cve.get('affected_products', [])]
        )
        text = f"""CVE Record:
        CVE ID: {cve['cve_id']}
        Published Date: {cve['published_date']}
        CVSS Base Score: {cve['cvss_base']}
        Description: {cve['description']}
        Affected Products: {affected_str}
        """
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "type": "cve",
                    "cve_id": cve["cve_id"],
                    "cvss_score": str(cve["cvss_base"])
                }
            )
        )
        if (idx + 1) % 10000 == 0:
            print(f"    [*] Processed {idx + 1} CVE records...")
    print(f"  [✓] Loaded {len(docs)} CVE documents")
    return docs


def load_vulnerabilities():
    print("  [*] Loading vulnerability scan results...")
    df = pd.read_csv(VULN_FILE)
    docs = []
    for idx, row in df.iterrows():
        text = f"""Vulnerability Scan Result:
        Issue ID: {row['issue_id']}
        Host: {row['host']}
        Severity: {row['severity']}
        Issue Type: {row['issue']}
        Finding: {row['finding']}
        Remediation: {row['remediation']}
        """
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "type": "vulnerability",
                    "host": row["host"],
                    "severity": row["severity"],
                    "issue_id": row["issue_id"]
                }
            )
        )
        if (idx + 1) % 5000 == 0:
            print(f"    [*] Processed {idx + 1} vulnerability records...")
    print(f"  [✓] Loaded {len(docs)} vulnerability documents")
    return docs


def load_incidents():
    print("  [*] Loading incident alerts...")
    df = pd.read_csv(INCIDENT_FILE)
    docs = []
    for idx, row in df.iterrows():
        text = f"""Security Incident Alert:
        Alert ID: {row['alert_id']}
        Timestamp: {row['timestamp']}
        Source IP: {row['src']}
        Target IP: {row['tgt']}
        Alert Type: {row['type']}
        Recommendation: {row['recommendation']}
        """
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "type": "incident",
                    "alert_id": row["alert_id"],
                    "alert_type": row["type"]
                }
            )
        )
        if (idx + 1) % 10000 == 0:
            print(f"    [*] Processed {idx + 1} incident records...")
    print(f"  [✓] Loaded {len(docs)} incident documents")
    return docs


def load_policies():
    print("  [*] Loading policy check results...")
    df = pd.read_csv(POLICY_FILE)
    docs = []
    for idx, row in df.iterrows():
        text = f"""Policy Compliance Check:
        Host: {row['host']}
        Policy ID: {row['policy_id']}
        Standard: {row['standard']}
        Status: {row['status']}
        Detail: {row['detail']}
        """
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "type": "policy",
                    "host": row["host"],
                    "standard": row["standard"],
                    "status": row["status"]
                }
            )
        )
        if (idx + 1) % 2000 == 0:
            print(f"    [*] Processed {idx + 1} policy records...")
    print(f"  [✓] Loaded {len(docs)} policy documents")
    return docs


# ===== Load All Documents =====
print("\n[*] Loading all datasets...")

documents = []
documents.extend(load_cves())
documents.extend(load_incidents())
documents.extend(load_vulnerabilities())
documents.extend(load_policies())
# Note: Syslogs are very large (500k+ records), add if memory permits
# documents.extend(load_syslogs())

print(f"\n[✓] Total documents loaded: {len(documents)}")

# ===== Create Vector Store =====
print("\n[*] Indexing documents into Chroma collections (this may take a while)...")

# Initialize Chroma client for collection operations
base_chroma = Chroma(persist_directory="./cyber_vector_db")

collections = {
    "logs": base_chroma._client.get_or_create_collection(name="logs_collection"),
    "cve": base_chroma._client.get_or_create_collection(name="cve_collection"),
    "vuln": base_chroma._client.get_or_create_collection(name="vuln_collection"),
    "incident": base_chroma._client.get_or_create_collection(name="incident_collection"),
    "policy": base_chroma._client.get_or_create_collection(name="policy_collection"),
}


def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# Map loaded documents to collections (do not include syslogs by default)
dataset_map = {
    "cve": load_cves(),
    "incident": load_incidents(),
    "vuln": load_vulnerabilities(),
    "policy": load_policies(),
    # Uncomment to include large syslogs (may require lots of memory/time)
    # "logs": load_syslogs(),
}

for col_name, docs in dataset_map.items():
    coll = collections.get(col_name)
    if not coll:
        print(f"  [!] Collection object for {col_name} missing, skipping")
        continue

    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]

    batch_size = 2000 if col_name == "cve" else 1000
    total = len(texts)
    print(f"\n  [*] Indexing {total} documents into '{col_name}' collection in batches of {batch_size}...")

    for batch_idx, text_batch in enumerate(chunk_list(texts, batch_size)):
        meta_batch = metadatas[batch_idx * batch_size : batch_idx * batch_size + len(text_batch)]

        # Compute embeddings for the batch using sentence-transformers
        vectors = embeddings.encode(text_batch).tolist()

        # Create stable ids for the batch
        offset = batch_idx * batch_size
        ids = [f"{col_name}_{offset + i}" for i in range(len(text_batch))]

        # Add documents with ids, metadatas and precomputed embeddings
        coll.add(ids=ids, documents=text_batch, metadatas=meta_batch, embeddings=vectors)

        processed = min((batch_idx + 1) * batch_size, total)
        print(f"    [*] Indexed {processed}/{total} into {col_name}")

print("\n[✅] Indexing complete. Collections stored in ./cyber_vector_db")