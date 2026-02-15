"""
JIRA Ticket Agent
Creates JIRA tickets for critical incidents.
"""

from orchestrator.state import IncidentAnalysisState, JIRATicketStatus
from utils.api_clients import JIRAClient


class JIRATicketAgent:
    """
    Agent responsible for creating JIRA tickets for critical incidents.
    Only activates when severity is CRITICAL.
    """
    
    def __init__(self, jira_url: str, username: str, api_token: str, project_key: str = "OPS", issue_type: str = "Task"):
        """
        Initialize JIRA Ticket Agent
        
        Args:
            jira_url: JIRA instance URL
            username: JIRA username
            api_token: JIRA API token
            project_key: JIRA project key (default: OPS)
            issue_type: JIRA issue type for created tickets (default: Task)
        """
        self.project_key = project_key
        self.issue_type = issue_type
        try:
            self.jira_client = JIRAClient(jira_url, username, api_token)
        except Exception as e:
            self.jira_client = None
            self.init_error = str(e)
    
    def prepare_ticket_content(self, state: IncidentAnalysisState) -> tuple[str, str, str]:
        """
        Prepare ticket content from state
        
        Args:
            state: Current incident analysis state
            
        Returns:
            Tuple of (summary, details, remediation_text)
        """
        incident = state.classified_incident
        remediation = state.remediation_plan
        
        # Summary for ticket title
        summary = f"{incident.incident_type} in {incident.affected_service}"
        
        # Details
        details = f"""
{incident.summary}

Technical Details:
{incident.technical_details}

Root Cause Hypothesis:
{remediation.root_cause_hypothesis}

Technical Rationale:
{remediation.technical_rationale}

Estimated Impact:
{remediation.estimated_impact}

Urgency: {remediation.urgency}
"""
        
        # Remediation text
        remediation_text = "Recommended Actions:\n"
        for i, fix in enumerate(remediation.recommended_fixes, 1):
            remediation_text += f"{i}. {fix}\n"
        
        return summary, details, remediation_text
    
    def process(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """
        Main processing method for the agent
        
        Args:
            state: Current incident analysis state
            
        Returns:
            Updated state with JIRA ticket status
        """
        try:
            # Check if JIRA ticket should be created
            if not state.should_create_jira:
                state.jira_ticket_status = JIRATicketStatus(
                    created=False,
                    error="Incident not critical - JIRA ticket not required"
                )
                return state
            
            if not self.jira_client:
                state.jira_ticket_status = JIRATicketStatus(
                    created=False,
                    error=f"JIRA client initialization failed: {self.init_error}"
                )
                return state
            
            if not state.classified_incident or not state.remediation_plan:
                raise ValueError("Missing required data for JIRA ticket")
            
            # Prepare content
            summary, details, remediation_text = self.prepare_ticket_content(state)
            
            # Create ticket
            success, ticket_key, ticket_url, error = self.jira_client.create_incident_ticket(
                project_key=self.project_key,
                incident_summary=summary,
                incident_details=details,
                remediation_plan=remediation_text,
                severity=state.classified_incident.severity,
                issue_type=self.issue_type
            )
            
            # Update state
            state.jira_ticket_status = JIRATicketStatus(
                created=success,
                ticket_key=ticket_key,
                ticket_url=ticket_url,
                error=error
            )
            
        except Exception as e:
            state.jira_ticket_status = JIRATicketStatus(
                created=False,
                error=str(e)
            )
            state.errors.append(f"JIRA Agent Error: {str(e)}")
        
        return state
