"""
API clients for external integrations (Tavily/Slack and JIRA).
"""

import requests
from typing import Optional
from jira import JIRA
from datetime import datetime


class SlackNotifier:
    """
    Slack notification via Tavily API or direct webhook.
    Note: Tavily is primarily a search API. For Slack, we'll use webhook directly.
    """
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
    
    def send_notification(
        self,
        incident_summary: str,
        severity: str,
        remediation_steps: list[str],
        jira_ticket: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Send formatted notification to Slack
        
        Args:
            incident_summary: Brief incident description
            severity: Incident severity level
            remediation_steps: List of remediation steps
            jira_ticket: Optional JIRA ticket URL
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Format severity with emoji
            severity_emoji = {
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "🔴",
                "CRITICAL": "🚨"
            }
            
            emoji = severity_emoji.get(severity, "⚠️")
            
            # Build message
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} DevOps Incident Alert - {severity}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Incident Summary:*\n{incident_summary}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Recommended Actions:*"
                    }
                }
            ]
            
            # Add remediation steps
            for i, step in enumerate(remediation_steps[:5], 1):  # Limit to 5 steps
                message_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{i}. {step}"
                    }
                })
            
            # Add JIRA ticket if exists
            if jira_ticket:
                message_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📋 *JIRA Ticket:* <{jira_ticket}|View Ticket>"
                    }
                })
            
            # Add timestamp
            message_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            })
            
            # Send to Slack
            payload = {
                "blocks": message_blocks
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Notification sent successfully"
            else:
                return False, f"Slack API error: {response.status_code} - {response.text}"
        
        except Exception as e:
            return False, f"Failed to send notification: {str(e)}"


class JIRAClient:
    """JIRA REST API client for ticket creation"""
    
    def __init__(self, jira_url: str, username: str, api_token: str):
        """
        Initialize JIRA client
        
        Args:
            jira_url: JIRA instance URL
            username: JIRA username/email
            api_token: JIRA API token
        """
        self.jira_url = jira_url
        try:
            self.client = JIRA(
                server=jira_url,
                basic_auth=(username, api_token)
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize JIRA client: {str(e)}")
    
    def create_incident_ticket(
        self,
        project_key: str,
        incident_summary: str,
        incident_details: str,
        remediation_plan: str,
        severity: str,
        issue_type: str = "Task"
    ) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Create incident ticket in JIRA
        
        Args:
            project_key: JIRA project key (e.g., 'OPS')
            incident_summary: Brief summary for ticket title
            incident_details: Detailed incident description
            remediation_plan: Remediation steps
            severity: Incident severity
            issue_type: JIRA issue type (e.g., Task, Bug, Incident). Default: Task
            
        Returns:
            Tuple of (success, ticket_key, ticket_url, error_message)
        """
        try:
            issuetype_name = (issue_type or "Task").strip()

            # Map severity to JIRA priority
            priority_map = {
                "CRITICAL": "Highest",
                "ERROR": "High",
                "WARNING": "Medium",
                "INFO": "Low"
            }
            priority = priority_map.get(severity, "High")
            
            # Build description
            description = f"""
h2. Incident Details
{incident_details}

h2. Remediation Plan
{remediation_plan}

h2. Severity
{severity}

---
_Auto-generated by DevOps Incident Analysis Suite_
_Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_
"""
            
            # Create ticket
            issue_dict = {
                'project': {'key': project_key},
                'summary': f"[{severity}] {incident_summary}",
                'description': description,
                'issuetype': {'name': issuetype_name},
                'priority': {'name': priority}
            }
            
            new_issue = self.client.create_issue(fields=issue_dict)
            
            ticket_key = new_issue.key
            ticket_url = f"{self.jira_url}/browse/{ticket_key}"
            
            return True, ticket_key, ticket_url, None
        
        except Exception as e:
            return False, None, None, f"Failed to create JIRA ticket: {str(e)}"
