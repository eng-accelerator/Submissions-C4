"""Tests for the Astraeus CLI interface."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import build_parser, _C, list_agents


class TestCLIParser(unittest.TestCase):
    """Test argument parsing."""

    def test_basic_query(self):
        parser = build_parser()
        args = parser.parse_args(["What is RAG?"])
        self.assertEqual(args.query, "What is RAG?")
        self.assertEqual(args.mode, "hybrid")
        self.assertFalse(args.verbose)
        self.assertFalse(args.json_output)
        self.assertIsNone(args.output)
        self.assertIsNone(args.model)

    def test_output_flag(self):
        parser = build_parser()
        args = parser.parse_args(["test query", "--output", "report.md"])
        self.assertEqual(args.output, "report.md")

    def test_output_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["test query", "-o", "out.md"])
        self.assertEqual(args.output, "out.md")

    def test_mode_local(self):
        parser = build_parser()
        args = parser.parse_args(["test", "--mode", "local"])
        self.assertEqual(args.mode, "local")

    def test_mode_web(self):
        parser = build_parser()
        args = parser.parse_args(["test", "-m", "web"])
        self.assertEqual(args.mode, "web")

    def test_mode_invalid(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["test", "--mode", "invalid"])

    def test_model_override(self):
        parser = build_parser()
        args = parser.parse_args(["test", "--model", "anthropic/claude-3-haiku"])
        self.assertEqual(args.model, "anthropic/claude-3-haiku")

    def test_json_flag(self):
        parser = build_parser()
        args = parser.parse_args(["test", "--json"])
        self.assertTrue(args.json_output)

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["test", "-v"])
        self.assertTrue(args.verbose)

    def test_no_color_flag(self):
        parser = build_parser()
        args = parser.parse_args(["test", "--no-color"])
        self.assertTrue(args.no_color)

    def test_list_agents_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--list-agents"])
        self.assertTrue(args.list_agents)

    def test_all_flags_combined(self):
        parser = build_parser()
        args = parser.parse_args([
            "complex query here",
            "--output", "out.md",
            "--mode", "hybrid",
            "--model", "openai/gpt-4o",
            "--json",
            "--verbose",
            "--no-color",
        ])
        self.assertEqual(args.query, "complex query here")
        self.assertEqual(args.output, "out.md")
        self.assertEqual(args.mode, "hybrid")
        self.assertEqual(args.model, "openai/gpt-4o")
        self.assertTrue(args.json_output)
        self.assertTrue(args.verbose)
        self.assertTrue(args.no_color)

    def test_no_query_no_list(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.query)
        self.assertFalse(args.list_agents)


class TestCLIColors(unittest.TestCase):
    """Test ANSI color handling."""

    def test_colors_have_escape_codes(self):
        self.assertIn("\033[", _C.BOLD)
        self.assertIn("\033[", _C.GREEN)
        self.assertIn("\033[", _C.RESET)

    def test_disable_colors(self):
        # Save originals
        orig_bold = _C.BOLD
        orig_green = _C.GREEN

        _C.disable()
        self.assertEqual(_C.BOLD, "")
        self.assertEqual(_C.GREEN, "")
        self.assertEqual(_C.RESET, "")

        # Restore
        _C.BOLD = orig_bold
        _C.GREEN = orig_green
        _C.RESET = "\033[0m"


class TestCLIListAgents(unittest.TestCase):
    """Test list-agents output."""

    def test_list_agents_runs(self):
        """list_agents() should print without errors."""
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            list_agents()

        output = buf.getvalue()
        self.assertIn("Research Coordinator", output)
        self.assertIn("Contextual Retriever", output)
        self.assertIn("Critical Analysis", output)
        self.assertIn("Fact-Checker", output)
        self.assertIn("Insight Generator", output)
        self.assertIn("Report Builder", output)


class TestCLIMain(unittest.TestCase):
    """Test the main() entry point."""

    def test_main_no_args_returns_1(self):
        from cli import main
        # No query and no --list-agents should return 1
        ret = main([])
        self.assertEqual(ret, 1)

    def test_main_list_agents_returns_0(self):
        from cli import main
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["--list-agents"])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
