import pytest
from agent import risk_aggregator_node


def _make_state(sequence_features, payload_features, behavior_features, priority_weights):
    """Build a minimal state dict with the fields risk_aggregator_node needs."""
    return {
        "sequence_features": sequence_features,
        "payload_features": payload_features,
        "behavior_features": behavior_features,
        "priority_weights": priority_weights,
    }


# ---- Default (uniform) weights ----

class TestDefaultWeights:
    """All priority multipliers are 1.0 — baseline behavior."""

    def test_risk_score_with_uniform_weights(self):
        state = _make_state(
            sequence_features={"login_velocity": 0.9, "request_frequency": 0.5},
            payload_features={"sql_injection_score": 0.8, "unexpected_field_score": 0.3},
            behavior_features={"geo_deviation_score": 0.6, "role_deviation_score": 0.4},
            priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        # max scores: sequence=0.9, payload=0.8, behavior=0.6
        # expected: 0.4*0.9 + 0.4*0.8 + 0.2*0.6 = 0.36 + 0.32 + 0.12 = 0.80
        assert result["risk_score"] == pytest.approx(0.80)

    def test_risk_factors_above_threshold(self):
        state = _make_state(
            sequence_features={"login_velocity": 0.9, "request_frequency": 0.5},
            payload_features={"sql_injection_score": 0.8, "unexpected_field_score": 0.3},
            behavior_features={"geo_deviation_score": 0.6, "role_deviation_score": 0.4},
            priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        assert "login_velocity" in result["risk_factors"]
        assert "sql_injection_score" in result["risk_factors"]
        assert "request_frequency" not in result["risk_factors"]
        assert "geo_deviation_score" not in result["risk_factors"]


# ---- Payload-boosted weights (sql query) ----

class TestPayloadBoostedWeights:
    """Simulates intent_router setting payload weight to 1.5 for SQL-related queries."""

    def test_payload_boost_increases_risk_score(self):
        features = dict(
            sequence_features={"login_velocity": 0.9, "request_frequency": 0.5},
            payload_features={"sql_injection_score": 0.95, "unexpected_field_score": 0.3},
            behavior_features={"geo_deviation_score": 0.6, "role_deviation_score": 0.4},
        )

        baseline = risk_aggregator_node(_make_state(
            **features, priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        ))
        boosted = risk_aggregator_node(_make_state(
            **features, priority_weights={"sequence": 1.0, "payload": 1.5, "behavior": 1.0},
        ))

        assert boosted["risk_score"] > baseline["risk_score"]

    def test_payload_boost_exact_value(self):
        state = _make_state(
            sequence_features={"login_velocity": 0.9},
            payload_features={"sql_injection_score": 0.95},
            behavior_features={"geo_deviation_score": 0.6},
            priority_weights={"sequence": 1.0, "payload": 1.5, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        # 0.4*1.0*0.9 + 0.4*1.5*0.95 + 0.2*1.0*0.6 = 0.36 + 0.57 + 0.12 = 1.05
        assert result["risk_score"] == pytest.approx(1.05)


# ---- Sequence-boosted weights (credential/login query) ----

class TestSequenceBoostedWeights:
    """Simulates intent_router setting sequence weight to 1.5 for login-related queries."""

    def test_sequence_boost_increases_risk_score(self):
        features = dict(
            sequence_features={"login_velocity": 0.9, "request_frequency": 0.7},
            payload_features={"sql_injection_score": 0.1, "unexpected_field_score": 0.1},
            behavior_features={"geo_deviation_score": 0.6, "role_deviation_score": 0.4},
        )

        baseline = risk_aggregator_node(_make_state(
            **features, priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        ))
        boosted = risk_aggregator_node(_make_state(
            **features, priority_weights={"sequence": 1.5, "payload": 1.0, "behavior": 1.0},
        ))

        assert boosted["risk_score"] > baseline["risk_score"]

    def test_sequence_boost_exact_value(self):
        state = _make_state(
            sequence_features={"login_velocity": 0.9},
            payload_features={"sql_injection_score": 0.1},
            behavior_features={"geo_deviation_score": 0.6},
            priority_weights={"sequence": 1.5, "payload": 1.0, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        # 0.4*1.5*0.9 + 0.4*1.0*0.1 + 0.2*1.0*0.6 = 0.54 + 0.04 + 0.12 = 0.70
        assert result["risk_score"] == pytest.approx(0.70)


# ---- Behavior-boosted weights ----

class TestBehaviorBoostedWeights:
    """Simulates intent_router setting behavior weight to 1.5."""

    def test_behavior_boost_increases_risk_score(self):
        features = dict(
            sequence_features={"login_velocity": 0.5},
            payload_features={"sql_injection_score": 0.5},
            behavior_features={"user_agent_anomaly_score": 0.8},
        )

        baseline = risk_aggregator_node(_make_state(
            **features, priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        ))
        boosted = risk_aggregator_node(_make_state(
            **features, priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.5},
        ))

        assert boosted["risk_score"] > baseline["risk_score"]


# ---- Edge cases ----

class TestEdgeCases:
    def test_all_zero_scores(self):
        state = _make_state(
            sequence_features={"a": 0.0},
            payload_features={"b": 0.0},
            behavior_features={"c": 0.0},
            priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        assert result["risk_score"] == pytest.approx(0.0)
        assert result["risk_factors"] == []

    def test_all_max_scores(self):
        state = _make_state(
            sequence_features={"a": 1.0},
            payload_features={"b": 1.0},
            behavior_features={"c": 1.0},
            priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        # 0.4 + 0.4 + 0.2 = 1.0
        assert result["risk_score"] == pytest.approx(1.0)
        assert set(result["risk_factors"]) == {"a", "b", "c"}

    def test_risk_factors_threshold_boundary(self):
        """Score of exactly 0.7 should NOT be included (threshold is > 0.7)."""
        state = _make_state(
            sequence_features={"exactly_threshold": 0.7},
            payload_features={"above_threshold": 0.71},
            behavior_features={"below_threshold": 0.69},
            priority_weights={"sequence": 1.0, "payload": 1.0, "behavior": 1.0},
        )
        result = risk_aggregator_node(state)

        assert "exactly_threshold" not in result["risk_factors"]
        assert "above_threshold" in result["risk_factors"]
        assert "below_threshold" not in result["risk_factors"]
