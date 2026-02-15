#!/usr/bin/env python
"""
Test script to verify DevOps Incident Analysis Suite installation.
Run this to check if all dependencies are properly installed.
"""

import sys
from typing import List, Tuple


def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        return True, f"✅ {package_name or module_name}"
    except ImportError as e:
        return False, f"❌ {package_name or module_name}: {str(e)}"


def main():
    print("=" * 70)
    print("DevOps Incident Analysis Suite - Installation Test")
    print("=" * 70)
    print()
    
    # Test Python version
    print("Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"⚠️  Python {version.major}.{version.minor}.{version.micro} (Recommended: 3.12+)")
    print()
    
    # Test core dependencies
    print("Testing core dependencies...")
    tests = [
        ("langchain", "langchain"),
        ("langchain_core", "langchain-core"),
        ("langchain_openai", "langchain-openai"),
        ("langgraph", "langgraph"),
        ("pydantic", "pydantic"),
        ("streamlit", "streamlit"),
        ("requests", "requests"),
        ("httpx", "httpx"),
        ("jira", "jira"),
        ("dotenv", "python-dotenv"),
    ]
    
    results: List[Tuple[bool, str]] = []
    for module, package in tests:
        success, message = test_import(module, package)
        results.append((success, message))
        print(f"  {message}")
    
    print()
    
    # Test project modules
    print("Testing project modules...")
    project_tests = [
        ("agents.log_classifier", "Log Classifier Agent"),
        ("agents.remediation", "Remediation Agent"),
        ("agents.cookbook", "Cookbook Agent"),
        ("agents.notification", "Notification Agent"),
        ("agents.jira_ticket", "JIRA Ticket Agent"),
        ("orchestrator.state", "State Models"),
        ("orchestrator.graph", "LangGraph Orchestrator"),
        ("utils.llm_client", "LLM Client"),
        ("utils.api_clients", "API Clients"),
        ("ui.streamlit_app", "Streamlit UI"),
    ]
    
    for module, name in project_tests:
        success, message = test_import(module, name)
        results.append((success, message))
        print(f"  {message}")
    
    print()
    
    # Summary
    print("=" * 70)
    total = len(results)
    passed = sum(1 for success, _ in results if success)
    failed = total - passed
    
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    
    if failed == 0:
        print()
        print("🎉 All tests passed! Your installation is ready.")
        print()
        print("Next steps:")
        print("  1. Get your OpenRouter API key from https://openrouter.ai/")
        print("  2. Run: python main.py")
        print("  3. Open http://localhost:8501 in your browser")
        print()
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
