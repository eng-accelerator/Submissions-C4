import unittest
from unittest.mock import patch

from pipeline.orchestrator import create_pipeline_state, run_pipeline, AgentState


def _agent_ok(agent_id):
    def _run(context):
        context[f"{agent_id}_output"] = {"ok": True}
        context.setdefault("trace", []).append(agent_id)
        return context

    return _run


def _agent_fail(_context):
    raise RuntimeError("simulated agent failure")


class PipelineSmokeTests(unittest.TestCase):
    def test_pipeline_happy_path(self):
        registry = [
            {"id": "a1", "name": "Agent 1", "run": _agent_ok("a1")},
            {"id": "a2", "name": "Agent 2", "run": _agent_ok("a2")},
            {"id": "a3", "name": "Agent 3", "run": _agent_ok("a3")},
        ]
        with patch("pipeline.orchestrator.AGENT_REGISTRY", registry):
            state = create_pipeline_state()
            seen = []
            started = []
            ended = []

            final = run_pipeline(
                query="test query",
                state=state,
                initial_context={"retrieval_mode": "hybrid"},
                on_state_change=lambda s: seen.append((s.current_agent_index, s.is_complete, s.has_error)),
                before_agent_run=lambda agent_id: started.append(agent_id),
                after_agent_run=lambda agent_id: ended.append(agent_id),
            )

        self.assertTrue(final.is_complete)
        self.assertFalse(final.has_error)
        self.assertEqual(final.context.get("query"), "test query")
        self.assertEqual(final.context.get("retrieval_mode"), "hybrid")
        self.assertEqual(final.context.get("trace"), ["a1", "a2", "a3"])
        self.assertEqual(started, ["a1", "a2", "a3"])
        self.assertEqual(ended, ["a1", "a2", "a3"])
        self.assertTrue(len(seen) > 0)
        for agent in final.agents:
            self.assertEqual(agent.state, AgentState.COMPLETE)

    def test_pipeline_stops_on_agent_failure(self):
        registry = [
            {"id": "a1", "name": "Agent 1", "run": _agent_ok("a1")},
            {"id": "a2", "name": "Agent 2", "run": _agent_fail},
            {"id": "a3", "name": "Agent 3", "run": _agent_ok("a3")},
        ]
        with patch("pipeline.orchestrator.AGENT_REGISTRY", registry):
            state = create_pipeline_state()
            started = []
            ended = []
            final = run_pipeline(
                query="test query",
                state=state,
                before_agent_run=lambda agent_id: started.append(agent_id),
                after_agent_run=lambda agent_id: ended.append(agent_id),
            )

        self.assertTrue(final.has_error)
        self.assertFalse(final.is_complete)
        self.assertEqual(final.context["pipeline_error"]["agent"], "a2")
        self.assertIn("simulated agent failure", final.context["pipeline_error"]["error"])
        self.assertEqual(started, ["a1", "a2"])
        self.assertEqual(ended, ["a1", "a2"])
        self.assertEqual(final.agents[0].state, AgentState.COMPLETE)
        self.assertEqual(final.agents[1].state, AgentState.ERROR)
        self.assertEqual(final.agents[2].state, AgentState.NOT_STARTED)


if __name__ == "__main__":
    unittest.main()
