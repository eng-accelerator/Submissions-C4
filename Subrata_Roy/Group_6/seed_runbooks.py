"""
Seed the remediation knowledge base with sample runbooks.
Run once: python seed_runbooks.py
"""

from utils.knowledge_base import RemediationKB

SAMPLE_RUNBOOKS = [
    {
        "content": """Title: Database Connection Pool Exhausted
Category: database, subcategory: connection_timeout
Steps:
1. Check current pool size: SELECT count(*) FROM pg_stat_activity;
2. Identify long-running queries: SELECT pid, now() - query_start, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;
3. Terminate blocking queries: SELECT pg_terminate_backend(pid) WHERE ...
4. Increase pool size in config: max_connections = 200
5. Restart service with zero downtime deployment""",
        "metadata": {
            "category": "database",
            "subcategory": "connection_timeout",
            "severity": "HIGH",
            "success_rate": 0.85,
            "time_estimate": "10-15 min",
            "prerequisites": "DB admin access",
        },
    },
    {
        "content": """Title: Nginx Upstream Connection Refused
Category: network, subcategory: connection_refused
Steps:
1. Verify upstream service is running: systemctl status <service>
2. Check upstream address and port in nginx config
3. Test connectivity: curl -v http://upstream:port/health
4. Restart upstream service if needed
5. Reload nginx: nginx -s reload""",
        "metadata": {
            "category": "network",
            "subcategory": "connection_refused",
            "severity": "HIGH",
            "success_rate": 0.9,
            "time_estimate": "5-10 min",
        },
    },
    {
        "content": """Title: Rate Limit Exceeded
Category: application, subcategory: rate_limit_exceeded
Steps:
1. Identify client IP or API key from logs
2. Check current rate limit config
3. Temporarily increase limit or add client to allowlist if legitimate
4. If abuse: block IP at firewall or WAF
5. Tune rate limits based on baseline traffic""",
        "metadata": {
            "category": "application",
            "subcategory": "rate_limit_exceeded",
            "severity": "MEDIUM",
            "success_rate": 0.95,
            "time_estimate": "5 min",
        },
    },
    {
        "content": """Title: Authentication Failure / Invalid Token
Category: application, subcategory: authentication_failure
Steps:
1. Confirm token expiry and issuer in JWT
2. Check auth service logs for validation errors
3. Rotate secrets if compromise suspected
4. Verify client is sending Authorization header
5. Clear client cache / re-login if token refresh flow broken""",
        "metadata": {
            "category": "application",
            "subcategory": "authentication_failure",
            "severity": "MEDIUM",
            "success_rate": 0.88,
            "time_estimate": "5-10 min",
        },
    },
    {
        "content": """Title: Disk Full / No Space Left
Category: infrastructure, subcategory: disk_full
Steps:
1. Find full filesystem: df -h
2. Find large dirs: du -sh /* 2>/dev/null | sort -hr | head -20
3. Clear logs, temp, or old releases: truncate, rotate, delete
4. Extend volume if no safe cleanup
5. Set alerts and auto-cleanup policies""",
        "metadata": {
            "category": "infrastructure",
            "subcategory": "disk_full",
            "severity": "CRITICAL",
            "success_rate": 0.92,
            "time_estimate": "10-30 min",
        },
    },
]


def main():
    kb = RemediationKB()
    for r in SAMPLE_RUNBOOKS:
        kb.add_runbook(r["content"], metadata=r["metadata"])
        print("Added runbook:", r["metadata"].get("category"), r["metadata"].get("subcategory"))
    print("Done. Runbooks seeded.")


if __name__ == "__main__":
    main()
