"""
Notification Agent
Sends incident summaries and remediation plans to Slack.
"""

from orchestrator.state import IncidentAnalysisState, NotificationStatus
from utils.api_clients import SlackNotifier
from datetime import datetime


class NotificationAgent:
    """
    Agent responsible for sending notifications to Slack.
    Formats and delivers incident alerts with remediation steps.
    """
    
    def __init__(self, slack_webhook_url: str):
        """
        Initialize Notification Agent
        
        Args:
            slack_webhook_url: Slack webhook URL for notifications
        """
        self.slack_notifier = SlackNotifier(slack_webhook_url)
    
    def prepare_notification_content(self, state: IncidentAnalysisState) -> tuple[str, str, list[str], str]:
        """
        Prepare notification content from state
        
        Args:
            state: Current incident analysis state
            
        Returns:
            Tuple of (summary, severity, remediation_steps, jira_url)
        """
        incident = state.classified_incident
        remediation = state.remediation_plan
        
        # Build summary
        summary = f"{incident.incident_type} - {incident.summary}"
        
        # Get severity
        severity = incident.severity
        
        # Get remediation steps
        remediation_steps = remediation.recommended_fixes if remediation else []
        
        # Get JIRA URL if exists
        jira_url = None
        if state.jira_ticket_status and state.jira_ticket_status.ticket_url:
            jira_url = state.jira_ticket_status.ticket_url
        
        return summary, severity, remediation_steps, jira_url
    
    def process(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """
        Main processing method for the agent
        
        Args:
            state: Current incident analysis state
            
        Returns:
            Updated state with notification status
        """
        try:
            if not state.classified_incident or not state.remediation_plan:
                raise ValueError("Missing required data for notification")
            
            # Prepare content
            summary, severity, remediation_steps, jira_url = self.prepare_notification_content(state)
            
            # Send notification
            success, message = self.slack_notifier.send_notification(
                incident_summary=summary,
                severity=severity,
                remediation_steps=remediation_steps,
                jira_ticket=jira_url
            )
            
            # Update state
            state.notification_status = NotificationStatus(
                sent=success,
                message=message,
                error=None if success else message,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            state.notification_status = NotificationStatus(
                sent=False,
                message="",
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
            state.errors.append(f"Notification Agent Error: {str(e)}")
        
        return state
