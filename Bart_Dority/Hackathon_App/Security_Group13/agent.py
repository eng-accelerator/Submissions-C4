import json
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END


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
# ANALYSIS HELPERS (pure functions, no state mutation)
# -------------------------

def _analyze_sequences(logs):
    login_velocity = max(
        (0.9 if e.get("endpoint") == "/api/login" and e.get("response_code") == 401 else 0.1 for e in logs),
        default=0.1,
    )
    sequential_object_access = max(
        (0.85 if "/api/users/" in e.get("endpoint", "") else 0.1 for e in logs),
        default=0.1,
    )
    request_frequency = min(len(logs) / 10.0, 1.0)
    repeated_action_score = max(
        (0.8 if e.get("endpoint") == "/api/orders" else 0.1 for e in logs),
        default=0.1,
    )
    return {
        "login_velocity": login_velocity,
        "sequential_object_access": sequential_object_access,
        "request_frequency": request_frequency,
        "repeated_action_score": repeated_action_score,
    }


def _analyze_payloads(logs):
    sql_injection_score = 0.1
    unexpected_field_score = 0.1
    for e in logs:
        params = str(e.get("params", "")) + str(e.get("body", ""))
        if "OR 1=1" in params or "UNION SELECT" in params:
            sql_injection_score = 0.95
        if "isAdmin" in params or "role" in params:
            unexpected_field_score = 0.9
    return {
        "sql_injection_score": sql_injection_score,
        "unexpected_field_score": unexpected_field_score,
        "command_injection_score": 0.1,
    }


def _analyze_behavior(logs):
    role_deviation_score = max(
        (0.75 if e.get("user_id") == 456 else 0.2 for e in logs),
        default=0.2,
    )
    user_agent_anomaly_score = max(
        (0.8 if "sqlmap" in e.get("user_agent", "") else 0.2 for e in logs),
        default=0.2,
    )
    return {
        "geo_deviation_score": 0.6,
        "role_deviation_score": role_deviation_score,
        "user_agent_anomaly_score": user_agent_anomaly_score,
    }


# -------------------------
# NODES
# -------------------------

def _keyword_fallback(query: str) -> dict:
    """Keyword-matching logic used when the LLM is unavailable."""
    result = {
        "analysis_mode": "full",
        "priority_weights": {"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        "explanation_level": "standard",
    }
    if "sql" in query:
        result["analysis_mode"] = "payload_focus"
        result["priority_weights"]["payload"] = 1.5
    elif "credential" in query or "login" in query:
        result["analysis_mode"] = "sequence_focus"
        result["priority_weights"]["sequence"] = 1.5
    elif "behavior" in query:
        result["analysis_mode"] = "behavior_focus"
        result["priority_weights"]["behavior"] = 1.5
    if "explain" in query:
        result["explanation_level"] = "detailed"
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
- Set explanation_level to "detailed" if the user asks for explanations or reasoning"""


def intent_router_node(state: SecurityState) -> SecurityState:
    query = (state.get("query") or "").lower()
    client = state.get("client")
    logs = state.get('logs')

    state["analysis_mode"] = "full"
    state["priority_weights"] = {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}
    state["explanation_level"] = "standard"

    if not query.strip():
        return state

    if client:
        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": INTENT_ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                    {"role": "user", "content": logs}
                ],
                max_tokens=150,
                temperature=0,
            )
            parsed = json.loads(response.choices[0].message.content)
            state["analysis_mode"] = parsed.get("analysis_mode", "full")
            weights = parsed.get("priority_weights", {})
            state["priority_weights"] = {
                "sequence": float(weights.get("sequence", 1.0)),
                "payload": float(weights.get("payload", 1.0)),
                "behavior": float(weights.get("behavior", 1.0)),
            }
            state["explanation_level"] = parsed.get("explanation_level", "standard")
            return state
        except Exception:
            pass

    fallback = _keyword_fallback(query)
    state["analysis_mode"] = fallback["analysis_mode"]
    state["priority_weights"] = fallback["priority_weights"]
    state["explanation_level"] = fallback["explanation_level"]
    return state


def log_ingest_node(state: SecurityState) -> SecurityState:
    state["logs"] = state.get("logs", [])
    state["selected_vuln"] = state.get("selected_vuln", "")
    state["retry_count"] = 0
    return state


def sequence_analyzer_node(state: SecurityState) -> SecurityState:
    state["sequence_features"] = _analyze_sequences(state["logs"])
    return state


def payload_inspector_node(state: SecurityState) -> SecurityState:
    state["payload_features"] = _analyze_payloads(state["logs"])
    return state


def behavior_profiler_node(state: SecurityState) -> SecurityState:
    state["behavior_features"] = _analyze_behavior(state["logs"])
    return state


def run_all_analyzers_node(state: SecurityState) -> SecurityState:
    state["sequence_features"] = _analyze_sequences(state["logs"])
    state["payload_features"] = _analyze_payloads(state["logs"])
    state["behavior_features"] = _analyze_behavior(state["logs"])
    return state


def risk_aggregator_node(state: SecurityState) -> SecurityState:
    sf = state.get("sequence_features") or DEFAULT_SEQUENCE_FEATURES
    pf = state.get("payload_features") or DEFAULT_PAYLOAD_FEATURES
    bf = state.get("behavior_features") or DEFAULT_BEHAVIOR_FEATURES

    state["sequence_features"] = sf
    state["payload_features"] = pf
    state["behavior_features"] = bf

    sequence_score = max(sf.values())
    payload_score = max(pf.values())
    behavior_score = max(bf.values())

    weights = state.get("priority_weights") or {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}

    sequence_weight = 0.4 * weights["sequence"]
    payload_weight = 0.4 * weights["payload"]
    behavior_weight = 0.2 * weights["behavior"]

    state["risk_score"] = min(
        sequence_weight * sequence_score
        + payload_weight * payload_score
        + behavior_weight * behavior_score,
        1.0,
    )

    combined = {**sf, **pf, **bf}
    state["risk_factors"] = [k for k, v in combined.items() if v > 0.7]

    return state


def mini_agent_classifier_node(state: SecurityState) -> SecurityState:
    sf = state["sequence_features"]
    pf = state["payload_features"]
    bf = state["behavior_features"]
    risk_score = state["risk_score"]

    hypothesis_definitions = {
        "SQL_INJECTION": {
            "primary": ("sql_injection_score", pf.get("sql_injection_score", 0)),
            "support_keys": ["unexpected_field_score", "user_agent_anomaly_score"],
            "contradict_keys": ["login_velocity", "sequential_object_access"],
        },
        "CREDENTIAL_STUFFING": {
            "primary": ("login_velocity", sf.get("login_velocity", 0)),
            "support_keys": ["request_frequency", "geo_deviation_score"],
            "contradict_keys": ["sql_injection_score", "sequential_object_access"],
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
    }

    all_features = {**sf, **pf, **bf}

    evaluated = []
    for label, defn in hypothesis_definitions.items():
        primary_name, primary_score = defn["primary"]
        if primary_score <= 0.5:
            continue

        evidence = {"support": [primary_name], "contradict": [], "score": primary_score}

        for key in defn["support_keys"]:
            val = all_features.get(key, 0)
            if val > 0.5:
                evidence["support"].append(key)
                evidence["score"] += 0.1

        for key in defn["contradict_keys"]:
            val = all_features.get(key, 0)
            if val > 0.7:
                evidence["contradict"].append(key)
                evidence["score"] -= 0.15

        evidence["score"] = max(evidence["score"], 0) * risk_score
        evaluated.append((label, evidence))

    if not evaluated:
        state["alert_type"] = None
        state["alert_confidence"] = 0.0
        state["analysis_summary"] = {
            "selected_alert": None,
            "confidence": 0.0,
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }
        return state

    evaluated.sort(key=lambda x: x[1]["score"], reverse=True)
    top_label, top_evidence = evaluated[0]

    if len(evaluated) >= 2 and abs(evaluated[0][1]["score"] - evaluated[1][1]["score"]) <= 0.1:
        top_label = "MULTI_VECTOR_ATTACK"

    state["alert_type"] = top_label
    state["alert_confidence"] = top_evidence["score"]
    state["analysis_summary"] = {
        "selected_alert": top_label,
        "confidence": top_evidence["score"],
        "supporting_evidence": top_evidence["support"],
        "contradicting_evidence": top_evidence["contradict"],
    }
    return state


def benign_summary_node(state: SecurityState) -> SecurityState:
    state["alert_type"] = None
    state["alert_confidence"] = 0.0
    state["risk_factors"] = state.get("risk_factors", [])
    state["analysis_summary"] = {
        "selected_alert": None,
        "confidence": 0.0,
        "supporting_evidence": [],
        "contradicting_evidence": [],
    }
    state["threat_narrative"] = (
        f"Activity appears benign. Risk score: {state.get('risk_score', 0):.0%}. "
        "No significant threat indicators detected across analyzed dimensions."
    )
    return state


def widen_and_retry_node(state: SecurityState) -> SecurityState:
    """Widens a focused scan to full analysis when initial confidence is too low."""
    state["analysis_mode"] = "full"
    state["retry_count"] = state.get("retry_count", 0) + 1
    state["priority_weights"] = {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}
    state["sequence_features"] = _analyze_sequences(state["logs"])
    state["payload_features"] = _analyze_payloads(state["logs"])
    state["behavior_features"] = _analyze_behavior(state["logs"])
    return state


def deep_sqli_analyzer_node(state: SecurityState) -> SecurityState:
    logs = state["logs"]
    findings = {
        "attack_type": "SQL_INJECTION",
        "encoding_evasion": False,
        "second_order_patterns": False,
        "waf_bypass_attempts": False,
        "injection_points": [],
        "payload_samples": [],
    }
    for e in logs:
        params = str(e.get("params", "")) + str(e.get("body", ""))
        if "%27" in params or "%22" in params or "\\x27" in params:
            findings["encoding_evasion"] = True
        if "INSERT" in params.upper() or "UPDATE" in params.upper():
            findings["second_order_patterns"] = True
        if "/*!50000" in params or "/*!" in params or "concat(" in params.lower():
            findings["waf_bypass_attempts"] = True
        if any(kw in params.upper() for kw in ["OR 1=1", "UNION SELECT", "DROP TABLE", "' --", "1=1"]):
            findings["injection_points"].append(e.get("endpoint", "unknown"))
            findings["payload_samples"].append(params[:200])
    state["deep_dive_findings"] = findings
    return state


def deep_credential_analyzer_node(state: SecurityState) -> SecurityState:
    logs = state["logs"]
    failed_logins = [
        e for e in logs
        if e.get("endpoint") == "/api/login" and e.get("response_code") == 401
    ]
    unique_ips = len(set(e.get("ip", "") for e in failed_logins))
    unique_users = len(set(e.get("user_id", "") for e in failed_logins))

    findings = {
        "attack_type": "CREDENTIAL_STUFFING",
        "failed_login_count": len(failed_logins),
        "unique_source_ips": unique_ips,
        "unique_target_users": unique_users,
        "is_distributed": unique_ips > 3,
        "is_password_spray": unique_users > 3 and unique_ips <= 2,
        "velocity": len(failed_logins) / max(len(logs), 1),
    }
    state["deep_dive_findings"] = findings
    return state


def deep_idor_analyzer_node(state: SecurityState) -> SecurityState:
    logs = state["logs"]
    user_endpoint_access = {}
    for e in logs:
        uid = e.get("user_id", "unknown")
        ep = e.get("endpoint", "")
        if "/api/users/" in ep:
            user_endpoint_access.setdefault(uid, []).append(ep)

    sequential_patterns = {}
    for uid, endpoints in user_endpoint_access.items():
        ids = []
        for ep in endpoints:
            parts = ep.split("/")
            for part in parts:
                if part.isdigit():
                    ids.append(int(part))
        if len(ids) >= 2:
            diffs = [ids[i + 1] - ids[i] for i in range(len(ids) - 1)]
            sequential_patterns[str(uid)] = {
                "accessed_ids": ids,
                "is_sequential": all(d == 1 for d in diffs) if diffs else False,
            }

    findings = {
        "attack_type": "POSSIBLE_IDOR",
        "users_with_suspicious_access": len(sequential_patterns),
        "sequential_enumeration_detected": any(
            p["is_sequential"] for p in sequential_patterns.values()
        ),
        "access_patterns": sequential_patterns,
    }
    state["deep_dive_findings"] = findings
    return state


THREAT_NARRATIVE_SYSTEM_PROMPT = """You are a senior security analyst writing a concise threat assessment. Based on the automated analysis results provided, write a 3-5 sentence threat narrative that includes:

1. What type of attack was detected and the confidence level
2. The key evidence signals that support this classification
3. What risk factors were flagged and their severity
4. One or two recommended immediate actions

Be specific — reference actual feature names and scores. Write in a direct, professional tone suitable for a security operations dashboard. Do not use markdown formatting."""


def llm_threat_narrative_node(state: SecurityState) -> SecurityState:
    """Uses the LLM to synthesize all computed scores into a human-readable threat analysis."""
    client = state.get("client")

    context = {
        "selected_vulnerability": state.get("selected_vuln"),
        "risk_score": state.get("risk_score"),
        "alert_type": state.get("alert_type"),
        "alert_confidence": state.get("alert_confidence"),
        "risk_factors": state.get("risk_factors"),
        "sequence_features": state.get("sequence_features"),
        "payload_features": state.get("payload_features"),
        "behavior_features": state.get("behavior_features"),
        "analysis_summary": state.get("analysis_summary"),
        "deep_dive_findings": state.get("deep_dive_findings"),
        "log_count": len(state.get("logs", [])),
        "query": state.get("query"),
    }

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
            state["threat_narrative"] = response.choices[0].message.content
            return state
        except Exception:
            pass

    alert = state.get("alert_type") or "Unknown"
    confidence = state.get("alert_confidence", 0)
    risk = state.get("risk_score", 0)
    factors = state.get("risk_factors", [])
    factors_str = ", ".join(factors) if factors else "none identified"
    deep = state.get("deep_dive_findings")
    deep_str = ""
    if deep:
        deep_str = f" Deep-dive analysis ({deep.get('attack_type', 'N/A')}) performed."
    state["threat_narrative"] = (
        f"Automated analysis classified this activity as {alert} "
        f"with {confidence:.0%} confidence. "
        f"Overall risk score: {risk:.0%}. "
        f"Key risk factors: {factors_str}.{deep_str}"
    )
    return state


# -------------------------
# ROUTING FUNCTIONS
# -------------------------

def route_analyzers(state: SecurityState) -> str:
    """Routes to the appropriate analyzer(s) based on intent_router's analysis_mode."""
    mode = state.get("analysis_mode", "full")
    if mode == "payload_focus":
        return "payload_inspector"
    elif mode == "sequence_focus":
        return "sequence_analyzer"
    elif mode == "behavior_focus":
        return "behavior_profiler"
    return "run_all_analyzers"


def check_risk_level(state: SecurityState) -> str:
    """Early termination: skip classifier and LLM for trivially benign logs."""
    if state.get("risk_score", 0) < 0.25:
        return "benign_summary"
    return "mini_agent_classifier"


def route_after_classification(state: SecurityState) -> str:
    """Routes to retry, specialist deep-dive, or final narrative."""
    confidence = state.get("alert_confidence", 0)
    mode = state.get("analysis_mode", "full")
    retry_count = state.get("retry_count", 0)
    alert_type = state.get("alert_type")

    # Low confidence on a focused scan with no prior retries -> widen to full
    if confidence < 0.3 and mode != "full" and retry_count == 0:
        return "widen_and_retry"

    # High confidence with a known attack type -> specialist deep-dive
    if confidence >= 0.4 and alert_type:
        specialist_map = {
            "SQL_INJECTION": "deep_sqli_analyzer",
            "CREDENTIAL_STUFFING": "deep_credential_analyzer",
            "POSSIBLE_IDOR": "deep_idor_analyzer",
        }
        if alert_type in specialist_map:
            return specialist_map[alert_type]

    return "llm_threat_narrative"


# -------------------------
# GRAPH CONSTRUCTION
# -------------------------

def create_real_agentic_workflow():
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

    return builder.compile()


# -------------------------
# SEND FINDINGS BACK TO UI
# -------------------------

graph = create_real_agentic_workflow()


def run_agent(input_data: dict, client):
    return graph.invoke({**input_data, "client": client})
