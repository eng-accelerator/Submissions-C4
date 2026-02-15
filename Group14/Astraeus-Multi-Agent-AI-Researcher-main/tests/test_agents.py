"""Tests for individual agent modules."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCoordinatorAgent(unittest.TestCase):
    """Test the Research Coordinator agent."""

    def test_import(self):
        from agents.coordinator import run as coordinator_run
        self.assertTrue(callable(coordinator_run))

    def test_basic_query_processing(self):
        from agents.coordinator import run as coordinator_run
        context = {"query": "What is machine learning?"}
        result = coordinator_run(context)
        self.assertIsInstance(result, dict)
        self.assertIn("query", result)

    def test_empty_query_handled(self):
        from agents.coordinator import run as coordinator_run
        context = {"query": ""}
        result = coordinator_run(context)
        self.assertIsInstance(result, dict)


class TestRetrieverAgent(unittest.TestCase):
    """Test the Contextual Retriever agent."""

    def test_import(self):
        from agents.retriever import run as retriever_run
        self.assertTrue(callable(retriever_run))

    def test_retriever_without_docs(self):
        from agents.retriever import run as retriever_run
        context = {
            "query": "test query",
            "expanded_queries": ["test query"],
            "retrieval_mode": "local",
        }
        result = retriever_run(context)
        self.assertIsInstance(result, dict)


class TestCriticalAnalysisAgent(unittest.TestCase):
    """Test the Critical Analysis agent."""

    def test_import(self):
        from agents.critical_analysis import run as critical_run
        self.assertTrue(callable(critical_run))

    def test_analysis_with_empty_sources(self):
        from agents.critical_analysis import run as critical_run
        context = {
            "query": "test",
            "retrieved_chunks": [],
        }
        result = critical_run(context)
        self.assertIsInstance(result, dict)


class TestFactCheckerAgent(unittest.TestCase):
    """Test the Fact-Checker agent."""

    def test_import(self):
        from agents.fact_checker import run as fact_check_run
        self.assertTrue(callable(fact_check_run))

    def test_fact_check_no_claims(self):
        from agents.fact_checker import run as fact_check_run
        context = {
            "query": "test",
            "claims": [],
            "retrieved_chunks": [],
        }
        result = fact_check_run(context)
        self.assertIsInstance(result, dict)


class TestInsightGeneratorAgent(unittest.TestCase):
    """Test the Insight Generator agent."""

    def test_import(self):
        from agents.insight_generator import run as insight_run
        self.assertTrue(callable(insight_run))


class TestReportBuilderAgent(unittest.TestCase):
    """Test the Report Builder agent."""

    def test_import(self):
        from agents.report_builder import run as report_run
        self.assertTrue(callable(report_run))


class TestReportChatAgent(unittest.TestCase):
    """Test the Report Chat agent."""

    def test_import(self):
        from agents.report_chat import render_chat_widget
        self.assertTrue(callable(render_chat_widget))


class TestConfig(unittest.TestCase):
    """Test configuration module."""

    def test_config_defaults(self):
        import config
        self.assertEqual(config.APP_TITLE, "Astraeus")
        self.assertIsInstance(config.AGENTS, list)
        self.assertEqual(len(config.AGENTS), 6)
        self.assertEqual(config.EMBEDDING_MODEL, "all-MiniLM-L6-v2")

    def test_agent_definitions(self):
        import config
        for agent in config.AGENTS:
            self.assertIn("id", agent)
            self.assertIn("name", agent)
            self.assertIn("color", agent)


class TestVectorStore(unittest.TestCase):
    """Test custom vector store."""

    def test_import(self):
        from rag.vector_store import get_collection_count
        self.assertTrue(callable(get_collection_count))


if __name__ == "__main__":
    unittest.main()
