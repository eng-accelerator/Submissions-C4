"""Shared data models for the incident analysis pipeline."""
from typing import List, Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Structured log entry from the universal log parser."""

    timestamp: Optional[str] = None  # ISO UTC
    severity: str = "INFO"
    service: Optional[str] = None
    message: str
    stack_trace: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    raw_line: Optional[str] = None


class ClassifiedIssue(BaseModel):
    """Issue classified by the Log Classifier agent."""

    category: str  # database | network | application | infrastructure | other
    subcategory: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    summary: str
    affected_services: List[str] = Field(default_factory=list)
    log_entries: List[LogEntry] = Field(default_factory=list)
    first_occurrence: Optional[str] = None
    last_occurrence: Optional[str] = None
    frequency: int = 1


class RemediationPlan(BaseModel):
    """Remediation suggestion from the knowledge base / remediation agent."""

    issue_summary: str
    runbook_content: str
    steps: List[str] = Field(default_factory=list)
    category: str = ""
    subcategory: str = ""
    success_rate: Optional[float] = None
    time_estimate: Optional[str] = None
    runbook_id: Optional[str] = None
