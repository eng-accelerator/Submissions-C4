import csv
import json
import random
import zipfile
from datetime import datetime, timedelta

# ---------------------------------
# Config
# ---------------------------------
NUM_SYSLOG = 500000         # ~0.5M log rows
NUM_CVE = 20000
NUM_VULN = 15000
NUM_ALERT = 100000
NUM_POLICY = 8000

#ZIP_NAME = "cybersecurity_datasets.zip"

# ---------------------------------
# Helpers
# ---------------------------------
def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------------------------------
# 1) Syslog / Network Logs
# ---------------------------------
syslog_rows = []
start = datetime(2026,2,1)

for i in range(NUM_SYSLOG):
    ts = start + timedelta(seconds=i)
    syslog_rows.append([
        ts.isoformat() + "Z",
        f"host{random.randint(1,20):02d}",
        random_ip(),
        random_ip(),
        random.choice(["TCP","UDP","ICMP"]),
        random.choice(["INFO","WARNING","ERROR","ALERT"]),
        random.choice(["ALLOW","DENY","DROP"]),
        random.choice([
            "Login success",
            "Login failure",
            "Port scan detected",
            "Malformed request",
            "Connection established"
        ])
    ])

write_csv("./cyber_demo/syslog_large.csv",
          ["timestamp","host","src_ip","dst_ip","protocol","severity","action","event"],
          syslog_rows)

# ---------------------------------
# 2) CVE JSON
# ---------------------------------
cve_list = []
for i in range(1, NUM_CVE+1):
    cve_list.append({
        "cve_id": f"CVE-2026-{i:05d}",
        "published_date": (start + timedelta(days=random.randint(0,60))).strftime("%Y-%m-%d"),
        "cvss_base": round(random.uniform(4.0, 10.0), 1),
        "description": f"Sample vulnerability #{i}",
        "affected_products": [
            {
                "vendor": f"Vendor{random.randint(1,100)}",
                "product": f"Prod{random.randint(1,500)}",
                "version": f"{random.randint(1,5)}.{random.randint(0,9)}"
            }
        ]
    })

write_json("./cyber_demo/cve_data.json", cve_list)

# ---------------------------------
# 3) Vulnerability Scan
# ---------------------------------
vuln_rows = []
for i in range(NUM_VULN):
    vuln_rows.append([
        random_ip(), 
        f"VULN-{i+1:05d}",
        random.choice(["LOW","MEDIUM","HIGH","CRITICAL"]),
        random.choice(["weak_cipher","open_port","config_issue"]),
        random.choice(["Weak cipher detected","Open port exposed","Misconfig found"]),
        random.choice(["Apply patch","Restrict port","Fix config"])
    ])

write_csv("./cyber_demo/vuln_scan.csv",
          ["host","issue_id","severity","issue","finding","remediation"],
          vuln_rows)

# ---------------------------------
# 4) Incident Alerts
# ---------------------------------
alert_rows = []
for i in range(1, NUM_ALERT+1):
    alert_rows.append([
        f"ALERT-{100000+i}",
        (start + timedelta(seconds=random.randint(0,1000000))).isoformat() + "Z",
        random_ip(),
        random_ip(),
        random.choice(["BRUTE_FORCE","PORT_SCAN","MALWARE","DDOS"]),
        random.choice(["block","reset credentials","review firewall","isolate host"])
    ])

write_csv("./cyber_demo/incident_alerts.csv",
          ["alert_id","timestamp","src","tgt","type","recommendation"],
          alert_rows)

# ---------------------------------
# 5) Policy Compliance
# ---------------------------------
policy_rows = []
for i in range(NUM_POLICY):
    policy_rows.append([
        random_ip(),
        f"P-{i+1:04d}",
        random.choice(["ISO27001","NIST-CSF","SOC2"]),
        random.choice(["PASS","FAIL"]),
        random.choice(["SSH root disabled","TLS>=1.2 enforced","MFA enabled"])
    ])

write_csv("./cyber_demo/policy_checks.csv",
          ["host","policy_id","standard","status","detail"],
          policy_rows)

# ---------------------------------
# 6) Metadata Schemas
# ---------------------------------
schema = {
    "syslog_large.csv": ["timestamp","host","src_ip","dst_ip","protocol","severity","action","event"],
    "cve_data.json": ["cve_id","published_date","cvss_base","description","affected_products"],
    "vuln_scan.csv": ["host","issue_id","severity","issue","finding","remediation"],
    "incident_alerts.csv": ["alert_id","timestamp","src","tgt","type","recommendation"],
    "policy_checks.csv": ["host","policy_id","standard","status","detail"]
}

write_json("./cyber_demo/metadata_schema.json", schema)

# ---------------------------------
# Zip it all
# ---------------------------------
#with zipfile.ZipFile(ZIP_NAME, "w") as z:
#    for fname in [
#        "syslog_large.csv",
#        "cve_data.json",
#        "vuln_scan.csv",
#        "incident_alerts.csv",
#        "policy_checks.csv",
#        "metadata_schema.json"
#    ]:
#        z.write(fname)

#print(f"✨ Created {ZIP_NAME} with all datasets!")
