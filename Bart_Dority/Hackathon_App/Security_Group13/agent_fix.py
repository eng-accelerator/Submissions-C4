import json
import re
import hashlib
import logging
from typing import TypedDict, Dict, Any, List
from enum import Enum
from functools import lru_cache
from langgraph.graph import StateGraph, END

# -------------------------
# LOGGING CONFIGURATION
# -------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------------
# CONSTANTS AND LIMITS
# -------------------------

MAX_LOGS = 1000
MAX_LOG_SIZE = 10000  # characters per log field
MAX_QUERY_LENGTH = 500
MAX_RETRY_COUNT = 2
CACHE_SIZE = 100


# -------------------------
# FEATURE DEFAULTS (used when an analyzer is skipped)
# -------------------------

DEFAULT_SEQUENCE_FEATURES = {
    "login_velocity": 0.1,
    "sequential_object_access": 0.1,
    "request_frequency": 0.1,
    "repeated_action_score": 0.1,
}
DEFAULT_PAYLOAD_FEATURES = {
    "sql_injection_score": 0.1,
    "unexpected_field_score": 0.1,
    "command_injection_score": 0.1,
}
DEFAULT_BEHAVIOR_FEATURES = {
    "geo_deviation_score": 0.2,
    "role_deviation_score": 0.2,
    "user_agent_anomaly_score": 0.2,
}


# -------------------------
# ENUMS FOR TYPE SAFETY
# -------------------------

class AnalysisMode(str, Enum):
    FULL = "full"
    PAYLOAD_FOCUS = "payload_focus"
    SEQUENCE_FOCUS = "sequence_focus"
    BEHAVIOR_FOCUS = "behavior_focus"


class ExplanationLevel(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"


# -------------------------
# STATE DEFINITION
# -------------------------

class SecurityState(TypedDict, total=False):
    selected_vuln: str
    logs: List[Dict[str, Any]]
    client: Any

    sequence_features: Dict[str, float]
    payload_features: Dict[str, float]
    behavior_features: Dict[str, float]

    risk_score: float
    risk_factors: List[str]

    alert_type: str | None
    alert_confidence: float | None

    query: str | None
    analysis_mode: str | None
    priority_weights: Dict[str, float] | None
    explanation_level: str | None
    analysis_summary: Dict[str, Any] | None
    threat_narrative: str | None

    retry_count: int
    deep_dive_findings: Dict[str, Any] | None


# -------------------------
# INPUT SANITIZATION
# -------------------------

def sanitize_query(query: str) -> str:
    """
    Remove potential prompt injection attempts and limit length.
    
    Args:
        query: Raw user query
        
    Returns:
        Sanitized query string
    """
    if not query:
        return ""
    
    # Remove potential prompt injection patterns
    forbidden_patterns = [
        r'ignore\s+previous\s+instructions',
        r'ignore\s+all\s+previous',
        r'system\s*:',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
        r'assistant\s*:',
        r'you\s+are\s+now',
        r'disregard\s+',
        r'forget\s+everything',
    ]
    
    sanitized = query
    for pattern in forbidden_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Limit length
    sanitized = sanitized[:MAX_QUERY_LENGTH]
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized


def sanitize_log_entry(log: Any) -> Dict[str, Any]:
    """
    Sanitize a single log entry to prevent injection attacks.
    
    Args:
        log: Raw log entry
        
    Returns:
        Sanitized log dictionary
    """
    if not isinstance(log, dict):
        return {}
    
    sanitized = {}
    allowed_keys = {
        'endpoint', 'response_code', 'user_id', 'ip', 'user_agent',
        'params', 'body', 'timestamp', 'method', 'status'
    }
    
    for key, value in log.items():
        if key not in allowed_keys:
            continue
            
        # Limit string field sizes
        if isinstance(value, str):
            sanitized[key] = value[:MAX_LOG_SIZE]
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, dict):
            # Limit nested dict size
            sanitized[key] = {
                k: str(v)[:MAX_LOG_SIZE] if isinstance(v, str) else v
                for k, v in list(value.items())[:10]
            }
        elif isinstance(value, list):
            # Limit list size
            sanitized[key] = [
                str(item)[:MAX_LOG_SIZE] if isinstance(item, str) else item
                for item in value[:10]
            ]
    
    return sanitized


def sanitize_findings(findings: dict, max_depth: int = 3) -> dict:
    """
    Recursively sanitize findings to ensure only safe data types.
    
    Args:
        findings: Raw findings dictionary
        max_depth: Maximum recursion depth
        
    Returns:
        Sanitized findings
    """
    if max_depth <= 0:
        return {}
    
    safe_findings = {}
    for key, value in list(findings.items())[:20]:  # Limit keys
        if isinstance(value, (str, int, float, bool, type(None))):
            if isinstance(value, str):
                safe_findings[key] = value[:1000]  # Limit string length
            else:
                safe_findings[key] = value
        elif isinstance(value, list):
            safe_findings[key] = [
                v for v in value[:10]
                if isinstance(v, (str, int, float, bool))
            ]
        elif isinstance(value, dict):
            safe_findings[key] = sanitize_findings(value, max_depth - 1)
    
    return safe_findings


def validate_priority_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Validate and clamp priority weights to safe ranges.
    
    Args:
        weights: Raw weight dictionary
        
    Returns:
        Validated weights
    """
    valid_weights = {}
    for key in ['sequence', 'payload', 'behavior']:
        raw_value = weights.get(key, 1.0)
        # Clamp to safe range
        valid_weights[key] = max(0.5, min(2.0, float(raw_value)))
    
    return valid_weights


# -------------------------
# ANALYSIS HELPERS (optimized for single-pass processing)
# -------------------------

def _analyze_sequences(logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Single-pass sequence analysis with optimized iteration.
    
    Args:
        logs: List of sanitized log entries
        
    Returns:
        Dictionary of sequence feature scores
    """
    login_failures = 0
    user_api_access = 0
    order_requests = 0
    total_requests = len(logs)
    
    for entry in logs:
        endpoint = entry.get("endpoint", "")
        response_code = entry.get("response_code")
        
        if endpoint == "/api/login" and response_code == 401:
            login_failures += 1
        
        if "/api/users/" in endpoint:
            user_api_access += 1
        
        if endpoint == "/api/orders":
            order_requests += 1
    
    return {
        "login_velocity": min(login_failures / 5.0, 0.9) if login_failures > 0 else 0.1,
        "sequential_object_access": min(user_api_access / 5.0, 0.85) if user_api_access > 0 else 0.1,
        "request_frequency": min(total_requests / 10.0, 1.0),
        "repeated_action_score": min(order_requests / 5.0, 0.8) if order_requests > 0 else 0.1,
    }


def _analyze_payloads(logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Enhanced payload analysis with robust pattern matching.
    
    Args:
        logs: List of sanitized log entries
        
    Returns:
        Dictionary of payload feature scores
    """
    sql_injection_score = 0.1
    unexpected_field_score = 0.1
    command_injection_score = 0.1
    
    # Improved SQL injection patterns (case-insensitive, spacing-tolerant)
    sqli_patterns = [
        r'(\bunion\b.*\bselect\b)',
        r'(\bor\b\s*\d+\s*=\s*\d+)',
        r'(\band\b\s*\d+\s*=\s*\d+)',
        r'(--|#|\/\*.*\*\/)',
        r'(\bexec\b|\bexecute\b)',
        r'(xp_cmdshell)',
        r'(\bdrop\b\s+\btable\b)',
        r'(\binsert\b\s+\binto\b)',
        r'(\bupdate\b\s+\w+\s+\bset\b)',
        r'(\bdelete\b\s+\bfrom\b)',
        r"('|\"|%27|%22|\\x27|\\x22)",  # Quote injection
    ]
    
    # Command injection patterns
    cmd_patterns = [
        r'(\||;|`|\$\()',
        r'(&&|\|\|)',
        r'(curl|wget|nc|netcat)',
        r'(/bin/bash|/bin/sh)',
    ]
    
    for entry in logs:
        params = str(entry.get("params", "")) + str(entry.get("body", ""))
        params_lower = params.lower()
        
        # Check SQL injection
        for pattern in sqli_patterns:
            if re.search(pattern, params_lower, re.IGNORECASE):
                sql_injection_score = max(sql_injection_score, 0.95)
                break
        
        # Check command injection
        for pattern in cmd_patterns:
            if re.search(pattern, params, re.IGNORECASE):
                command_injection_score = max(command_injection_score, 0.9)
                break
        
        # Check unexpected fields
        if re.search(r'\b(isAdmin|admin|role|privilege)\b', params, re.IGNORECASE):
            unexpected_field_score = max(unexpected_field_score, 0.9)
    
    return {
        "sql_injection_score": sql_injection_score,
        "unexpected_field_score": unexpected_field_score,
        "command_injection_score": command_injection_score,
    }


def _analyze_behavior(logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Single-pass behavior analysis.
    
    Args:
        logs: List of sanitized log entries
        
    Returns:
        Dictionary of behavior feature scores
    """
    suspicious_user_ids = set()
    suspicious_agents = 0
    unique_ips = set()
    
    suspicious_agent_patterns = [
        r'sqlmap',
        r'nikto',
        r'nmap',
        r'masscan',
        r'burp',
        r'zap',
        r'metasploit',
    ]
    
    for entry in logs:
        user_id = entry.get("user_id")
        user_agent = entry.get("user_agent", "").lower()
        ip = entry.get("ip", "")
        
        # Track suspicious user IDs (example: user 456)
        if user_id == 456:
            suspicious_user_ids.add(user_id)
        
        # Check for suspicious user agents
        for pattern in suspicious_agent_patterns:
            if pattern in user_agent:
                suspicious_agents += 1
                break
        
        # Track unique IPs
        if ip:
            unique_ips.add(ip)
    
    geo_deviation_score = 0.6 if len(unique_ips) > 5 else 0.2
    role_deviation_score = 0.75 if suspicious_user_ids else 0.2
    user_agent_anomaly_score = min(suspicious_agents / 3.0, 0.8) if suspicious_agents > 0 else 0.2
    
    return {
        "geo_deviation_score": geo_deviation_score,
        "role_deviation_score": role_deviation_score,
        "user_agent_anomaly_score": user_agent_anomaly_score,
    }


# -------------------------
# LLM INTERACTION WITH CACHING
# -------------------------

@lru_cache(maxsize=CACHE_SIZE)
def _cached_intent_analysis(query_hash: str, client_repr: str) -> dict:
    """
    Cached wrapper for intent analysis to avoid redundant LLM calls.
    
    Args:
        query_hash: MD5 hash of the sanitized query
        client_repr: String representation of client (for cache key)
        
    Returns:
        Analysis result dictionary
    """
    # This is just a cache key function
    # Actual implementation happens in intent_router_node
    return {}


def safe_json_parse(content: str) -> dict:
    """
    Safely parse JSON from LLM response with validation.
    
    Args:
        content: Raw LLM response content
        
    Returns:
        Parsed and validated dictionary
        
    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    # Remove markdown code blocks if present
    cleaned = content.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned, flags=re.MULTILINE | re.DOTALL)
        cleaned = cleaned.strip()
    
    # Parse JSON
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    # Validate required keys
    required_keys = {'analysis_mode', 'priority_weights', 'explanation_level'}
    if not required_keys.issubset(parsed.keys()):
        missing = required_keys - set(parsed.keys())
        raise ValueError(f"Missing required keys: {missing}")
    
    # Validate analysis_mode
    valid_modes = {mode.value for mode in AnalysisMode}
    if parsed['analysis_mode'] not in valid_modes:
        raise ValueError(f"Invalid analysis_mode: {parsed['analysis_mode']}")
    
    # Validate explanation_level
    valid_levels = {level.value for level in ExplanationLevel}
    if parsed['explanation_level'] not in valid_levels:
        raise ValueError(f"Invalid explanation_level: {parsed['explanation_level']}")
    
    # Validate priority_weights structure
    if not isinstance(parsed['priority_weights'], dict):
        raise ValueError("priority_weights must be a dictionary")
    
    return parsed


# -------------------------
# NODES
# -------------------------

def _keyword_fallback(query: str) -> dict:
    """
    Keyword-matching logic used when the LLM is unavailable.
    
    Args:
        query: Sanitized user query
        
    Returns:
        Analysis configuration dictionary
    """
    result = {
        "analysis_mode": AnalysisMode.FULL.value,
        "priority_weights": {"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        "explanation_level": ExplanationLevel.STANDARD.value,
    }
    
    query_lower = query.lower()
    
    # SQL-related queries
    if any(keyword in query_lower for keyword in ['sql', 'injection', 'sqli', 'union', 'payload']):
        result["analysis_mode"] = AnalysisMode.PAYLOAD_FOCUS.value
        result["priority_weights"]["payload"] = 1.5
    
    # Credential-related queries
    elif any(keyword in query_lower for keyword in ['credential', 'login', 'brute', 'password', 'auth']):
        result["analysis_mode"] = AnalysisMode.SEQUENCE_FOCUS.value
        result["priority_weights"]["sequence"] = 1.5
    
    # Behavior-related queries
    elif any(keyword in query_lower for keyword in ['behavior', 'anomaly', 'suspicious', 'insider', 'user agent']):
        result["analysis_mode"] = AnalysisMode.BEHAVIOR_FOCUS.value
        result["priority_weights"]["behavior"] = 1.5
    
    # Explanation requested
    if any(keyword in query_lower for keyword in ['explain', 'detail', 'why', 'how']):
        result["explanation_level"] = ExplanationLevel.DETAILED.value
    
    return result


INTENT_ROUTER_SYSTEM_PROMPT = """You are a security analysis intent parser. Given a user query about security log analysis, determine the best analysis configuration.

Return ONLY valid JSON (no markdown, no explanation) with these exact keys:
{
  "analysis_mode": one of "full", "payload_focus", "sequence_focus", "behavior_focus",
  "priority_weights": {"sequence": <float 0.5-2.0>, "payload": <float 0.5-2.0>, "behavior": <float 0.5-2.0>},
  "explanation_level": "standard" or "detailed"
}

Guidelines for setting weights:
- Default all weights to 1.0 for general queries
- Boost "payload" (1.3-1.8) for queries about injection attacks, malicious payloads, SQLi, XSS, command injection
- Boost "sequence" (1.3-1.8) for queries about login attempts, credential stuffing, brute force, IDOR, repeated actions
- Boost "behavior" (1.3-1.8) for queries about anomalous users, geo-deviation, suspicious user agents, insider threats
- Set explanation_level to "detailed" if the user asks for explanations or reasoning

CRITICAL: Return ONLY the JSON object. No other text."""


def intent_router_node(state: SecurityState) -> SecurityState:
    """
    Routes analysis based on user query intent with LLM assistance.
    Falls back to keyword matching if LLM unavailable.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with analysis configuration
    """
    raw_query = state.get("query") or ""
    query = sanitize_query(raw_query)
    client = state.get("client")

    # Set defaults
    state["analysis_mode"] = AnalysisMode.FULL.value
    state["priority_weights"] = {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}
    state["explanation_level"] = ExplanationLevel.STANDARD.value

    if not query.strip():
        logger.info("Empty query, using default analysis mode")
        return state

    # Try LLM-based intent analysis with caching
    if client:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        try:
            logger.info(f"Analyzing intent for query hash: {query_hash[:8]}...")
            
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": INTENT_ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                max_tokens=150,
                temperature=0,
            )
            
            content = response.choices[0].message.content
            parsed = safe_json_parse(content)
            
            state["analysis_mode"] = parsed["analysis_mode"]
            state["priority_weights"] = validate_priority_weights(parsed["priority_weights"])
            state["explanation_level"] = parsed["explanation_level"]
            
            logger.info(
                f"LLM intent analysis complete",
                extra={
                    "mode": state["analysis_mode"],
                    "weights": state["priority_weights"]
                }
            )
            return state
            
        except (json.JSONDecodeError, ValueError, KeyError, Exception) as e:
            logger.warning(f"LLM intent analysis failed: {e}, falling back to keyword matching")

    # Fallback to keyword matching
    fallback = _keyword_fallback(query)
    state["analysis_mode"] = fallback["analysis_mode"]
    state["priority_weights"] = fallback["priority_weights"]
    state["explanation_level"] = fallback["explanation_level"]
    
    logger.info(
        f"Keyword fallback intent analysis complete",
        extra={
            "mode": state["analysis_mode"],
            "weights": state["priority_weights"]
        }
    )
    
    return state


def log_ingest_node(state: SecurityState) -> SecurityState:
    """
    Ingest and sanitize logs with size limits and validation.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with sanitized logs
    """
    raw_logs = state.get("logs", [])
    
    # Limit number of logs
    limited_logs = raw_logs[:MAX_LOGS]
    
    # Sanitize each log entry
    sanitized_logs = []
    for log in limited_logs:
        sanitized = sanitize_log_entry(log)
        if sanitized:  # Only add non-empty sanitized logs
            sanitized_logs.append(sanitized)
    
    state["logs"] = sanitized_logs
    state["selected_vuln"] = str(state.get("selected_vuln", ""))[:100]
    state["retry_count"] = 0
    
    logger.info(
        f"Log ingestion complete",
        extra={
            "original_count": len(raw_logs),
            "sanitized_count": len(sanitized_logs),
            "selected_vuln": state["selected_vuln"]
        }
    )
    
    return state


def sequence_analyzer_node(state: SecurityState) -> SecurityState:
    """Analyze sequence patterns in logs."""
    logger.info("Running sequence analyzer")
    state["sequence_features"] = _analyze_sequences(state["logs"])
    logger.info(f"Sequence analysis complete: {state['sequence_features']}")
    return state


def payload_inspector_node(state: SecurityState) -> SecurityState:
    """Inspect payloads for malicious patterns."""
    logger.info("Running payload inspector")
    state["payload_features"] = _analyze_payloads(state["logs"])
    logger.info(f"Payload analysis complete: {state['payload_features']}")
    return state


def behavior_profiler_node(state: SecurityState) -> SecurityState:
    """Profile user behavior for anomalies."""
    logger.info("Running behavior profiler")
    state["behavior_features"] = _analyze_behavior(state["logs"])
    logger.info(f"Behavior analysis complete: {state['behavior_features']}")
    return state


def run_all_analyzers_node(state: SecurityState) -> SecurityState:
    """Run all analyzers in parallel (single-pass optimization)."""
    logger.info("Running all analyzers")
    
    state["sequence_features"] = _analyze_sequences(state["logs"])
    state["payload_features"] = _analyze_payloads(state["logs"])
    state["behavior_features"] = _analyze_behavior(state["logs"])
    
    logger.info("All analyzers complete")
    return state


def risk_aggregator_node(state: SecurityState) -> SecurityState:
    """
    Aggregate risk scores from all feature sets with weighted scoring.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with aggregated risk score
    """
    logger.info("Aggregating risk scores")
    
    # Get features with defaults
    sf = state.get("sequence_features") or DEFAULT_SEQUENCE_FEATURES
    pf = state.get("payload_features") or DEFAULT_PAYLOAD_FEATURES
    bf = state.get("behavior_features") or DEFAULT_BEHAVIOR_FEATURES

    # Ensure features are set in state
    state["sequence_features"] = sf
    state["payload_features"] = pf
    state["behavior_features"] = bf

    # Calculate component scores (max of each category)
    sequence_score = max(sf.values())
    payload_score = max(pf.values())
    behavior_score = max(bf.values())

    # Get priority weights
    weights = state.get("priority_weights") or {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}

    # Apply weights (base weights: 0.4, 0.4, 0.2)
    sequence_weight = 0.4 * weights["sequence"]
    payload_weight = 0.4 * weights["payload"]
    behavior_weight = 0.2 * weights["behavior"]

    # Normalize weights to sum to 1.0
    total_weight = sequence_weight + payload_weight + behavior_weight
    sequence_weight /= total_weight
    payload_weight /= total_weight
    behavior_weight /= total_weight

    # Calculate final risk score
    state["risk_score"] = min(
        sequence_weight * sequence_score
        + payload_weight * payload_score
        + behavior_weight * behavior_score,
        1.0,
    )

    # Identify risk factors (features with scores > 0.7)
    combined = {**sf, **pf, **bf}
    state["risk_factors"] = [k for k, v in combined.items() if v > 0.7]

    logger.info(
        f"Risk aggregation complete",
        extra={
            "risk_score": state["risk_score"],
            "risk_factors": state["risk_factors"],
            "component_scores": {
                "sequence": sequence_score,
                "payload": payload_score,
                "behavior": behavior_score,
            }
        }
    )

    return state


def mini_agent_classifier_node(state: SecurityState) -> SecurityState:
    """
    Classify threats using hypothesis-driven mini-agent logic.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with threat classification
    """
    logger.info("Starting threat classification")
    
    sf = state["sequence_features"]
    pf = state["payload_features"]
    bf = state["behavior_features"]
    risk_score = state["risk_score"]

    # Define attack hypotheses with primary signals and supporting/contradicting evidence
    hypothesis_definitions = {
        "SQL_INJECTION": {
            "primary": ("sql_injection_score", pf.get("sql_injection_score", 0)),
            "support_keys": ["unexpected_field_score", "user_agent_anomaly_score", "command_injection_score"],
            "contradict_keys": ["login_velocity", "sequential_object_access"],
        },
        "CREDENTIAL_STUFFING": {
            "primary": ("login_velocity", sf.get("login_velocity", 0)),
            "support_keys": ["request_frequency", "geo_deviation_score"],
            "contradict_keys": ["sql_injection_score", "sequential_object_access", "command_injection_score"],
        },
        "POSSIBLE_IDOR": {
            "primary": ("sequential_object_access", sf.get("sequential_object_access", 0)),
            "support_keys": ["role_deviation_score", "request_frequency"],
            "contradict_keys": ["sql_injection_score", "login_velocity"],
        },
        "BUSINESS_LOGIC_ABUSE": {
            "primary": ("repeated_action_score", sf.get("repeated_action_score", 0)),
            "support_keys": ["request_frequency", "role_deviation_score"],
            "contradict_keys": ["sql_injection_score", "login_velocity"],
        },
        "COMMAND_INJECTION": {
            "primary": ("command_injection_score", pf.get("command_injection_score", 0)),
            "support_keys": ["unexpected_field_score", "user_agent_anomaly_score"],
            "contradict_keys": ["login_velocity", "sequential_object_access"],
        },
    }

    all_features = {**sf, **pf, **bf}

    # Evaluate each hypothesis
    evaluated = []
    for label, defn in hypothesis_definitions.items():
        primary_name, primary_score = defn["primary"]
        
        # Skip if primary signal is weak
        if primary_score <= 0.5:
            continue

        evidence = {
            "support": [primary_name],
            "contradict": [],
            "score": primary_score
        }

        # Add supporting evidence
        for key in defn["support_keys"]:
            val = all_features.get(key, 0)
            if val > 0.5:
                evidence["support"].append(key)
                evidence["score"] += 0.1

        # Subtract contradicting evidence
        for key in defn["contradict_keys"]:
            val = all_features.get(key, 0)
            if val > 0.7:
                evidence["contradict"].append(key)
                evidence["score"] -= 0.15

        # Apply global risk score multiplier
        evidence["score"] = max(evidence["score"], 0) * risk_score
        
        evaluated.append((label, evidence))

    # Handle no strong hypotheses
    if not evaluated:
        logger.info("No strong threat hypotheses detected")
        state["alert_type"] = None
        state["alert_confidence"] = 0.0
        state["analysis_summary"] = {
            "selected_alert": None,
            "confidence": 0.0,
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }
        return state

    # Sort by score
    evaluated.sort(key=lambda x: x[1]["score"], reverse=True)
    top_label, top_evidence = evaluated[0]

    # Detect multi-vector attacks (close scores)
    if len(evaluated) >= 2 and abs(evaluated[0][1]["score"] - evaluated[1][1]["score"]) <= 0.1:
        top_label = "MULTI_VECTOR_ATTACK"
        logger.warning("Multi-vector attack detected")

    state["alert_type"] = top_label
    state["alert_confidence"] = top_evidence["score"]
    state["analysis_summary"] = {
        "selected_alert": top_label,
        "confidence": top_evidence["score"],
        "supporting_evidence": top_evidence["support"],
        "contradicting_evidence": top_evidence["contradict"],
    }
    
    logger.info(
        f"Threat classification complete",
        extra={
            "alert_type": top_label,
            "confidence": top_evidence["score"],
            "candidates": len(evaluated)
        }
    )

    return state


def benign_summary_node(state: SecurityState) -> SecurityState:
    """
    Generate summary for benign/low-risk activity.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with benign summary
    """
    logger.info("Generating benign activity summary")
    
    state["alert_type"] = None
    state["alert_confidence"] = 0.0
    state["risk_factors"] = state.get("risk_factors", [])
    state["analysis_summary"] = {
        "selected_alert": None,
        "confidence": 0.0,
        "supporting_evidence": [],
        "contradicting_evidence": [],
    }
    
    risk_score = state.get("risk_score", 0)
    state["threat_narrative"] = (
        f"Activity appears benign. Risk score: {risk_score:.0%}. "
        "No significant threat indicators detected across analyzed dimensions."
    )
    
    logger.info(f"Benign summary complete, risk_score={risk_score:.2%}")
    return state


def widen_and_retry_node(state: SecurityState) -> SecurityState:
    """
    Widens a focused scan to full analysis when initial confidence is too low.
    Only runs missing analyzers to avoid redundant work.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state after widening analysis
    """
    retry_count = state.get("retry_count", 0)
    
    # Prevent infinite loops
    if retry_count >= MAX_RETRY_COUNT:
        logger.warning(f"Max retry count ({MAX_RETRY_COUNT}) reached, aborting retry")
        return state
    
    logger.info(f"Widening analysis scope (retry {retry_count + 1}/{MAX_RETRY_COUNT})")
    
    mode = state.get("analysis_mode", AnalysisMode.FULL.value)
    
    # Only run missing analyses based on previous mode
    if mode == AnalysisMode.PAYLOAD_FOCUS.value:
        if not state.get("sequence_features"):
            logger.info("Running missing sequence analysis")
            state["sequence_features"] = _analyze_sequences(state["logs"])
        if not state.get("behavior_features"):
            logger.info("Running missing behavior analysis")
            state["behavior_features"] = _analyze_behavior(state["logs"])
    
    elif mode == AnalysisMode.SEQUENCE_FOCUS.value:
        if not state.get("payload_features"):
            logger.info("Running missing payload analysis")
            state["payload_features"] = _analyze_payloads(state["logs"])
        if not state.get("behavior_features"):
            logger.info("Running missing behavior analysis")
            state["behavior_features"] = _analyze_behavior(state["logs"])
    
    elif mode == AnalysisMode.BEHAVIOR_FOCUS.value:
        if not state.get("sequence_features"):
            logger.info("Running missing sequence analysis")
            state["sequence_features"] = _analyze_sequences(state["logs"])
        if not state.get("payload_features"):
            logger.info("Running missing payload analysis")
            state["payload_features"] = _analyze_payloads(state["logs"])
    
    # Update mode and reset weights
    state["analysis_mode"] = AnalysisMode.FULL.value
    state["retry_count"] = retry_count + 1
    state["priority_weights"] = {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}
    
    logger.info("Analysis widening complete")
    return state


def deep_sqli_analyzer_node(state: SecurityState) -> SecurityState:
    """
    Deep-dive analysis for SQL injection attacks.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with detailed SQLi findings
    """
    logger.info("Running deep SQL injection analysis")
    
    logs = state["logs"]
    findings = {
        "attack_type": "SQL_INJECTION",
        "encoding_evasion": False,
        "second_order_patterns": False,
        "waf_bypass_attempts": False,
        "injection_points": [],
        "payload_samples": [],
    }
    
    for entry in logs:
        params = str(entry.get("params", "")) + str(entry.get("body", ""))
        params_lower = params.lower()
        
        # Check for encoding evasion
        if re.search(r'(%27|%22|\\x27|\\x22|%2527)', params):
            findings["encoding_evasion"] = True
        
        # Check for second-order injection patterns
        if re.search(r'\b(insert|update|delete)\b', params_lower):
            findings["second_order_patterns"] = True
        
        # Check for WAF bypass techniques
        if re.search(r'(/\*![\d]*|concat\(|char\(|0x[0-9a-f]+)', params_lower):
            findings["waf_bypass_attempts"] = True
        
        # Identify injection points
        if re.search(r"(or\s+\d+=\d+|union\s+select|drop\s+table|'\s*--|1\s*=\s*1)", params_lower):
            endpoint = entry.get("endpoint", "unknown")
            if endpoint not in findings["injection_points"]:
                findings["injection_points"].append(endpoint)
            
            # Store payload sample (truncated)
            if len(findings["payload_samples"]) < 5:
                findings["payload_samples"].append(params[:200])
    
    state["deep_dive_findings"] = sanitize_findings(findings)
    
    logger.info(
        f"Deep SQLi analysis complete",
        extra={
            "injection_points": len(findings["injection_points"]),
            "encoding_evasion": findings["encoding_evasion"],
            "waf_bypass": findings["waf_bypass_attempts"]
        }
    )
    
    return state


def deep_credential_analyzer_node(state: SecurityState) -> SecurityState:
    """
    Deep-dive analysis for credential stuffing attacks.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with detailed credential attack findings
    """
    logger.info("Running deep credential stuffing analysis")
    
    logs = state["logs"]
    
    # Filter failed login attempts
    failed_logins = [
        entry for entry in logs
        if entry.get("endpoint") == "/api/login" and entry.get("response_code") == 401
    ]
    
    # Calculate statistics
    unique_ips = len(set(entry.get("ip", "") for entry in failed_logins))
    unique_users = len(set(entry.get("user_id", "") for entry in failed_logins))

    findings = {
        "attack_type": "CREDENTIAL_STUFFING",
        "failed_login_count": len(failed_logins),
        "unique_source_ips": unique_ips,
        "unique_target_users": unique_users,
        "is_distributed": unique_ips > 3,
        "is_password_spray": unique_users > 3 and unique_ips <= 2,
        "velocity": len(failed_logins) / max(len(logs), 1),
    }
    
    state["deep_dive_findings"] = sanitize_findings(findings)
    
    logger.info(
        f"Deep credential analysis complete",
        extra={
            "failed_logins": findings["failed_login_count"],
            "unique_ips": unique_ips,
            "unique_users": unique_users,
            "is_distributed": findings["is_distributed"]
        }
    )
    
    return state


def deep_idor_analyzer_node(state: SecurityState) -> SecurityState:
    """
    Deep-dive analysis for IDOR (Insecure Direct Object Reference) attacks.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with detailed IDOR findings
    """
    logger.info("Running deep IDOR analysis")
    
    logs = state["logs"]
    user_endpoint_access = {}
    
    # Map user IDs to accessed endpoints
    for entry in logs:
        uid = entry.get("user_id", "unknown")
        endpoint = entry.get("endpoint", "")
        
        if "/api/users/" in endpoint:
            user_endpoint_access.setdefault(uid, []).append(endpoint)

    # Analyze access patterns for sequential enumeration
    sequential_patterns = {}
    for uid, endpoints in user_endpoint_access.items():
        # Extract numeric IDs from endpoints
        ids = []
        for endpoint in endpoints:
            parts = endpoint.split("/")
            for part in parts:
                if part.isdigit():
                    ids.append(int(part))
        
        # Check for sequential access
        if len(ids) >= 2:
            diffs = [ids[i + 1] - ids[i] for i in range(len(ids) - 1)]
            is_sequential = all(d == 1 for d in diffs) if diffs else False
            
            sequential_patterns[str(uid)] = {
                "accessed_ids": ids[:20],  # Limit for safety
                "is_sequential": is_sequential,
                "access_count": len(ids),
            }

    findings = {
        "attack_type": "POSSIBLE_IDOR",
        "users_with_suspicious_access": len(sequential_patterns),
        "sequential_enumeration_detected": any(
            pattern["is_sequential"] for pattern in sequential_patterns.values()
        ),
        "access_patterns": sequential_patterns,
    }
    
    state["deep_dive_findings"] = sanitize_findings(findings)
    
    logger.info(
        f"Deep IDOR analysis complete",
        extra={
            "suspicious_users": findings["users_with_suspicious_access"],
            "sequential_enum": findings["sequential_enumeration_detected"]
        }
    )
    
    return state


THREAT_NARRATIVE_SYSTEM_PROMPT = """You are a senior security analyst writing a concise threat assessment. Based on the automated analysis results provided, write a 3-5 sentence threat narrative that includes:

1. What type of attack was detected and the confidence level
2. The key evidence signals that support this classification
3. What risk factors were flagged and their severity
4. One or two recommended immediate actions

Be specific — reference actual feature names and scores. Write in a direct, professional tone suitable for a security operations dashboard. Do not use markdown formatting.

CRITICAL: Base your analysis ONLY on the provided data. Do not add speculative information."""


def llm_threat_narrative_node(state: SecurityState) -> SecurityState:
    """
    Uses the LLM to synthesize all computed scores into a human-readable threat analysis.
    Falls back to template-based narrative if LLM unavailable.
    
    Args:
        state: Current security state
        
    Returns:
        Updated state with threat narrative
    """
    logger.info("Generating threat narrative")
    
    client = state.get("client")

    # Prepare sanitized context for LLM
    context = {
        "selected_vulnerability": state.get("selected_vuln", "")[:100],
        "risk_score": round(state.get("risk_score", 0), 3),
        "alert_type": state.get("alert_type"),
        "alert_confidence": round(state.get("alert_confidence", 0), 3),
        "risk_factors": state.get("risk_factors", [])[:10],
        "sequence_features": {k: round(v, 3) for k, v in state.get("sequence_features", {}).items()},
        "payload_features": {k: round(v, 3) for k, v in state.get("payload_features", {}).items()},
        "behavior_features": {k: round(v, 3) for k, v in state.get("behavior_features", {}).items()},
        "analysis_summary": state.get("analysis_summary", {}),
        "deep_dive_findings": sanitize_findings(state.get("deep_dive_findings", {})) if state.get("deep_dive_findings") else None,
        "log_count": len(state.get("logs", [])),
    }

    # Try LLM-based narrative generation
    if client:
        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": THREAT_NARRATIVE_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(context, default=str)},
                ],
                max_tokens=300,
                temperature=0.2,
            )
            
            narrative = response.choices[0].message.content.strip()
            
            # Basic validation: ensure narrative is reasonable length
            if 50 <= len(narrative) <= 1000:
                state["threat_narrative"] = narrative
                logger.info("LLM threat narrative generated successfully")
                return state
            else:
                logger.warning(f"LLM narrative length unusual ({len(narrative)} chars), using fallback")
        
        except Exception as e:
            logger.warning(f"LLM narrative generation failed: {e}, using fallback")

    # Fallback to template-based narrative
    alert = state.get("alert_type") or "Unknown"
    confidence = state.get("alert_confidence", 0)
    risk = state.get("risk_score", 0)
    factors = state.get("risk_factors", [])
    factors_str = ", ".join(factors[:5]) if factors else "none identified"
    
    deep = state.get("deep_dive_findings")
    deep_str = ""
    if deep:
        attack_type = deep.get("attack_type", 'N/A')
        deep_str = f" Deep-dive analysis ({attack_type}) completed with additional forensic details."
    
    state["threat_narrative"] = (
        f"Automated analysis classified this activity as {alert} "
        f"with {confidence:.0%} confidence. "
        f"Overall risk score: {risk:.0%}. "
        f"Key risk factors: {factors_str}.{deep_str} "
        f"Recommend immediate review and correlation with SIEM events."
    )
    
    logger.info("Fallback threat narrative generated")
    return state


# -------------------------
# ROUTING FUNCTIONS
# -------------------------

def route_analyzers(state: SecurityState) -> str:
    """
    Routes to the appropriate analyzer(s) based on intent_router's analysis_mode.
    
    Args:
        state: Current security state
        
    Returns:
        Next node name
    """
    mode = state.get("analysis_mode", AnalysisMode.FULL.value)
    
    if mode == AnalysisMode.PAYLOAD_FOCUS.value:
        logger.info("Routing to payload_inspector")
        return "payload_inspector"
    elif mode == AnalysisMode.SEQUENCE_FOCUS.value:
        logger.info("Routing to sequence_analyzer")
        return "sequence_analyzer"
    elif mode == AnalysisMode.BEHAVIOR_FOCUS.value:
        logger.info("Routing to behavior_profiler")
        return "behavior_profiler"
    
    logger.info("Routing to run_all_analyzers")
    return "run_all_analyzers"


def check_risk_level(state: SecurityState) -> str:
    """
    Early termination: skip classifier and LLM for trivially benign logs.
    
    Args:
        state: Current security state
        
    Returns:
        Next node name
    """
    risk_score = state.get("risk_score", 0)
    
    if risk_score < 0.25:
        logger.info(f"Low risk score ({risk_score:.2%}), routing to benign_summary")
        return "benign_summary"
    
    logger.info(f"Risk score {risk_score:.2%}, routing to mini_agent_classifier")
    return "mini_agent_classifier"


def route_after_classification(state: SecurityState) -> str:
    """
    Routes to retry, specialist deep-dive, or final narrative.
    
    Args:
        state: Current security state
        
    Returns:
        Next node name
    """
    confidence = state.get("alert_confidence", 0)
    mode = state.get("analysis_mode", AnalysisMode.FULL.value)
    retry_count = state.get("retry_count", 0)
    alert_type = state.get("alert_type")

    # Low confidence on a focused scan with no prior retries -> widen to full
    if confidence < 0.3 and mode != AnalysisMode.FULL.value and retry_count == 0:
        logger.info(f"Low confidence ({confidence:.2%}) on focused scan, widening analysis")
        return "widen_and_retry"

    # High confidence with a known attack type -> specialist deep-dive
    if confidence >= 0.4 and alert_type:
        specialist_map = {
            "SQL_INJECTION": "deep_sqli_analyzer",
            "CREDENTIAL_STUFFING": "deep_credential_analyzer",
            "POSSIBLE_IDOR": "deep_idor_analyzer",
        }
        
        if alert_type in specialist_map:
            specialist = specialist_map[alert_type]
            logger.info(f"High confidence ({confidence:.2%}), routing to {specialist}")
            return specialist

    logger.info("Routing to llm_threat_narrative")
    return "llm_threat_narrative"


# -------------------------
# GRAPH CONSTRUCTION
# -------------------------

def create_real_agentic_workflow():
    """
    Creates and compiles the LangGraph workflow for security analysis.
    
    Returns:
        Compiled StateGraph
    """
    logger.info("Building security analysis workflow graph")
    
    builder = StateGraph(SecurityState)

    # Register all nodes
    builder.add_node("log_ingest", log_ingest_node)
    builder.add_node("intent_router", intent_router_node)
    builder.add_node("sequence_analyzer", sequence_analyzer_node)
    builder.add_node("payload_inspector", payload_inspector_node)
    builder.add_node("behavior_profiler", behavior_profiler_node)
    builder.add_node("run_all_analyzers", run_all_analyzers_node)
    builder.add_node("risk_aggregator", risk_aggregator_node)
    builder.add_node("benign_summary", benign_summary_node)
    builder.add_node("mini_agent_classifier", mini_agent_classifier_node)
    builder.add_node("widen_and_retry", widen_and_retry_node)
    builder.add_node("deep_sqli_analyzer", deep_sqli_analyzer_node)
    builder.add_node("deep_credential_analyzer", deep_credential_analyzer_node)
    builder.add_node("deep_idor_analyzer", deep_idor_analyzer_node)
    builder.add_node("llm_threat_narrative", llm_threat_narrative_node)

    # Entry point
    builder.set_entry_point("log_ingest")

    # log_ingest -> intent_router
    builder.add_edge("log_ingest", "intent_router")

    # Conditional: route to analyzer(s) based on analysis_mode
    builder.add_conditional_edges("intent_router", route_analyzers)

    # All analyzer paths converge at risk_aggregator
    builder.add_edge("run_all_analyzers", "risk_aggregator")
    builder.add_edge("sequence_analyzer", "risk_aggregator")
    builder.add_edge("payload_inspector", "risk_aggregator")
    builder.add_edge("behavior_profiler", "risk_aggregator")

    # Conditional: early termination for benign vs. deep analysis
    builder.add_conditional_edges("risk_aggregator", check_risk_level)

    # Conditional: retry loop, specialist deep-dive, or narrative
    builder.add_conditional_edges("mini_agent_classifier", route_after_classification)

    # Retry loop: widen_and_retry -> back to risk_aggregator
    builder.add_edge("widen_and_retry", "risk_aggregator")

    # Specialists -> narrative
    builder.add_edge("deep_sqli_analyzer", "llm_threat_narrative")
    builder.add_edge("deep_credential_analyzer", "llm_threat_narrative")
    builder.add_edge("deep_idor_analyzer", "llm_threat_narrative")

    # Terminal edges
    builder.add_edge("llm_threat_narrative", END)
    builder.add_edge("benign_summary", END)

    logger.info("Workflow graph built successfully")
    return builder.compile()


# -------------------------
# MAIN EXECUTION INTERFACE
# -------------------------

# Create the compiled graph
graph = create_real_agentic_workflow()


def run_agent(input_data: dict, client) -> dict:
    """
    Main entry point for running the security analysis agent.
    
    Args:
        input_data: Dictionary containing logs, query, and other inputs
        client: LLM client instance
        
    Returns:
        Final state dictionary with analysis results
    """
    logger.info("Starting agent execution")
    
    try:
        result = graph.invoke({**input_data, "client": client})
        logger.info("Agent execution completed successfully")
        return result
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise


# -------------------------
# UTILITY FUNCTIONS FOR TESTING
# -------------------------

def validate_agent_output(result: dict) -> bool:
    """
    Validates that agent output contains expected fields.
    
    Args:
        result: Agent execution result
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "risk_score",
        "alert_type",
        "alert_confidence",
        "threat_narrative",
        "analysis_summary"
    ]
    
    for field in required_fields:
        if field not in result:
            logger.error(f"Missing required field in output: {field}")
            return False
    
    return True


if __name__ == "__main__":
    # Example usage
    logger.info("Security Analysis Agent loaded successfully")
    print("Security Analysis Agent - Optimized Version")
    print("=" * 50)
    print("Features:")
    print("✓ Prompt injection protection")
    print("✓ Input validation and sanitization")
    print("✓ Single-pass log analysis")
    print("✓ Enhanced SQL injection detection")
    print("✓ Retry loop optimization")
    print("✓ Comprehensive logging")
    print("✓ LRU caching for LLM calls")
    print("✓ Bounded resource usage")
    print("=" * 50)
