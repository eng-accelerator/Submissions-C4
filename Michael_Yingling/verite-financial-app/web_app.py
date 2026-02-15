"""
Flask Web Application for Multi-Agent Financial Advisor
Provides a user-friendly web interface for document upload and analysis
"""

from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import secrets
from financial_advisor_app import FinancialAdvisorOrchestrator, FinancialData
import traceback

# Try to import optional dependencies
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("Warning: PyPDF2 not installed. PDF parsing will not work.")

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    print("Warning: python-docx not installed. DOCX parsing will not work.")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not installed. CSV/Excel parsing will not work.")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'docx', 'csv', 'xlsx'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Check if using OpenRouter
USE_OPENROUTER = os.environ.get('USE_OPENROUTER', 'false').lower() == 'true'

# Global orchestrator instance (in production, use proper session management)
orchestrators = {}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def extract_text_from_file(filepath):
    """Extract text content from various file formats"""
    ext = filepath.rsplit('.', 1)[1].lower()
    
    try:
        if ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == 'pdf':
            if not HAS_PDF:
                return None
            text = ""
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        
        elif ext == 'docx':
            if not HAS_DOCX:
                return None
            doc = docx.Document(filepath)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        elif ext in ['csv', 'xlsx']:
            if not HAS_PANDAS:
                return None
            df = pd.read_excel(filepath) if ext == 'xlsx' else pd.read_csv(filepath)
            return df.to_string()
        
        else:
            return None
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
        traceback.print_exc()
        return None


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/test')
def test_page():
    """Test dashboard page"""
    import os
    test_file = os.path.join(os.path.dirname(__file__), 'test_dashboard.html')
    with open(test_file, 'r') as f:
        return f.read()


@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Handle document upload and parsing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from file
        document_text = extract_text_from_file(filepath)
        
        if not document_text:
            os.remove(filepath)
            return jsonify({'error': 'Failed to extract text from document'}), 500
        
        print(f"\n{'='*60}")
        print(f"DOCUMENT UPLOADED: {filename}")
        print(f"{'='*60}")
        print(f"Extracted text length: {len(document_text)} characters")
        print(f"First 500 chars: {document_text[:500]}")
        print(f"{'='*60}\n")
        
        # Initialize orchestrator for this session
        session_id = session.get('session_id', secrets.token_hex(16))
        session['session_id'] = session_id
        
        orchestrator = FinancialAdvisorOrchestrator(use_openrouter=USE_OPENROUTER)
        orchestrators[session_id] = orchestrator
        
        # Parse document
        print("Calling parse_documents...")
        financial_data = orchestrator.parse_documents(document_text)
        
        print(f"\n{'='*60}")
        print("PARSED FINANCIAL DATA:")
        print(f"{'='*60}")
        print(f"Monthly Income: ${financial_data.monthly_income:,.2f}")
        print(f"Expenses: {financial_data.expenses}")
        print(f"Debts: {len(financial_data.debts)} debt(s)")
        print(f"Savings: ${financial_data.savings:,.2f}")
        print(f"Investments: {financial_data.investments}")
        print(f"Goals: {financial_data.financial_goals}")
        print(f"{'='*60}\n")
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Document parsed successfully',
            'data': {
                'monthly_income': financial_data.monthly_income,
                'expenses': financial_data.expenses,
                'debts': financial_data.debts,
                'savings': financial_data.savings,
                'investments': financial_data.investments,
                'goals': financial_data.financial_goals
            }
        })
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/analyze/<agent_type>', methods=['POST'])
def analyze(agent_type):
    """Run specific agent analysis"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in orchestrators:
        return jsonify({'error': 'No financial data available. Please upload a document first.'}), 400
    
    orchestrator = orchestrators[session_id]
    data = request.json or {}
    
    try:
        if agent_type == 'debt':
            result = orchestrator.analyze_debt()
        elif agent_type == 'savings':
            goals = data.get('goals')
            result = orchestrator.create_savings_strategy(goals)
        elif agent_type == 'budget':
            result = orchestrator.optimize_budget()
        elif agent_type == 'investment':
            risk_tolerance = data.get('risk_tolerance', 'moderate')
            result = orchestrator.investment_advice(risk_tolerance)
        elif agent_type == 'tax':
            result = orchestrator.tax_optimization()
        elif agent_type == 'emergency':
            result = orchestrator.emergency_fund_plan()
        elif agent_type == 'comprehensive':
            result = orchestrator.comprehensive_financial_plan()
        else:
            return jsonify({'error': 'Invalid agent type'}), 400
        
        # Ensure result is JSON serializable
        if isinstance(result, dict):
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': True, 'data': {'response': str(result)}})
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in analyze endpoint: {error_details}")
        return jsonify({
            'error': str(e),
            'details': 'Check server logs for more information'
        }), 500


@app.route('/api/test-data', methods=['POST'])
def create_test_data():
    """Create test financial data for debugging"""
    session_id = session.get('session_id', secrets.token_hex(16))
    session['session_id'] = session_id
    
    orchestrator = FinancialAdvisorOrchestrator(use_openrouter=USE_OPENROUTER)
    
    # Create test data
    financial_data = FinancialData(
        monthly_income=6600.0,
        expenses={
            "Rent": 1800.0,
            "Utilities": 150.0,
            "Groceries": 600.0,
            "Transportation": 300.0,
            "Insurance": 200.0,
            "Entertainment": 250.0,
            "Dining Out": 400.0,
            "Subscriptions": 85.0,
            "Phone": 70.0,
            "Internet": 60.0
        },
        debts=[
            {
                "name": "Credit Card A",
                "balance": 8500.0,
                "interest_rate": 18.99,
                "minimum_payment": 170.0,
                "type": "credit_card"
            },
            {
                "name": "Credit Card B",
                "balance": 3200.0,
                "interest_rate": 22.50,
                "minimum_payment": 80.0,
                "type": "credit_card"
            },
            {
                "name": "Student Loan",
                "balance": 28000.0,
                "interest_rate": 4.5,
                "minimum_payment": 310.0,
                "type": "student_loan"
            },
            {
                "name": "Car Loan",
                "balance": 12000.0,
                "interest_rate": 6.2,
                "minimum_payment": 280.0,
                "type": "auto_loan"
            }
        ],
        savings=3700.0,
        investments={
            "401k": 18500.0,
            "IRA": 8200.0
        },
        financial_goals=[
            "Pay off high-interest credit cards",
            "Build 6-month emergency fund",
            "Save for house down payment"
        ]
    )
    
    orchestrator.financial_data = financial_data
    orchestrators[session_id] = orchestrator
    
    print(f"\n{'='*60}")
    print("TEST DATA CREATED")
    print(f"{'='*60}")
    print(f"Session ID: {session_id}")
    print(f"Monthly Income: ${financial_data.monthly_income:,.2f}")
    print(f"Total Expenses: ${sum(financial_data.expenses.values()):,.2f}")
    print(f"Total Debts: {len(financial_data.debts)}")
    print(f"{'='*60}\n")
    
    return jsonify({
        'success': True,
        'message': 'Test data created successfully',
        'session_id': session_id
    })


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get financial summary"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in orchestrators:
        return jsonify({'error': 'No financial data available'}), 400
    
    orchestrator = orchestrators[session_id]
    
    if not orchestrator.financial_data:
        return jsonify({'error': 'No financial data parsed yet'}), 400
    
    summary = orchestrator._generate_summary()
    return jsonify({'success': True, 'data': summary})


@app.route('/api/manual-input', methods=['POST'])
def manual_input():
    """Accept manual financial data input"""
    data = request.json
    
    session_id = session.get('session_id', secrets.token_hex(16))
    session['session_id'] = session_id
    
    orchestrator = FinancialAdvisorOrchestrator(use_openrouter=USE_OPENROUTER)
    
    # Create FinancialData from manual input
    financial_data = FinancialData(
        monthly_income=float(data.get('monthly_income', 0)),
        expenses=data.get('expenses', {}),
        debts=data.get('debts', []),
        savings=float(data.get('savings', 0)),
        investments=data.get('investments', {}),
        financial_goals=data.get('goals', []),
        tax_bracket=data.get('tax_bracket')
    )
    
    orchestrator.financial_data = financial_data
    orchestrators[session_id] = orchestrator
    
    return jsonify({
        'success': True,
        'message': 'Financial data saved successfully'
    })


@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler to return JSON errors"""
    print(f"Unhandled exception: {e}")
    traceback.print_exc()
    
    return jsonify({
        'error': str(e),
        'type': type(e).__name__,
        'message': 'An unexpected error occurred. Check server logs for details.'
    }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏦 Vérité Financial - Multi-Agent AI Advisor")
    print("="*60)
    
    # Show API configuration
    if USE_OPENROUTER:
        print("\n🌐 API: OpenRouter")
        model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        print(f"   Model: {model}")
        print(f"   API Key: {'✅ Set' if os.environ.get('OPENROUTER_API_KEY') else '❌ Missing'}")
    else:
        print("\n🤖 API: Anthropic (Direct)")
        print("   Model: claude-sonnet-4-20250514")
        print(f"   API Key: {'✅ Set' if os.environ.get('ANTHROPIC_API_KEY') else '❌ Missing'}")
    
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nMissing libraries:")
    if not HAS_PDF:
        print("  ⚠️  PyPDF2 - PDF parsing disabled")
    if not HAS_DOCX:
        print("  ⚠️  python-docx - DOCX parsing disabled")
    if not HAS_PANDAS:
        print("  ⚠️  pandas - CSV/Excel parsing disabled")
    if HAS_PDF and HAS_DOCX and HAS_PANDAS:
        print("  ✅ All libraries installed!")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5003)
