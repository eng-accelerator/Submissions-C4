import pytest
from agent import (
    # Helpers
    _analyze_sequences,
    _analyze_payloads,
    _analyze_behavior,
    _keyword_fallback,
    # Nodes
    log_ingest_node,
    intent_router_node,
    sequence_analyzer_node,
    payload_inspector_node,
    behavior_profiler_node,
    run_all_analyzers_node,
    risk_aggregator_node,
    mini_agent_classifier_node,
    benign_summary_node,
    widen_and_retry_node,
    deep_sqli_analyzer_node,
    deep_credential_analyzer_node,
    deep_idor_analyzer_node,
    llm_threat_narrative_node,
    # Routing
    route_analyzers,
    check_risk_level,
    route_after_classification,
    # Defaults
    DEFAULT_SEQUENCE_FEATURES,
    DEFAULT_PAYLOAD_FEATURES,
    DEFAULT_BEHAVIOR_FEATURES,
    # End-to-end
    run_agent,
)


# -------------------------
# TEST FIXTURES
# -------------------------

SQL_INJECTION_LOGS = [
    {
        "endpoint": "/api/users",
        "params": "id=1 OR 1=1",
        "body": "",
        "response_code": 200,
        "user_id": 123,
        "user_agent": "sqlmap/1.4",
    },
]

CREDENTIAL_STUFFING_LOGS = [
    {"endpoint": "/api/login", "response_code": 401, "user_id": 789, "user_agent": "Mozilla/5.0", "params": "", "body": "", "ip": "10.0.0.1"},
    {"endpoint": "/api/login", "response_code": 401, "user_id": 790, "user_agent": "Mozilla/5.0", "params": "", "body": "", "ip": "10.0.0.2"},
    {"endpoint": "/api/login", "response_code": 401, "user_id": 791, "user_agent": "Mozilla/5.0", "params": "", "body": "", "ip": "10.0.0.3"},
    {"endpoint": "/api/login", "response_code": 401, "user_id": 792, "user_agent": "Mozilla/5.0", "params": "", "body": "", "ip": "10.0.0.4"},
    {"endpoint": "/api/login", "response_code": 401, "user_id": 793, "user_agent": "Mozilla/5.0", "params": "", "body": "", "ip": "10.0.0.5"},
]

IDOR_LOGS = [
    {"endpoint": "/api/users/1", "response_code": 200, "user_id": 456, "user_agent": "Mozilla/5.0", "params": "", "body": ""},
    {"endpoint": "/api/users/2", "response_code": 200, "user_id": 456, "user_agent": "Mozilla/5.0", "params": "", "body": ""},
    {"endpoint": "/api/users/3", "response_code": 200, "user_id": 456, "user_agent": "Mozilla/5.0", "params": "", "body": ""},
    {"endpoint": "/api/users/4", "response_code": 200, "user_id": 456, "user_agent": "Mozilla/5.0", "params": "", "body": ""},
]

BENIGN_LOGS = [
    {"endpoint": "/api/products", "response_code": 200, "user_id": 101, "user_agent": "Mozilla/5.0", "params": "", "body": ""},
]


# =========================================================
# 1. ANALYSIS HELPER TESTS
# =========================================================

class TestAnalyzeSequences:
    def test_detects_login_velocity(self):
        logs = [{"endpoint": "/api/login", "response_code": 401}]
        result = _analyze_sequences(logs)
        assert result["login_velocity"] == 0.9

    def test_detects_sequential_object_access(self):
        logs = [{"endpoint": "/api/users/5"}]
        result = _analyze_sequences(logs)
        assert result["sequential_object_access"] == 0.85

    def test_computes_request_frequency(self):
        logs = [{"endpoint": "/api/foo"} for _ in range(20)]
        result = _analyze_sequences(logs)
        assert result["request_frequency"] == 1.0

    def test_detects_repeated_action(self):
        logs = [{"endpoint": "/api/orders"}]
        result = _analyze_sequences(logs)
        assert result["repeated_action_score"] == 0.8

    def test_benign_defaults(self):
        logs = [{"endpoint": "/api/products", "response_code": 200}]
        result = _analyze_sequences(logs)
        assert result["login_velocity"] == 0.1
        assert result["sequential_object_access"] == 0.1
        assert result["repeated_action_score"] == 0.1

    def test_empty_logs(self):
        result = _analyze_sequences([])
        assert result["login_velocity"] == 0.1
        assert result["request_frequency"] == 0.0


class TestAnalyzePayloads:
    def test_detects_sql_injection(self):
        logs = [{"params": "id=1 OR 1=1", "body": ""}]
        result = _analyze_payloads(logs)
        assert result["sql_injection_score"] == 0.95

    def test_detects_union_select(self):
        logs = [{"params": "id=1 UNION SELECT * FROM users", "body": ""}]
        result = _analyze_payloads(logs)
        assert result["sql_injection_score"] == 0.95

    def test_detects_unexpected_fields(self):
        logs = [{"params": "", "body": '{"isAdmin": true}'}]
        result = _analyze_payloads(logs)
        assert result["unexpected_field_score"] == 0.9

    def test_benign_payloads(self):
        logs = [{"params": "page=1", "body": ""}]
        result = _analyze_payloads(logs)
        assert result["sql_injection_score"] == 0.1
        assert result["unexpected_field_score"] == 0.1


class TestAnalyzeBehavior:
    def test_detects_sqlmap_user_agent(self):
        logs = [{"user_agent": "sqlmap/1.4", "user_id": 123}]
        result = _analyze_behavior(logs)
        assert result["user_agent_anomaly_score"] == 0.8

    def test_detects_role_deviation(self):
        logs = [{"user_id": 456, "user_agent": "Mozilla/5.0"}]
        result = _analyze_behavior(logs)
        assert result["role_deviation_score"] == 0.75

    def test_benign_behavior(self):
        logs = [{"user_id": 101, "user_agent": "Mozilla/5.0"}]
        result = _analyze_behavior(logs)
        assert result["role_deviation_score"] == 0.2
        assert result["user_agent_anomaly_score"] == 0.2


# =========================================================
# 2. ROUTING FUNCTION TESTS
# =========================================================

class TestRouteAnalyzers:
    def test_full_mode(self):
        assert route_analyzers({"analysis_mode": "full"}) == "run_all_analyzers"

    def test_default_mode(self):
        assert route_analyzers({}) == "run_all_analyzers"

    def test_payload_focus(self):
        assert route_analyzers({"analysis_mode": "payload_focus"}) == "payload_inspector"

    def test_sequence_focus(self):
        assert route_analyzers({"analysis_mode": "sequence_focus"}) == "sequence_analyzer"

    def test_behavior_focus(self):
        assert route_analyzers({"analysis_mode": "behavior_focus"}) == "behavior_profiler"


class TestCheckRiskLevel:
    def test_benign_threshold(self):
        assert check_risk_level({"risk_score": 0.1}) == "benign_summary"

    def test_just_below_threshold(self):
        assert check_risk_level({"risk_score": 0.24}) == "benign_summary"

    def test_exactly_at_threshold(self):
        assert check_risk_level({"risk_score": 0.25}) == "mini_agent_classifier"

    def test_high_risk(self):
        assert check_risk_level({"risk_score": 0.8}) == "mini_agent_classifier"

    def test_missing_score(self):
        assert check_risk_level({}) == "benign_summary"


class TestRouteAfterClassification:
    def test_retry_on_low_confidence_focused(self):
        state = {
            "alert_confidence": 0.1,
            "analysis_mode": "payload_focus",
            "retry_count": 0,
            "alert_type": None,
        }
        assert route_after_classification(state) == "widen_and_retry"

    def test_no_retry_when_full_mode(self):
        state = {
            "alert_confidence": 0.1,
            "analysis_mode": "full",
            "retry_count": 0,
            "alert_type": None,
        }
        assert route_after_classification(state) == "llm_threat_narrative"

    def test_no_retry_after_first_attempt(self):
        state = {
            "alert_confidence": 0.1,
            "analysis_mode": "payload_focus",
            "retry_count": 1,
            "alert_type": None,
        }
        assert route_after_classification(state) == "llm_threat_narrative"

    def test_specialist_sqli(self):
        state = {
            "alert_confidence": 0.6,
            "analysis_mode": "full",
            "retry_count": 0,
            "alert_type": "SQL_INJECTION",
        }
        assert route_after_classification(state) == "deep_sqli_analyzer"

    def test_specialist_credential_stuffing(self):
        state = {
            "alert_confidence": 0.5,
            "analysis_mode": "full",
            "retry_count": 0,
            "alert_type": "CREDENTIAL_STUFFING",
        }
        assert route_after_classification(state) == "deep_credential_analyzer"

    def test_specialist_idor(self):
        state = {
            "alert_confidence": 0.5,
            "analysis_mode": "full",
            "retry_count": 0,
            "alert_type": "POSSIBLE_IDOR",
        }
        assert route_after_classification(state) == "deep_idor_analyzer"

    def test_no_specialist_for_business_logic(self):
        state = {
            "alert_confidence": 0.6,
            "analysis_mode": "full",
            "retry_count": 0,
            "alert_type": "BUSINESS_LOGIC_ABUSE",
        }
        assert route_after_classification(state) == "llm_threat_narrative"

    def test_narrative_on_moderate_confidence(self):
        state = {
            "alert_confidence": 0.35,
            "analysis_mode": "full",
            "retry_count": 0,
            "alert_type": "SQL_INJECTION",
        }
        assert route_after_classification(state) == "llm_threat_narrative"


# =========================================================
# 3. NODE TESTS
# =========================================================

class TestLogIngestNode:
    def test_initializes_defaults(self):
        state = {}
        result = log_ingest_node(state)
        assert result["logs"] == []
        assert result["selected_vuln"] == ""
        assert result["retry_count"] == 0

    def test_preserves_existing_logs(self):
        state = {"logs": [{"endpoint": "/test"}], "selected_vuln": "SQLi"}
        result = log_ingest_node(state)
        assert len(result["logs"]) == 1
        assert result["selected_vuln"] == "SQLi"


class TestIntentRouterNode:
    def test_empty_query_defaults_to_full(self):
        state = {"query": "", "client": None}
        result = intent_router_node(state)
        assert result["analysis_mode"] == "full"
        assert result["priority_weights"] == {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}

    def test_keyword_fallback_sql(self):
        state = {"query": "detect sql injection", "client": None}
        result = intent_router_node(state)
        assert result["analysis_mode"] == "payload_focus"
        assert result["priority_weights"]["payload"] == 1.5

    def test_keyword_fallback_credential(self):
        state = {"query": "find credential stuffing", "client": None}
        result = intent_router_node(state)
        assert result["analysis_mode"] == "sequence_focus"

    def test_keyword_fallback_login(self):
        state = {"query": "show failed login attempts", "client": None}
        result = intent_router_node(state)
        assert result["analysis_mode"] == "sequence_focus"

    def test_keyword_fallback_behavior(self):
        state = {"query": "check for unusual behavior", "client": None}
        result = intent_router_node(state)
        assert result["analysis_mode"] == "behavior_focus"


class TestRunAllAnalyzersNode:
    def test_populates_all_features(self):
        state = {"logs": SQL_INJECTION_LOGS}
        result = run_all_analyzers_node(state)
        assert "sequence_features" in result
        assert "payload_features" in result
        assert "behavior_features" in result
        assert result["payload_features"]["sql_injection_score"] == 0.95


class TestRiskAggregatorNode:
    def test_fills_defaults_for_missing_features(self):
        state = {
            "payload_features": {"sql_injection_score": 0.95, "unexpected_field_score": 0.1, "command_injection_score": 0.1},
            "priority_weights": {"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        }
        result = risk_aggregator_node(state)
        assert result["sequence_features"] == DEFAULT_SEQUENCE_FEATURES
        assert result["behavior_features"] == DEFAULT_BEHAVIOR_FEATURES
        assert result["risk_score"] > 0

    def test_risk_score_capped_at_one(self):
        state = {
            "sequence_features": {"login_velocity": 1.0, "sequential_object_access": 1.0, "request_frequency": 1.0, "repeated_action_score": 1.0},
            "payload_features": {"sql_injection_score": 1.0, "unexpected_field_score": 1.0, "command_injection_score": 1.0},
            "behavior_features": {"geo_deviation_score": 1.0, "role_deviation_score": 1.0, "user_agent_anomaly_score": 1.0},
            "priority_weights": {"sequence": 2.0, "payload": 2.0, "behavior": 2.0},
        }
        result = risk_aggregator_node(state)
        assert result["risk_score"] <= 1.0

    def test_identifies_risk_factors(self):
        state = {
            "sequence_features": {"login_velocity": 0.9, "sequential_object_access": 0.1, "request_frequency": 0.1, "repeated_action_score": 0.1},
            "payload_features": {"sql_injection_score": 0.95, "unexpected_field_score": 0.1, "command_injection_score": 0.1},
            "behavior_features": {"geo_deviation_score": 0.2, "role_deviation_score": 0.2, "user_agent_anomaly_score": 0.8},
            "priority_weights": {"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        }
        result = risk_aggregator_node(state)
        assert "login_velocity" in result["risk_factors"]
        assert "sql_injection_score" in result["risk_factors"]
        assert "user_agent_anomaly_score" in result["risk_factors"]


class TestBenignSummaryNode:
    def test_sets_benign_fields(self):
        state = {"risk_score": 0.05, "risk_factors": []}
        result = benign_summary_node(state)
        assert result["alert_type"] is None
        assert result["alert_confidence"] == 0.0
        assert "benign" in result["threat_narrative"].lower()


class TestWidenAndRetryNode:
    def test_increments_retry_count(self):
        state = {"logs": BENIGN_LOGS, "retry_count": 0, "analysis_mode": "payload_focus"}
        result = widen_and_retry_node(state)
        assert result["retry_count"] == 1
        assert result["analysis_mode"] == "full"

    def test_resets_weights(self):
        state = {"logs": BENIGN_LOGS, "retry_count": 0, "priority_weights": {"sequence": 1.0, "payload": 1.5, "behavior": 1.0}}
        result = widen_and_retry_node(state)
        assert result["priority_weights"] == {"sequence": 1.0, "payload": 1.0, "behavior": 1.0}

    def test_runs_all_analyzers(self):
        state = {"logs": SQL_INJECTION_LOGS, "retry_count": 0}
        result = widen_and_retry_node(state)
        assert "sequence_features" in result
        assert "payload_features" in result
        assert "behavior_features" in result


# =========================================================
# 4. SPECIALIST NODE TESTS
# =========================================================

class TestDeepSqliAnalyzer:
    def test_finds_injection_points(self):
        state = {"logs": SQL_INJECTION_LOGS}
        result = deep_sqli_analyzer_node(state)
        findings = result["deep_dive_findings"]
        assert findings["attack_type"] == "SQL_INJECTION"
        assert len(findings["injection_points"]) > 0

    def test_detects_encoding_evasion(self):
        logs = [{"params": "id=%27 OR 1=1", "body": "", "endpoint": "/api/users"}]
        state = {"logs": logs}
        result = deep_sqli_analyzer_node(state)
        assert result["deep_dive_findings"]["encoding_evasion"] is True

    def test_no_false_positives_on_benign(self):
        state = {"logs": BENIGN_LOGS}
        result = deep_sqli_analyzer_node(state)
        findings = result["deep_dive_findings"]
        assert len(findings["injection_points"]) == 0
        assert findings["encoding_evasion"] is False


class TestDeepCredentialAnalyzer:
    def test_counts_failed_logins(self):
        state = {"logs": CREDENTIAL_STUFFING_LOGS}
        result = deep_credential_analyzer_node(state)
        findings = result["deep_dive_findings"]
        assert findings["attack_type"] == "CREDENTIAL_STUFFING"
        assert findings["failed_login_count"] == 5

    def test_detects_distributed_attack(self):
        state = {"logs": CREDENTIAL_STUFFING_LOGS}
        result = deep_credential_analyzer_node(state)
        findings = result["deep_dive_findings"]
        assert findings["unique_source_ips"] == 5
        assert findings["is_distributed"] is True

    def test_calculates_velocity(self):
        state = {"logs": CREDENTIAL_STUFFING_LOGS}
        result = deep_credential_analyzer_node(state)
        assert result["deep_dive_findings"]["velocity"] == 1.0


class TestDeepIdorAnalyzer:
    def test_detects_sequential_access(self):
        state = {"logs": IDOR_LOGS}
        result = deep_idor_analyzer_node(state)
        findings = result["deep_dive_findings"]
        assert findings["attack_type"] == "POSSIBLE_IDOR"
        assert findings["sequential_enumeration_detected"] is True
        assert findings["users_with_suspicious_access"] > 0

    def test_no_false_positives_on_benign(self):
        state = {"logs": BENIGN_LOGS}
        result = deep_idor_analyzer_node(state)
        findings = result["deep_dive_findings"]
        assert findings["users_with_suspicious_access"] == 0
        assert findings["sequential_enumeration_detected"] is False


class TestLlmThreatNarrativeNode:
    def test_fallback_without_client(self):
        state = {
            "client": None,
            "alert_type": "SQL_INJECTION",
            "alert_confidence": 0.8,
            "risk_score": 0.7,
            "risk_factors": ["sql_injection_score"],
            "logs": [],
        }
        result = llm_threat_narrative_node(state)
        assert "SQL_INJECTION" in result["threat_narrative"]
        assert "80%" in result["threat_narrative"]

    def test_includes_deep_dive_in_fallback(self):
        state = {
            "client": None,
            "alert_type": "SQL_INJECTION",
            "alert_confidence": 0.8,
            "risk_score": 0.7,
            "risk_factors": [],
            "deep_dive_findings": {"attack_type": "SQL_INJECTION"},
            "logs": [],
        }
        result = llm_threat_narrative_node(state)
        assert "Deep-dive" in result["threat_narrative"]


# =========================================================
# 5. END-TO-END PIPELINE TESTS
# =========================================================

class TestEndToEndPipeline:
    def test_sqli_full_pipeline(self):
        """SQL injection logs with targeted query -> payload_focus -> specialist deep-dive."""
        result = run_agent(
            {"logs": SQL_INJECTION_LOGS, "query": "detect sql injection", "selected_vuln": "SQLi"},
            client=None,
        )
        assert result["alert_type"] in ("SQL_INJECTION", "MULTI_VECTOR_ATTACK")
        assert result["risk_score"] > 0.3
        assert result.get("deep_dive_findings") is not None
        assert result["threat_narrative"] is not None

    def test_credential_stuffing_pipeline(self):
        """Credential stuffing logs with login query -> sequence_focus -> specialist."""
        result = run_agent(
            {"logs": CREDENTIAL_STUFFING_LOGS, "query": "show failed login attempts", "selected_vuln": "Credential Stuffing"},
            client=None,
        )
        assert result["alert_type"] in ("CREDENTIAL_STUFFING", "MULTI_VECTOR_ATTACK")
        assert result["risk_score"] > 0.3
        assert result["threat_narrative"] is not None

    def test_benign_early_termination(self):
        """Benign logs should trigger early termination (benign_summary)."""
        result = run_agent(
            {"logs": BENIGN_LOGS, "query": "", "selected_vuln": ""},
            client=None,
        )
        assert result["alert_type"] is None
        assert result["alert_confidence"] == 0.0
        assert result["risk_score"] < 0.25
        assert "benign" in result["threat_narrative"].lower()

    def test_full_mode_no_query(self):
        """No query defaults to full analysis mode."""
        result = run_agent(
            {"logs": SQL_INJECTION_LOGS, "query": "", "selected_vuln": "SQLi"},
            client=None,
        )
        assert result["analysis_mode"] == "full"
        assert result["risk_score"] > 0

    def test_idor_pipeline(self):
        """IDOR logs should trigger POSSIBLE_IDOR classification."""
        result = run_agent(
            {"logs": IDOR_LOGS, "query": "", "selected_vuln": "IDOR"},
            client=None,
        )
        assert result["risk_score"] > 0.15
        assert result["alert_type"] is not None

    def test_retry_loop_triggers_on_weak_focused_scan(self):
        """Focused scan on ambiguous logs should widen and retry.

        These logs have an 'unexpected_field_score' signal (role in params)
        which raises the risk above the benign threshold, but the primary
        sql_injection_score stays low. The classifier finds no strong
        hypothesis -> low confidence -> retry with full mode.
        """
        ambiguous_logs = [
            {"endpoint": "/api/users", "response_code": 200, "user_id": 101, "user_agent": "Mozilla/5.0", "params": "role=admin", "body": ""},
            {"endpoint": "/api/users", "response_code": 200, "user_id": 102, "user_agent": "Mozilla/5.0", "params": "role=manager", "body": ""},
        ]
        result = run_agent(
            {"logs": ambiguous_logs, "query": "detect sql injection", "selected_vuln": "None"},
            client=None,
        )
        # After retry, mode should be widened to "full"
        assert result["analysis_mode"] == "full"
        assert result["retry_count"] == 1

    def test_pipeline_preserves_all_expected_keys(self):
        """The result should contain all keys the UI expects."""
        result = run_agent(
            {"logs": SQL_INJECTION_LOGS, "query": "", "selected_vuln": "SQLi"},
            client=None,
        )
        expected_keys = [
            "risk_score", "alert_type", "alert_confidence",
            "risk_factors", "threat_narrative",
            "sequence_features", "payload_features", "behavior_features",
        ]
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"


class TestKeywordFallback:
    def test_sql_keyword(self):
        result = _keyword_fallback("check for sql issues")
        assert result["analysis_mode"] == "payload_focus"

    def test_credential_keyword(self):
        result = _keyword_fallback("credential stuffing detection")
        assert result["analysis_mode"] == "sequence_focus"

    def test_login_keyword(self):
        result = _keyword_fallback("login brute force")
        assert result["analysis_mode"] == "sequence_focus"

    def test_behavior_keyword(self):
        result = _keyword_fallback("behavior anomaly")
        assert result["analysis_mode"] == "behavior_focus"

    def test_explain_flag(self):
        result = _keyword_fallback("explain the threats")
        assert result["explanation_level"] == "detailed"

    def test_generic_query(self):
        result = _keyword_fallback("analyze everything")
        assert result["analysis_mode"] == "full"
