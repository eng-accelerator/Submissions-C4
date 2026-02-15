"""
Log Reader / Classifier Agent
Parses and classifies incident logs into structured format.
"""

from orchestrator.state import IncidentAnalysisState, LogEntry, ClassifiedIncident
from utils.llm_client import LLMClient
import re
from datetime import datetime


class LogClassifierAgent:
    """
    Agent responsible for parsing raw logs and classifying incidents.
    Extracts structured information and determines incident type.
    """
    
    SYSTEM_PROMPT = """You are a specialized DevOps Log Analysis AI.

Your task is to analyze raw application/system logs and extract structured information.

You must:
1. Parse the log to identify timestamp, service, severity, error codes, and message
2. Classify the incident type (e.g., DatabaseConnectionFailure, APITimeout, MemoryLeak, etc.)
3. Determine severity: INFO, WARNING, ERROR, or CRITICAL
4. Identify affected service
5. Provide a concise summary and technical details

Be precise and technical in your analysis."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize Log Classifier Agent
        
        Args:
            llm_client: LLM client for analysis
        """
        self.llm = llm_client
    
    def parse_log(self, raw_log: str) -> LogEntry:
        """
        Parse raw log into structured format
        
        Args:
            raw_log: Raw log string
            
        Returns:
            Structured LogEntry
        """
        # Basic regex patterns for common log formats
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}'
        severity_pattern = r'\b(INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|DEBUG)\b'
        
        timestamp_match = re.search(timestamp_pattern, raw_log)
        severity_match = re.search(severity_pattern, raw_log, re.IGNORECASE)
        
        # Extract fields
        timestamp = timestamp_match.group(0) if timestamp_match else None
        
        severity_str = severity_match.group(0).upper() if severity_match else "ERROR"
        # Normalize severity
        severity_map = {
            "INFO": "INFO",
            "DEBUG": "INFO",
            "WARN": "WARNING",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
            "FATAL": "CRITICAL"
        }
        severity = severity_map.get(severity_str, "ERROR")
        
        # Try to extract service name (common patterns)
        service_patterns = [
            r'service[=:\s]+([a-zA-Z0-9_-]+)',
            r'\[([a-zA-Z0-9_-]+)\]',
            r'from\s+([a-zA-Z0-9_-]+)',
        ]
        service = None
        for pattern in service_patterns:
            match = re.search(pattern, raw_log, re.IGNORECASE)
            if match:
                service = match.group(1)
                break
        
        # Error code extraction
        error_code_patterns = [
            r'error[_\s]code[=:\s]+([A-Z0-9_-]+)',
            r'code[=:\s]+(\d+)',
            r'ERR-(\d+)',
        ]
        error_code = None
        for pattern in error_code_patterns:
            match = re.search(pattern, raw_log, re.IGNORECASE)
            if match:
                error_code = match.group(1)
                break
        
        return LogEntry(
            timestamp=timestamp,
            service=service,
            severity=severity,
            error_code=error_code,
            message=raw_log.strip(),
            raw_log=raw_log
        )
    
    def classify_incident(self, log_entry: LogEntry) -> ClassifiedIncident:
        """
        Classify incident using LLM
        
        Args:
            log_entry: Parsed log entry
            
        Returns:
            Classified incident
        """
        user_prompt = f"""Analyze this log entry and classify the incident:

Raw Log:
{log_entry.raw_log}

Parsed Information:
- Timestamp: {log_entry.timestamp or 'Not detected'}
- Service: {log_entry.service or 'Unknown'}
- Severity: {log_entry.severity}
- Error Code: {log_entry.error_code or 'None'}

Provide a structured classification including:
- Incident type (specific, e.g., DatabaseConnectionTimeout, APIRateLimitExceeded)
- Severity assessment (INFO, WARNING, ERROR, CRITICAL)
- Affected service
- Brief summary (1-2 sentences)
- Technical details (what exactly went wrong)
"""
        
        # Use structured output
        classification = self.llm.invoke_with_structured_output(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=ClassifiedIncident
        )
        
        # Attach the original log entry
        classification.log_entry = log_entry
        
        return classification
    
    def process(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """
        Main processing method for the agent
        
        Args:
            state: Current incident analysis state
            
        Returns:
            Updated state with classified incident
        """
        try:
            # Parse log
            log_entry = self.parse_log(state.raw_log_input)
            
            # Classify incident
            classified_incident = self.classify_incident(log_entry)
            
            # Update state
            state.classified_incident = classified_incident
            
            # Set JIRA flag if critical
            if classified_incident.severity == "CRITICAL":
                state.should_create_jira = True
            
        except Exception as e:
            state.errors.append(f"Log Classifier Error: {str(e)}")
        
        return state
