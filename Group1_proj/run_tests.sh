#!/bin/bash
# Test Execution Script for Cybersecurity Orchestrator
# This script provides convenient commands to run various test suites

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         Cybersecurity Orchestrator - Test Suite Runner                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}Project Directory:${NC} $SCRIPT_DIR"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found. Creating...${NC}"
    python3.12 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Display menu
echo -e "${BLUE}Available Test Commands:${NC}"
echo ""
echo "1. Run ALL tests"
echo "   python test_orchestrator.py"
echo ""
echo "2. Run specific feature tests:"
echo "   python -m unittest test_orchestrator.TestThreatDetectionAndAnalysis -v"
echo "   python -m unittest test_orchestrator.TestVulnerabilityAnalysis -v"
echo "   python -m unittest test_orchestrator.TestIncidentResponse -v"
echo "   python -m unittest test_orchestrator.TestComplianceEvaluation -v"
echo "   python -m unittest test_orchestrator.TestFullAuditability -v"
echo ""
echo "3. Run individual test case:"
echo "   python -m unittest test_orchestrator.TestThreatDetectionAndAnalysis.test_threat_detection_pass_valid_alert -v"
echo ""
echo "4. Run with coverage (if coverage is installed):"
echo "   python -m coverage run -m unittest test_orchestrator"
echo "   python -m coverage report"
echo "   python -m coverage html  # Generate HTML report"
echo ""

# Ask user what they want to do
read -p "Enter command number (1-4) or 'q' to quit: " choice

case $choice in
    1)
        echo -e "${GREEN}Running ALL tests...${NC}"
        python test_orchestrator.py
        ;;
    2)
        echo -e "${BLUE}Running feature-specific tests${NC}"
        read -p "Select feature (TD=Threat, VA=Vulnerability, IR=Incident, CE=Compliance, AU=Auditability): " feature
        case $feature in
            TD)
                python -m unittest test_orchestrator.TestThreatDetectionAndAnalysis -v
                ;;
            VA)
                python -m unittest test_orchestrator.TestVulnerabilityAnalysis -v
                ;;
            IR)
                python -m unittest test_orchestrator.TestIncidentResponse -v
                ;;
            CE)
                python -m unittest test_orchestrator.TestComplianceEvaluation -v
                ;;
            AU)
                python -m unittest test_orchestrator.TestFullAuditability -v
                ;;
            *)
                echo "Invalid feature selected"
                ;;
        esac
        ;;
    3)
        echo -e "${BLUE}Running individual test case${NC}"
        read -p "Enter full test case name (e.g., test_threat_detection_pass_valid_alert): " testname
        python -m unittest test_orchestrator.$testname -v
        ;;
    4)
        echo -e "${BLUE}Running tests with coverage${NC}"
        python -m coverage run -m unittest test_orchestrator
        python -m coverage report
        ;;
    q)
        echo "Exiting..."
        deactivate
        exit 0
        ;;
    *)
        echo "Invalid option"
        deactivate
        exit 1
        ;;
esac

# Deactivate virtual environment
deactivate
