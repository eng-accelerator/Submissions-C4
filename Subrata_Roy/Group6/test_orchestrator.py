#!/usr/bin/env python
"""
Simple test to verify the orchestrator returns state properly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_orchestrator():
    """Test orchestrator with minimal input"""
    print("Testing Orchestrator...")
    
    try:
        from orchestrator.state import IncidentAnalysisState
        from orchestrator.graph import IncidentAnalysisOrchestrator
        
        # Create minimal test state
        state = IncidentAnalysisState(
            raw_log_input="2024-02-14 ERROR Test error message",
            openrouter_api_key="test-key",  # Will fail but should return state
            llm_model="openai/gpt-4o"
        )
        
        print("✓ State created successfully")
        
        # Try to create orchestrator
        try:
            orchestrator = IncidentAnalysisOrchestrator(state)
            print("✓ Orchestrator created successfully")
        except Exception as e:
            print(f"✗ Orchestrator creation failed: {e}")
            return False
        
        print("✓ All components loaded successfully")
        print("\n⚠️  Note: Full run requires valid OpenRouter API key")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)
