"""
LangGraph incident workflow: orchestrates parse -> classify -> remediate -> cookbook -> notify/jira.
"""

import json
import time
from pathlib import Path
from typing import Literal, Optional, TypedDict

_DEBUG_LOG = Path(__file__).resolve().parent.parent / ".cursor" / "debug.log"

from langgraph.graph import StateGraph, END

from models import LogEntry, ClassifiedIssue, RemediationPlan
from utils.log_parser import LogParser
from utils.knowledge_base import RemediationKB
from .log_classifier import LogClassifierAgent
from .remediation_agent import RemediationAgent
from .cookbook_synthesizer import CookbookSynthesizerAgent
from .slack_notifier import SlackNotificationAgent
from .jira_agent import JiraTicketAgent


class IncidentState(TypedDict, total=False):
    raw_logs: str
    parsed_entries: list
    classified_issues: list
    remediations: list
    cookbook: str
    notifications_sent: bool
    jira_ticket_id: Optional[str]
    error: Optional[str]


def _parse_logs_node(state: IncidentState) -> IncidentState:
    parser = LogParser()
    raw = state.get("raw_logs") or ""
    entries = parser.parse(raw)
    return {"parsed_entries": [e.model_dump() for e in entries]}


def _classify_issues_node(state: IncidentState) -> IncidentState:
    parsed = state.get("parsed_entries") or []
    entries = [LogEntry(**e) if isinstance(e, dict) else e for e in parsed]
    agent = LogClassifierAgent()
    issues = agent.classify(entries)
    return {"classified_issues": [i.model_dump() for i in issues]}


def _find_remediations_node(state: IncidentState) -> IncidentState:
    issues_data = state.get("classified_issues") or []
    issues = [ClassifiedIssue(**i) if isinstance(i, dict) else i for i in issues_data]
    agent = RemediationAgent()
    plans = agent.find_remediations(issues)
    return {"remediations": [p.model_dump() for p in plans]}


def _generate_cookbook_node(state: IncidentState) -> IncidentState:
    issues_data = state.get("classified_issues") or []
    remediations_data = state.get("remediations") or []
    issues = [ClassifiedIssue(**i) if isinstance(i, dict) else i for i in issues_data]
    remediations = [RemediationPlan(**r) if isinstance(r, dict) else r for r in remediations_data]
    agent = CookbookSynthesizerAgent()
    cookbook = agent.generate(issues, remediations)
    return {"cookbook": cookbook}


def _route_notification(state: IncidentState) -> Literal["notify_slack", "end"]:
    issues_data = state.get("classified_issues") or []
    severities = [i.get("severity") for i in issues_data if isinstance(i, dict)]
    route = "end"
    if not issues_data:
        route = "end"
    else:
        if "CRITICAL" in severities or "HIGH" in severities or "MEDIUM" in severities:
            route = "notify_slack"
        else:
            route = "end"
    # #region agent log
    try:
        first_type = type(issues_data[0]).__name__ if issues_data else None
        with open(_DEBUG_LOG, "a") as f:
            f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "workflow.py:_route_notification", "message": "notification route", "data": {"issues_count": len(issues_data), "severities": severities, "route": route, "first_issue_type": first_type}, "hypothesisId": "B,E"}) + "\n")
    except Exception:
        pass
    # #endregion
    return route


def _notify_slack_node(state: IncidentState) -> IncidentState:
    issues_data = state.get("classified_issues") or []
    remediations_data = state.get("remediations") or []
    issues = [ClassifiedIssue(**i) if isinstance(i, dict) else i for i in issues_data]
    remediations = [RemediationPlan(**r) if isinstance(r, dict) else r for r in remediations_data]
    cookbook = state.get("cookbook") or ""
    agent = SlackNotificationAgent()
    # #region agent log
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "workflow.py:_notify_slack_node", "message": "before send", "data": {"issues_count": len(issues), "client_is_none": agent._client is None}, "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
    sent = agent.send(issues, remediations, cookbook)
    # #region agent log
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "workflow.py:_notify_slack_node", "message": "after send", "data": {"sent": sent}, "hypothesisId": "D"}) + "\n")
    except Exception:
        pass
    # #endregion
    return {"notifications_sent": sent}


def _create_jira_node(state: IncidentState) -> IncidentState:
    issues_data = state.get("classified_issues") or []
    remediations_data = state.get("remediations") or []
    cookbook = state.get("cookbook") or ""
    issues = [ClassifiedIssue(**i) if isinstance(i, dict) else i for i in issues_data]
    remediations = [RemediationPlan(**r) if isinstance(r, dict) else r for r in remediations_data]
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "workflow.py:_create_jira_node", "message": "create_jira entry", "data": {"issues_count": len(issues)}}) + "\n")
    except Exception:
        pass
    agent = JiraTicketAgent()
    key = agent.create_or_comment(issues, remediations, cookbook)
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "workflow.py:_create_jira_node", "message": "create_jira result", "data": {"jira_ticket_id": key}}) + "\n")
    except Exception:
        pass
    return {"jira_ticket_id": key}


def _route_after_slack(state: IncidentState) -> Literal["create_jira", "end"]:
    issues_data = state.get("classified_issues") or []
    severities = [i.get("severity") for i in issues_data if isinstance(i, dict)]
    route = "end"
    if "CRITICAL" in severities or "HIGH" in severities or "MEDIUM" in severities or "WARN" in severities or "INFO" in severities:
        route = "create_jira"
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(json.dumps({"timestamp": int(time.time() * 1000), "location": "workflow.py:_route_after_slack", "message": "jira route", "data": {"severities": severities, "route": route}}) + "\n")
    except Exception:
        pass
    return route


def build_incident_graph(checkpointer=None):
    """Build the LangGraph StateGraph for incident analysis with optional checkpointing."""
    builder = StateGraph(IncidentState)
    builder.add_node("parse_logs", _parse_logs_node)
    builder.add_node("classify_issues", _classify_issues_node)
    builder.add_node("find_remediations", _find_remediations_node)
    builder.add_node("generate_cookbook", _generate_cookbook_node)
    builder.add_node("notify_slack", _notify_slack_node)
    builder.add_node("create_jira", _create_jira_node)

    builder.set_entry_point("parse_logs")
    builder.add_edge("parse_logs", "classify_issues")
    builder.add_edge("classify_issues", "find_remediations")
    builder.add_edge("find_remediations", "generate_cookbook")
    builder.add_conditional_edges("generate_cookbook", _route_notification, {"notify_slack": "notify_slack", "end": END})
    builder.add_conditional_edges("notify_slack", _route_after_slack, {"create_jira": "create_jira", "end": END})
    builder.add_edge("create_jira", END)

    # Compile without checkpointer by default so invoke() does not require configurable (thread_id).
    # Pass checkpointer=MemorySaver() and invoke(..., config={"configurable": {"thread_id": "..."}}) for replay.
    return builder.compile(checkpointer=checkpointer)
