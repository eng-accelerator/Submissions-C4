"""
Log Reader/Classifier agent: categorizes issues from parsed logs.
Uses LLM with few-shot style for category and severity assignment.
"""

import json
import re
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from models import LogEntry, ClassifiedIssue


CLASSIFICATION_PROMPT = """You are an expert SRE analyzing log entries. Classify each distinct issue and assign severity.

Issue categories: database, network, application, infrastructure, other
Subcategories (examples): connection_timeout, query_timeout, deadlock, oom, connection_refused, timeout, dns_failure, null_pointer, authentication_failure, rate_limit_exceeded, disk_full, cpu_throttling, oom_killer

Severity:
- CRITICAL: service down, data loss risk
- HIGH: degraded performance, partial outage
- MEDIUM: isolated errors, retryable failures
- LOW: warnings, informational

Given the following parsed log entries, output a JSON array of classified issues. Group similar errors into one issue with frequency count. Each issue must have:
- category (one of: database, network, application, infrastructure, other)
- subcategory (specific type)
- severity (CRITICAL, HIGH, MEDIUM, LOW)
- summary (brief description)
- affected_services (list of service names from logs)
- log_entry_indices (list of indices of log entries that belong to this issue, 0-based)
- first_occurrence (ISO timestamp if available)
- last_occurrence (ISO timestamp if available)
- frequency (count of occurrences)

Output ONLY a valid JSON array, no markdown or explanation.

Parsed log entries (index: timestamp, severity, service, message):
{log_entries_text}
"""


class LogClassifierAgent:
    """Classifies log entries into actionable categories and severity."""

    def __init__(self, llm=None):
        self.llm = llm or get_llm(temperature=0.1)

    def _entries_to_text(self, entries: List[LogEntry]) -> str:
        lines = []
        for i, e in enumerate(entries):
            parts = [f"{i}:", e.timestamp or "no-ts", e.severity, e.service or "unknown", e.message]
            if e.stack_trace:
                parts.append(f" Stack: {e.stack_trace[:200]}...")
            lines.append(" | ".join(str(p) for p in parts))
        return "\n".join(lines)

    def classify(self, parsed_entries: List[LogEntry]) -> List[ClassifiedIssue]:
        """
        Classify parsed log entries into distinct issues with category and severity.
        Returns list of ClassifiedIssue.
        """
        if not parsed_entries:
            return []
        # Filter to ERROR/WARN/CRITICAL for classification
        relevant = [e for e in parsed_entries if e.severity in ("ERROR", "WARN", "CRITICAL")]
        if not relevant:
            relevant = parsed_entries[:50]
        log_entries_text = self._entries_to_text(relevant[:100])
        prompt = CLASSIFICATION_PROMPT.format(log_entries_text=log_entries_text)
        messages = [
            SystemMessage(content="You output only valid JSON arrays. No markdown code blocks."),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        text = response.content if hasattr(response, "content") else str(response)
        text = text.strip()
        # Remove markdown code block if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)
        try:
            arr = json.loads(text)
        except json.JSONDecodeError:
            arr = []
        issues = []
        for item in arr if isinstance(arr, list) else []:
            try:
                indices = item.get("log_entry_indices", [])
                log_entries_for_issue = [relevant[i] for i in indices if 0 <= i < len(relevant)]
                if not log_entries_for_issue and indices:
                    log_entries_for_issue = relevant[:1]
                elif not log_entries_for_issue:
                    log_entries_for_issue = [relevant[0]] if relevant else []
                issue = ClassifiedIssue(
                    category=(item.get("category") or "other").lower(),
                    subcategory=(item.get("subcategory") or "uncategorized").lower().replace(" ", "_"),
                    severity=(item.get("severity") or "MEDIUM").upper(),
                    summary=item.get("summary") or "No summary",
                    affected_services=item.get("affected_services") or [],
                    log_entries=log_entries_for_issue,
                    first_occurrence=item.get("first_occurrence"),
                    last_occurrence=item.get("last_occurrence"),
                    frequency=int(item.get("frequency", 1)),
                )
                issues.append(issue)
            except Exception:
                continue
        return issues
