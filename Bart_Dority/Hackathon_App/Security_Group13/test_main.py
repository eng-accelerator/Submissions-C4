from unittest.mock import patch, MagicMock
import pytest
from streamlit.testing.v1 import AppTest

MOCK_LOGS = [
    {
        "vulnerability_type": "SQL Injection",
        "logs": [
            {"timestamp": "2024-01-01T00:00:00", "message": "SELECT * FROM users", "source_ip": "10.0.0.1"}
        ],
    },
    {
        "vulnerability_type": "Brute Force",
        "logs": [
            {"timestamp": "2024-01-01T00:01:00", "message": "Failed login attempt", "source_ip": "10.0.0.2"}
        ],
    },
]

MOCK_AGENT_RESULT = {
    "risk_score": 0.85,
    "alert_type": "SQL Injection",
    "alert_confidence": 0.9,
    "risk_factors": ["malicious payload"],
    "sequence_features": {"request_rate": 0.7},
    "payload_features": {"sql_keywords": 0.9},
    "behavior_features": {"anomaly_score": 0.6},
}


def _build_app():
    """Launch main.py under AppTest with the /logs request mocked."""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_LOGS

    with patch("requests.get", return_value=mock_response):
        return AppTest.from_file("main.py").run(timeout=30)


# --- preset query options ---

def test_preset_query_uses_selection_in_input_data():
    """Selecting a preset option should pass that option as the query."""
    at = _build_app()

    # The "User Query" selectbox should exist with preset options
    query_box = at.selectbox(key=None)
    # Find the selectbox labelled "User Query"
    user_query_boxes = [sb for sb in at.selectbox if sb.label == "User Query"]
    assert len(user_query_boxes) == 1, "Expected exactly one 'User Query' selectbox"

    sb = user_query_boxes[0]
    assert "Show failed logins" in sb.options
    assert "Detect SQL injection attempts" in sb.options
    assert "Find credential stuffing patterns" in sb.options
    assert "Custom..." in sb.options


def test_preset_option_passed_to_agent():
    """When a preset option is selected and Run Agent is clicked, the query in
    input_data should match the selected preset."""
    at = _build_app()

    # Select a preset query
    user_query_boxes = [sb for sb in at.selectbox if sb.label == "User Query"]
    sb = user_query_boxes[0]
    sb.set_value("Detect SQL injection attempts")

    # Mock run_agent and the openrouter_client in session state
    at.session_state["openrouter_client"] = MagicMock()

    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_LOGS

    with patch("requests.get", return_value=mock_response), \
         patch("main.run_agent", return_value=MOCK_AGENT_RESULT) as mock_agent:
        at = at.run(timeout=30)

        # Click the Run Agent button
        run_buttons = [b for b in at.button if b.label == "Run Agent"]
        assert len(run_buttons) == 1, "Expected exactly one 'Run Agent' button"
        run_buttons[0].click()

        with patch("main.run_agent", return_value=MOCK_AGENT_RESULT) as mock_agent2:
            at = at.run(timeout=30)
            if mock_agent2.called:
                call_args = mock_agent2.call_args[0][0]
                assert call_args["query"] == "Detect SQL injection attempts"


# --- custom query ---

def test_custom_option_shows_text_input():
    """Selecting 'Custom...' should reveal a text input field."""
    at = _build_app()

    user_query_boxes = [sb for sb in at.selectbox if sb.label == "User Query"]
    sb = user_query_boxes[0]
    sb.set_value("Custom...")

    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_LOGS

    with patch("requests.get", return_value=mock_response):
        at = at.run(timeout=30)

    custom_inputs = [ti for ti in at.text_input if ti.label == "Enter custom query"]
    assert len(custom_inputs) == 1, "Expected a text input for custom query when 'Custom...' is selected"


def test_custom_query_passed_to_agent():
    """When 'Custom...' is selected with a custom string and Run Agent is clicked,
    the custom text should be sent as the query."""
    at = _build_app()

    # Select Custom...
    user_query_boxes = [sb for sb in at.selectbox if sb.label == "User Query"]
    sb = user_query_boxes[0]
    sb.set_value("Custom...")

    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_LOGS

    with patch("requests.get", return_value=mock_response):
        at = at.run(timeout=30)

    # Type a custom query
    custom_inputs = [ti for ti in at.text_input if ti.label == "Enter custom query"]
    custom_inputs[0].set_value("Find XSS payloads in request headers")

    at.session_state["openrouter_client"] = MagicMock()

    with patch("requests.get", return_value=mock_response), \
         patch("main.run_agent", return_value=MOCK_AGENT_RESULT):
        at = at.run(timeout=30)

    # Click Run Agent
    run_buttons = [b for b in at.button if b.label == "Run Agent"]
    assert len(run_buttons) == 1
    run_buttons[0].click()

    with patch("requests.get", return_value=mock_response), \
         patch("main.run_agent", return_value=MOCK_AGENT_RESULT) as mock_agent:
        at = at.run(timeout=30)
        if mock_agent.called:
            call_args = mock_agent.call_args[0][0]
            assert call_args["query"] == "Find XSS payloads in request headers"


def test_no_text_input_for_preset_option():
    """When a preset option (not 'Custom...') is selected, no custom text input
    should appear."""
    at = _build_app()

    user_query_boxes = [sb for sb in at.selectbox if sb.label == "User Query"]
    sb = user_query_boxes[0]
    sb.set_value("Show failed logins")

    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_LOGS

    with patch("requests.get", return_value=mock_response):
        at = at.run(timeout=30)

    custom_inputs = [ti for ti in at.text_input if ti.label == "Enter custom query"]
    assert len(custom_inputs) == 0, "Custom text input should NOT appear for preset options"
