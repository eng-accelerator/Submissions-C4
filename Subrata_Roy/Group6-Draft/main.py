"""
Main entry point for DevOps Incident Analysis Suite
Launches the Streamlit UI application
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Path to Streamlit app
    app_path = project_root / "ui" / "streamlit_app.py"
    
    # Launch Streamlit
    sys.argv = ["streamlit", "run", str(app_path), "--server.port=8501", "--server.address=127.0.0.1"]
    sys.exit(stcli.main())
