"""Unit tests for the universal log parser."""
import pytest
from utils.log_parser import LogParser
from models import LogEntry


def test_syslog_parse():
    line = "Mar 24 10:15:23 web-server nginx: [error] 12345#0: *1 connect() failed (111: Connection refused) while connecting to upstream"
    parser = LogParser()
    entry = parser.parse_line(line)
    assert entry.severity == "ERROR"
    assert entry.service == "nginx"
    assert "Connection refused" in entry.message
    assert entry.metadata.get("pid") == "12345"


def test_json_parse():
    line = '{"timestamp": "2024-03-24T10:15:20Z", "level": "ERROR", "service": "user-service", "message": "Database connection pool exhausted", "pid": 1001}'
    parser = LogParser()
    entry = parser.parse_line(line)
    assert entry.timestamp == "2024-03-24T10:15:20Z"
    assert entry.severity == "ERROR"
    assert entry.service == "user-service"
    assert "pool exhausted" in entry.message
    assert entry.metadata.get("pid") == "1001"


def test_parse_returns_entries():
    raw = """Mar 24 10:15:23 web-server nginx: [error] 12345#0: *1 connect() failed
{"timestamp": "2024-03-24T10:15:20Z", "level": "WARN", "service": "api", "message": "Slow query"}
"""
    parser = LogParser()
    entries = parser.parse(raw)
    assert len(entries) >= 2
    assert entries[0].severity == "ERROR"
    assert entries[1].severity == "WARN"


def test_malformed_json_fallback():
    line = '{"broken": json here'
    parser = LogParser()
    entry = parser.parse_line(line)
    assert isinstance(entry, LogEntry)
    assert entry.message  # Falls back to plain text


def test_severity_normalization():
    parser = LogParser()
    e1 = parser.parse_line('{"level": "error", "message": "x"}')
    e2 = parser.parse_line('{"level": "WARN", "message": "y"}')
    assert e1.severity == "ERROR"
    assert e2.severity == "WARN"


def test_empty_input():
    parser = LogParser()
    entries = parser.parse("")
    assert entries == []
    entry = parser.parse_line("")
    assert entry.message == ""
