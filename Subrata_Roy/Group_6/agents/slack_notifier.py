"""
Notification agent: posts incident analysis to Slack using Block Kit.
Routes by severity and includes actionable buttons.
"""

import json
import urllib.request
import re
import time
from pathlib import Path
from typing import List, Optional

from config import SLACK_BOT_TOKEN, SLACK_WEBHOOK_URL

_DEBUG_LOG = Path(__file__).resolve().parent.parent / ".cursor" / "debug.log"
from models import ClassifiedIssue, RemediationPlan

# Channel routing by max severity in incident
CRITICAL_CHANNEL = "#incidents-critical"
HIGH_CHANNEL = "#incidents-high"
MEDIUM_LOW_CHANNEL = "#incidents-low"


def _truncate(text: str, max_len: int = 2900) -> str:
    if not text:
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _mrkdwn_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SlackNotificationAgent:
    """Formats and sends incident messages to Slack with Block Kit."""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or SLACK_BOT_TOKEN
        self._client = None
        if self.bot_token:
            try:
                from slack_sdk import WebClient
                self._client = WebClient(token=self.bot_token)
            except Exception:
                self._client = None
        # #region agent log
        try:
            with open(_DEBUG_LOG, "a") as f:
                f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "slack_notifier.py:__init__", "message": "SlackNotificationAgent init", "data": {"has_token": bool(self.bot_token), "client_is_none": self._client is None}, "hypothesisId": "A"}) + "\n")
        except Exception:
            pass
        # #endregion

    def _channel_for_severity(self, severity: str) -> str:
        if severity == "CRITICAL":
            return CRITICAL_CHANNEL
        if severity == "HIGH":
            return HIGH_CHANNEL
        return MEDIUM_LOW_CHANNEL

    def build_blocks(
        self,
        issues: List[ClassifiedIssue],
        remediations: List[RemediationPlan],
        cookbook_md: str,
        timestamp: Optional[str] = None,
    ) -> List[dict]:
        """Build Slack Block Kit blocks for the incident message."""
        severity = "LOW"
        for i in issues:
            if i.severity == "CRITICAL":
                severity = "CRITICAL"
                break
            if i.severity == "HIGH" and severity != "CRITICAL":
                severity = "HIGH"
            if i.severity == "MEDIUM" and severity == "LOW":
                severity = "MEDIUM"
        primary = issues[0] if issues else None
        title = primary.summary if primary else "Incident"
        header_emoji = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{header_emoji} {severity}: {_mrkdwn_escape(title)[:150]}", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Timestamp:* {timestamp or 'N/A'}\n*Severity:* {severity}",
                },
            },
        ]
        if issues:
            services = []
            for i in issues:
                for s in i.affected_services:
                    if s and s not in services:
                        services.append(s)
            if not services:
                services = [i.summary for i in issues[:3]]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Affected / Related:*\n• " + "\n• ".join(_mrkdwn_escape(s)[:100] for s in services[:10]),
                },
            })
        if remediations:
            steps_text = []
            for r in remediations[:3]:
                for j, step in enumerate(r.steps[:3], 1):
                    steps_text.append(f"{j}. {_mrkdwn_escape(step)[:200]}")
            if steps_text:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Recommended actions:*\n" + "\n".join(steps_text[:10]),
                    },
                })
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Cookbook", "emoji": True},
                    "url": "https://example.com/cookbook",
                    "action_id": "view_cookbook",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Mark Resolved", "emoji": True},
                    "action_id": "mark_resolved",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Escalate", "emoji": True},
                    "action_id": "escalate",
                },
            ],
        })
        return blocks

    def send(
        self,
        issues: List[ClassifiedIssue],
        remediations: List[RemediationPlan],
        cookbook_md: str,
        channel: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> bool:
        """Send incident message to Slack. Returns True if sent successfully."""
        # #region agent log
        try:
            with open(_DEBUG_LOG, "a") as f:
                f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "slack_notifier.py:send", "message": "send entry", "data": {"client_is_none": self._client is None}, "hypothesisId": "A"}) + "\n")
        except Exception:
            pass
        # #endregion
        severity = "LOW"
        for i in issues:
            if i.severity == "CRITICAL":
                severity = "CRITICAL"
                break
            if i.severity == "HIGH":
                severity = "HIGH"
            if i.severity == "MEDIUM":
                severity = "MEDIUM"
        ch = channel or self._channel_for_severity(severity)
        blocks = self.build_blocks(issues, remediations, cookbook_md, timestamp)
        text = f"{severity}: {(issues[0].summary if issues else 'Incident')}"[:100]
        if severity == "CRITICAL":
            blocks.insert(1, {"type": "section", "text": {"type": "mrkdwn", "text": "<!channel> Critical incident – please acknowledge."}})

        def try_webhook() -> bool:
            if not SLACK_WEBHOOK_URL:
                return False
            try:
                payload = {"text": text, "blocks": blocks}
                req = urllib.request.Request(
                    SLACK_WEBHOOK_URL,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status == 200
            except Exception:
                return False

        if self._client:
            try:
                self._client.chat_postMessage(channel=ch, text=text, blocks=blocks)
                # #region agent log
                try:
                    with open(_DEBUG_LOG, "a") as f:
                        f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "slack_notifier.py:send", "message": "send success", "data": {"sent": True}, "hypothesisId": "D"}) + "\n")
                except Exception:
                    pass
                # #endregion
                return True
            except Exception as e:
                # #region agent log
                try:
                    with open(_DEBUG_LOG, "a") as f:
                        f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "slack_notifier.py:send", "message": "send exception", "data": {"error": str(e)}, "hypothesisId": "D"}) + "\n")
                except Exception:
                    pass
                # #endregion
                if "missing_scope" in str(e) and try_webhook():
                    return True
                return False
        return try_webhook()
