#!/usr/bin/env python3
"""
Setup and Quick Start Script for Multi-Agent Financial Advisor
"""

import os
import sys
import subprocess
import platform


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_python_version():
    """Check if Python version is 3.8+"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install required packages"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def check_api_key():
    """Check if API key is set"""
    print("\nChecking for Anthropic API key...")
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ API key found in environment")
        return True
    else:
        print("⚠️  No API key found in environment")
        print("\n💡 To set your API key:")
        if platform.system() == "Windows":
            print("   set ANTHROPIC_API_KEY=your-api-key-here")
        else:
            print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\n   Get your API key from: https://console.anthropic.com/")
        return False


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    directories = ['uploads', 'static/css', 'static/js', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Directories created")


def run_test():
    """Run a simple test"""
    print("\nRunning quick test...")
    try:
        from financial_advisor_app import FinancialData, FinancialAdvisorOrchestrator
        print("✅ Core modules imported successfully")
        
        # Test data creation
        data = FinancialData(monthly_income=5000.0, savings=1000.0)
        print("✅ Data structure working")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def print_usage_instructions():
    """Print usage instructions"""
    print_header("SETUP COMPLETE! 🎉")
    
    print("📚 Quick Start Options:\n")
    
    print("1️⃣  WEB INTERFACE (Recommended)")
    print("   python web_app.py")
    print("   Then open: http://localhost:5000")
    print("")
    
    print("2️⃣  COMMAND LINE DEMO")
    print("   python financial_advisor_app.py")
    print("")
    
    print("3️⃣  EXAMPLE USAGE SCRIPTS")
    print("   python example_usage.py")
    print("")
    
    print("\n📖 Documentation:")
    print("   • README.md - Complete documentation")
    print("   • example_usage.py - Code examples")
    print("")
    
    print("\n🔧 Configuration:")
    print("   • Set ANTHROPIC_API_KEY environment variable")
    print("   • Modify system prompts in financial_advisor_app.py")
    print("   • Customize UI in templates/ and static/")
    print("")
    
    print("\n💡 Tips:")
    print("   • Upload any financial document (PDF, DOCX, CSV, etc.)")
    print("   • Or enter data manually through the web interface")
    print("   • Try different agents for specialized advice")
    print("   • Run comprehensive analysis for complete plan")
    print("")


def main():
    """Main setup function"""
    print_header("MULTI-AGENT FINANCIAL ADVISOR - SETUP")
    
    print("This script will help you set up the financial advisor system.\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    install_result = install_dependencies()
    if not install_result:
        print("\n⚠️  Continue anyway? Some features may not work. (y/n)")
        if input().lower() != 'y':
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check API key
    has_api_key = check_api_key()
    
    # Run tests
    if has_api_key:
        run_test()
    else:
        print("\n⚠️  Skipping tests (no API key)")
    
    # Print instructions
    print_usage_instructions()
    
    print("=" * 70)
    print("\n🚀 Ready to start! Choose an option above to begin.\n")


if __name__ == "__main__":
    main()
