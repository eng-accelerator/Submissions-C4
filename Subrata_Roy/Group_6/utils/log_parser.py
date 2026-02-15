"""
Universal log parser for the DevOps Incident Analysis system.

Handles multiple log formats: JSON, syslog, Apache, Nginx, custom application logs.
Extracts structured fields and supports multi-line stack traces.
"""

import json
import re
from datetime import datetime
from typing import List, Optional, Tuple
from dateutil import parser as date_parser

from models import LogEntry

# Severity normalization map (case-insensitive)
SEVERITY_MAP = {
    "critical": "CRITICAL",
    "error": "ERROR",
    "err": "ERROR",
    "warn": "WARN",
    "warning": "WARN",
    "info": "INFO",
    "information": "INFO",
    "debug": "DEBUG",
    "trace": "DEBUG",
    "fatal": "CRITICAL",
}

# Common timestamp patterns
TIMESTAMP_PATTERNS = [
    (re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)"), "iso"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)"), "datetime"),
    (re.compile(r"^([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"), "syslog"),  # Mar 24 10:15:23
    (re.compile(r"^(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2})"), "apache"),  # 24/Mar/2024:10:15:23
    (re.compile(r"^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})"), "datetime_slash"),
]


def _normalize_severity(level: Optional[str]) -> str:
    """Normalize severity string to standard levels."""
    if not level or not level.strip():
        return "INFO"
    key = level.strip().lower()
    return SEVERITY_MAP.get(key, "INFO")


def _parse_timestamp_to_utc(raw: str, fmt: str) -> Optional[str]:
    """Parse timestamp string to ISO UTC."""
    try:
        if fmt == "iso":
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        elif fmt == "syslog":
            # Assume current year if missing
            year = datetime.utcnow().year
            dt = date_parser.parse(f"{raw} {year}", ignore_tz=True)
        elif fmt == "apache":
            dt = date_parser.parse(raw, ignore_tz=True)
        else:
            dt = date_parser.parse(raw, ignore_tz=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=date_parser.tz.UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _detect_format(line: str) -> Tuple[Optional[str], Optional[dict]]:
    """
    Auto-detect log format and return (format_name, extracted_dict or None).
    Returns ("json", parsed_dict) for JSON, or ("syslog", None), ("apache", None), etc.
    """
    stripped = line.strip()
    if not stripped:
        return "empty", None

    # JSON
    if stripped.startswith("{"):
        try:
            obj = json.loads(stripped)
            return "json", obj
        except json.JSONDecodeError:
            pass

    # Syslog: Mar 24 10:15:23 host program[pid]: message or program: message
    syslog_re = re.compile(
        r"^([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?:\s*(.*)$",
        re.DOTALL,
    )
    m = syslog_re.match(stripped)
    if m:
        return "syslog", {"timestamp": m.group(1), "host": m.group(2), "program": m.group(3), "pid": m.group(4), "message": m.group(5)}

    # Apache/Nginx common: 192.168.1.1 - - [24/Mar/2024:10:15:23 +0000] "GET / HTTP/1.1" 500
    apache_re = re.compile(
        r"^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+\"([^\"]*)\"\s+(\d+)(?:\s+(\d+))?\s*(.*)$"
    )
    m = apache_re.match(stripped)
    if m:
        return "apache", {"ip": m.group(1), "timestamp": m.group(2), "request": m.group(3), "status": m.group(4), "message": m.group(6) or ""}

    # Generic: [timestamp] LEVEL service - message
    bracket_re = re.compile(r"^\[([^\]]+)\]\s+(\w+)\s+(\S+)\s+-\s+(.*)$", re.DOTALL)
    m = bracket_re.match(stripped)
    if m:
        return "bracket", {"timestamp": m.group(1), "level": m.group(2), "service": m.group(3), "message": m.group(4)}

    # Try timestamp at start then rest
    for pat, fmt in TIMESTAMP_PATTERNS:
        mo = pat.match(stripped)
        if mo:
            return "generic_ts", {"timestamp": mo.group(1), "rest": stripped[mo.end() :].strip()}

    return "plain", None


def _parse_json_line(obj: dict) -> LogEntry:
    """Build LogEntry from parsed JSON object."""
    ts = None
    if "timestamp" in obj:
        ts = _parse_timestamp_to_utc(str(obj["timestamp"]), "iso")
    if not ts and "time" in obj:
        ts = _parse_timestamp_to_utc(str(obj["time"]), "iso")
    if not ts and "@timestamp" in obj:
        ts = _parse_timestamp_to_utc(str(obj["@timestamp"]), "iso")

    severity = _normalize_severity(
        obj.get("level") or obj.get("severity") or obj.get("log_level") or obj.get("lvl")
    )
    service = obj.get("service") or obj.get("component") or obj.get("logger") or obj.get("app")
    message = obj.get("message") or obj.get("msg") or obj.get("text") or str(obj)
    stack = obj.get("stack_trace") or obj.get("stack") or obj.get("exception")

    metadata = {k: v for k, v in obj.items() if k not in (
        "timestamp", "time", "@timestamp", "level", "severity", "log_level", "lvl",
        "service", "component", "logger", "app", "message", "msg", "text",
        "stack_trace", "stack", "exception"
    ) and v is not None}
    if "pid" in obj:
        metadata["pid"] = str(obj["pid"])
    if "thread" in obj:
        metadata["thread_id"] = str(obj["thread"])
    if "request_id" in obj or "trace_id" in obj:
        metadata["request_id"] = str(obj.get("request_id") or obj.get("trace_id"))

    return LogEntry(
        timestamp=ts,
        severity=severity,
        service=service,
        message=message,
        stack_trace=stack,
        metadata=metadata,
        raw_line=json.dumps(obj) if isinstance(obj, dict) else None,
    )


def _parse_syslog_line(info: dict) -> LogEntry:
    """Build LogEntry from syslog-style extracted dict."""
    ts = _parse_timestamp_to_utc(info["timestamp"], "syslog")
    program = info["program"]
    msg = info["message"]

    # Try to extract [error] or level from message
    severity = "INFO"
    if "[error]" in msg.lower():
        severity = "ERROR"
    elif "[warn]" in msg.lower() or "[warning]" in msg.lower():
        severity = "WARN"
    elif "[debug]" in msg.lower():
        severity = "DEBUG"
    elif "[critical]" in msg.lower():
        severity = "CRITICAL"

    metadata = {}
    if info.get("pid"):
        metadata["pid"] = info["pid"]

    return LogEntry(
        timestamp=ts,
        severity=severity,
        service=program,
        message=msg,
        metadata=metadata,
        raw_line=f"{info['timestamp']} {info['host']} {program}: {msg}",
    )


def _parse_apache_line(info: dict) -> LogEntry:
    """Build LogEntry from Apache-style log."""
    ts_raw = info.get("timestamp", "")
    ts = _parse_timestamp_to_utc(ts_raw, "apache") if ts_raw else None
    status = info.get("status", "0")
    severity = "ERROR" if status and int(status) >= 500 else ("WARN" if int(status) >= 400 else "INFO")
    message = info.get("message", "").strip() or f"Request {info.get('request', '')} returned {status}"
    return LogEntry(
        timestamp=ts,
        severity=severity,
        service="apache",
        message=message,
        metadata={"status": status, "request": info.get("request")},
        raw_line=message or status,
    )


def _parse_bracket_line(info: dict) -> LogEntry:
    """Build LogEntry from [timestamp] LEVEL service - message."""
    ts = _parse_timestamp_to_utc(info["timestamp"], "datetime")
    severity = _normalize_severity(info["level"])
    return LogEntry(
        timestamp=ts,
        severity=severity,
        service=info["service"],
        message=info["message"],
        raw_line=f"[{info['timestamp']}] {info['level']} {info['service']} - {info['message']}",
    )


def _parse_generic_ts_line(info: dict) -> LogEntry:
    """Build LogEntry when only timestamp and rest are detected."""
    ts = _parse_timestamp_to_utc(info["timestamp"], "datetime")
    rest = info["rest"]
    severity = "INFO"
    for level in ["ERROR", "WARN", "DEBUG", "CRITICAL"]:
        if level.lower() in rest.lower():
            severity = level
            break
    return LogEntry(timestamp=ts, severity=severity, message=rest, raw_line=rest)


def _parse_plain_line(line: str) -> LogEntry:
    """Fallback for plain text line."""
    severity = "INFO"
    lower = line.lower()
    if "error" in lower or "exception" in lower or "failed" in lower:
        severity = "ERROR"
    elif "warn" in lower or "warning" in lower:
        severity = "WARN"
    elif "debug" in lower:
        severity = "DEBUG"
    return LogEntry(message=line.strip(), severity=severity, raw_line=line)


class LogParser:
    """
    Universal log parser for multiple formats with multi-line stack trace support.
    """

    def __init__(self, merge_multiline_stack: bool = True):
        """
        Args:
            merge_multiline_stack: If True, consecutive lines that look like
                stack traces (at ..., File "...", etc.) are merged into the
                previous log entry.
        """
        self.merge_multiline_stack = merge_multiline_stack
        self._stack_pattern = re.compile(
            r"^\s*(at\s+|File\s+[\"'].*[\"'],\s*line\s+\d+|"
            r"^\s*\.py\"?,\s*line\s+\d+|Caused by:|Traceback|\s+\.\.\.\s+\d+\s+more)"
        )

    def _is_stack_line(self, line: str) -> bool:
        """Heuristic: line looks like part of a stack trace."""
        s = line.strip()
        if not s:
            return False
        if self._stack_pattern.match(s):
            return True
        if s.startswith("  ") and ("at " in s or "line " in s or "File " in s):
            return True
        return False

    def parse_line(self, line: str) -> LogEntry:
        """
        Parse a single line into a LogEntry.
        Handles malformed JSON by falling back to plain text.
        """
        if not line or not line.strip():
            return LogEntry(message="", severity="INFO", raw_line=line)

        fmt, info = _detect_format(line)
        if fmt == "json" and info is not None:
            return _parse_json_line(info)
        if fmt == "syslog" and info is not None:
            return _parse_syslog_line(info)
        if fmt == "apache" and info is not None:
            return _parse_apache_line(info)
        if fmt == "bracket" and info is not None:
            return _parse_bracket_line(info)
        if fmt == "generic_ts" and info is not None:
            return _parse_generic_ts_line(info)
        return _parse_plain_line(line)

    def parse(self, raw_logs: str) -> List[LogEntry]:
        """
        Parse raw log text into a list of LogEntry objects.
        Supports multi-line stack traces by appending continuation lines to the
        previous entry's stack_trace field.
        """
        entries: List[LogEntry] = []
        lines = raw_logs.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            entry = self.parse_line(line)
            i += 1
            stack_lines: List[str] = []
            while i < len(lines) and self.merge_multiline_stack and self._is_stack_line(lines[i]):
                stack_lines.append(lines[i])
                i += 1
            if stack_lines:
                entry.stack_trace = "\n".join(stack_lines)
            # Skip empty message-only entries if they're truly empty
            if entry.message or entry.stack_trace or entry.raw_line:
                entries.append(entry)
        return entries
