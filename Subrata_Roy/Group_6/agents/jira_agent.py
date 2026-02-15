"""
JIRA Ticket agent: creates tickets for incidents with duplicate detection.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from config import JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY, _clean_project_key
from models import ClassifiedIssue, RemediationPlan

_JIRA_DEBUG_LOG = Path(__file__).resolve().parent.parent / ".cursor" / "debug.log"


def _normalize_jira_server(url: str) -> str:
    """Use only scheme+host so paths (e.g. UUID) in JIRA_SERVER do not break API requests."""
    if not url:
        return url
    parsed = urlparse(url.rstrip("/"))
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else url.rstrip("/")


def _escape(s: str) -> str:
    return (s or "").replace("\r", "")


class JiraTicketAgent:
    """Creates and updates JIRA tickets for incidents."""

    def __init__(
        self,
        server: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: Optional[str] = None,
    ):
        _raw_server = (server or JIRA_SERVER or "").strip()
        _raw_project = (project_key or JIRA_PROJECT_KEY or "")
        self.server = _normalize_jira_server(_raw_server)
        self.email = (email or JIRA_EMAIL or "").strip()
        self.api_token = (api_token or JIRA_API_TOKEN or "").strip()
        # Normalize project key so \n\ttext or trailing junk never gets into API URL
        self.project_key = _clean_project_key(_raw_project) or "INCIDENT"
        self._jira = None
        # #region agent log
        try:
            _host = urlparse(self.server).netloc if self.server else ""
            with open(_JIRA_DEBUG_LOG, "a") as f:
                f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:__init__", "message": "JIRA server normalized", "data": {"server_host": _host, "raw_project_repr": repr(_raw_project), "project_key": self.project_key}, "hypothesisId": "H1,H2,H3"}) + "\n")
        except Exception:
            pass
        # #endregion
        if self.server and self.email and self.api_token:
            try:
                from jira import JIRA
                self._jira = JIRA(server=self.server, basic_auth=(self.email, self.api_token))
            except Exception as e:
                self._jira = None
                try:
                    with open(_JIRA_DEBUG_LOG, "a") as f:
                        f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:__init__", "message": "JIRA client init failed", "data": {"error": str(e)}}) + "\n")
                except Exception:
                    pass
        try:
            with open(_JIRA_DEBUG_LOG, "a") as f:
                f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:__init__", "message": "JIRA agent init", "data": {"has_server": bool(self.server), "has_email": bool(self.email), "has_token": bool(self.api_token), "project_key": self.project_key, "jira_client_none": self._jira is None}}) + "\n")
        except Exception:
            pass

    def _severity_to_priority(self, severity: str) -> str:
        m = {"CRITICAL": "Highest", "HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
        return m.get(severity.upper(), "Medium")

    def _build_description(
        self,
        issues: List[ClassifiedIssue],
        remediations: List[RemediationPlan],
        cookbook_md: str,
        dashboard_url: Optional[str] = None,
    ) -> str:
        lines = ["h2. Incident Summary", ""]
        for i in issues:
            lines.append(f"* {i.severity}: {_escape(i.summary)}")
        lines.append("")
        lines.append("h2. Affected Services")
        services = set()
        for i in issues:
            for s in i.affected_services:
                services.add(s)
        for s in services or ["unknown"]:
            lines.append(f"* {_escape(s)}")
        lines.append("")
        lines.append("h2. Timeline")
        ts = []
        for i in issues:
            if i.first_occurrence:
                ts.append(i.first_occurrence)
            if i.last_occurrence:
                ts.append(i.last_occurrence)
        if ts:
            lines.append(f"First: {ts[0]}")
            lines.append(f"Last: {ts[-1]}")
        else:
            lines.append(f"Detected: {datetime.utcnow().isoformat()}Z")
        lines.append("")
        lines.append("h2. Log Excerpts")
        lines.append("{code}")
        for i in issues[:3]:
            for e in i.log_entries[:2]:
                lines.append(_escape(e.message)[:500])
        lines.append("{code}")
        lines.append("")
        lines.append("h2. Recommended Remediation")
        lines.append("See cookbook below.")
        if dashboard_url:
            lines.append(f"[View Analysis Dashboard|{dashboard_url}]")
        lines.append("")
        lines.append("h3. Cookbook")
        lines.append("{code}")
        lines.append(_escape(cookbook_md)[:32000])
        lines.append("{code}")
        return "\n".join(lines)

    def _find_duplicate(self, category: str, summary: str) -> Optional[str]:
        """Search for open ticket with same category in last 24h; return key or None."""
        if not self._jira or not self.project_key:
            return None
        try:
            since = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d")
            jql = f'project = {self.project_key} AND labels = "{category}" AND created >= "{since}" AND status != Done ORDER BY created DESC'
            issues = self._jira.search_issues(jql, maxResults=5)
            for issue in issues:
                if summary[:80] in (issue.fields.summary or ""):
                    return issue.key
        except Exception:
            pass
        return None

    def _primary_issue(self, issues: List[ClassifiedIssue]) -> Optional[ClassifiedIssue]:
        """Return the highest-severity issue (CRITICAL > HIGH > MEDIUM > LOW)."""
        if not issues:
            return None
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return min(issues, key=lambda i: order.get(i.severity.upper(), 4))

    def create_or_comment(
        self,
        issues: List[ClassifiedIssue],
        remediations: List[RemediationPlan],
        cookbook_md: str,
        dashboard_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a JIRA ticket for the highest-severity issue, or add comment to duplicate.
        Returns ticket key or None.
        """
        try:
            with open(_JIRA_DEBUG_LOG, "a") as f:
                f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:create_or_comment", "message": "create_or_comment entry", "data": {"has_jira": self._jira is not None, "project_key": self.project_key, "issues_count": len(issues)}}) + "\n")
        except Exception:
            pass
        if not self._jira or not self.project_key:
            try:
                with open(_JIRA_DEBUG_LOG, "a") as f:
                    f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:create_or_comment", "message": "skipped (no client or project)", "data": {"has_jira": self._jira is not None, "has_project_key": bool(self.project_key)}}) + "\n")
            except Exception:
                pass
            return None
        primary = self._primary_issue(issues)
        if not primary:
            return None
        summary = f"[{primary.category}] {primary.summary}"[:255]
        dup = self._find_duplicate(primary.category, primary.summary)
        if dup:
            body = self._build_description(issues, remediations, cookbook_md, dashboard_url)
            try:
                self._jira.add_comment(dup, f"Additional occurrence:\n\n{body[:32000]}")
                return dup
            except Exception:
                pass
        description = self._build_description(issues, remediations, cookbook_md, dashboard_url)
        priority = self._severity_to_priority(primary.severity)
        labels = ["incident", primary.category, primary.subcategory] + list(primary.affected_services)[:3]
        # #region agent log
        try:
            with open(_JIRA_DEBUG_LOG, "a") as f:
                f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:create_or_comment", "message": "before create_issue", "data": {"project_key_repr": repr(self.project_key)}, "hypothesisId": "H5"}) + "\n")
        except Exception:
            pass
        # #endregion
        try:
            issue = self._jira.create_issue(
                project=self.project_key,
                summary=summary,
                description=description,
                priority={"name": priority},
                labels=labels,
                issuetype={"name": "Bug"},
            )
            return issue.key
        except Exception as e:
            try:
                with open(_JIRA_DEBUG_LOG, "a") as f:
                    f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "jira_agent.py:create_or_comment", "message": "create_issue failed", "data": {"error": str(e)}}) + "\n")
            except Exception:
                pass
            return None
