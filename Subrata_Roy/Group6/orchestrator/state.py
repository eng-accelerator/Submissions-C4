"""
State management for the multi-agent incident analysis system.
Defines the shared state that flows through the LangGraph orchestrator.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class LogEntry(BaseModel):
    """Structured log entry after parsing"""
    timestamp: Optional[str] = None
    service: Optional[str] = None
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"] = "ERROR"
    error_code: Optional[str] = None
    message: str
    raw_log: str


class ClassifiedIncident(BaseModel):
    """Incident classification output"""
    incident_type: str = Field(description="Type of incident (e.g., DatabaseConnectionFailure, APITimeout)")
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    affected_service: str
    summary: str
    technical_details: str
    log_entry: LogEntry


class RemediationPlan(BaseModel):
    """Remediation plan with root cause and fixes"""
    root_cause_hypothesis: str
    recommended_fixes: list[str] = Field(description="List of recommended fix steps")
    technical_rationale: str
    estimated_impact: str = Field(description="Expected impact of remediation")
    urgency: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class CookbookChecklist(BaseModel):
    """DevOps runbook-style checklist"""
    title: str
    checklist_items: list[str] = Field(description="Step-by-step actionable items")
    prerequisites: list[str] = []
    validation_steps: list[str] = []
    rollback_plan: str = ""


class NotificationStatus(BaseModel):
    """Slack notification status"""
    sent: bool = False
    message: str = ""
    error: Optional[str] = None
    timestamp: Optional[str] = None


class JIRATicketStatus(BaseModel):
    """JIRA ticket creation status"""
    created: bool = False
    ticket_key: Optional[str] = None
    ticket_url: Optional[str] = None
    error: Optional[str] = None


class IncidentAnalysisState(BaseModel):
    """
    Main state object that flows through the LangGraph orchestrator.
    Each agent reads from and writes to this state.
    """
    # Input
    raw_log_input: str = ""
    
    # Configuration
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    slack_webhook_url: str = ""
    jira_url: str = ""
    jira_username: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""
    jira_issue_type: str = "Task"
    llm_model: str = "openai/gpt-4o"
    
    # Agent outputs
    classified_incident: Optional[ClassifiedIncident] = None
    remediation_plan: Optional[RemediationPlan] = None
    cookbook_checklist: Optional[CookbookChecklist] = None
    notification_status: Optional[NotificationStatus] = None
    jira_ticket_status: Optional[JIRATicketStatus] = None
    
    # Flow control
    should_create_jira: bool = False
    errors: list[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
