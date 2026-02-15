# 🏦 Vérité Financial - Multi-Agent AI Advisor

An **exceptionally beautiful** and sophisticated AI-powered financial planning application featuring a luxury-inspired interface with specialized Claude agents for comprehensive wealth management.

## ✨ Design Philosophy

**Vérité Financial** combines cutting-edge AI technology with refined aesthetics:

- 🎨 **Distinctive Typography** - Elegant Cormorant Garamond serif paired with modern Outfit sans-serif
- 🌌 **Sophisticated Color Palette** - Deep midnight blues, gold accents, and rose gold highlights
- ✨ **Glassmorphism & Depth** - Layered translucent cards with refined shadows and blur effects
- 🎭 **Smooth Animations** - Fluid transitions and micro-interactions throughout
- 💎 **Luxury Aesthetic** - Professional, trustworthy, and visually striking

## 🌟 Features

### 📄 Intelligent Document Processing
- **Universal Document Parser Agent** - Automatically extracts financial data from:
  - Bank statements (PDF, DOCX)
  - Pay stubs
  - Credit card statements
  - Loan documents
  - Investment statements
  - Budget spreadsheets (CSV, XLSX)
  - Plain text financial summaries

### 🤖 Specialized AI Agents

1. **💳 Debt Analyzer Agent**
   - Creates optimized debt payoff strategies
   - Avalanche method (highest interest first)
   - Snowball method (smallest balance first)
   - Calculates total interest savings
   - Provides month-by-month payment allocation
   - Identifies consolidation opportunities

2. **💰 Savings Strategist Agent**
   - Designs personalized savings plans
   - Emergency fund recommendations (3-6 months)
   - Goal-based savings strategies
   - High-yield account recommendations
   - Automated savings schedules
   - Milestone tracking system

3. **📊 Budget Optimizer Agent**
   - Analyzes spending patterns
   - Applies 50/30/20 budgeting rule
   - Identifies cost-cutting opportunities
   - Subscription audit recommendations
   - Bill negotiation strategies
   - Category-specific budget targets

4. **📈 Investment Advisor Agent**
   - Asset allocation recommendations
   - Tax-advantaged account prioritization (401k, IRA, HSA)
   - Index fund vs active management guidance
   - Dollar-cost averaging strategies
   - Rebalancing schedules
   - Retirement milestone planning

5. **🏛️ Tax Planner Agent**
   - Tax optimization strategies
   - Tax-loss harvesting opportunities
   - Deduction maximization
   - Retirement contribution planning
   - Year-end tax planning checklist

6. **🚨 Emergency Fund Builder Agent**
   - Target fund size calculations
   - Timeline projections
   - Monthly savings requirements
   - Best account recommendations
   - Milestone celebration strategy

### 📊 Comprehensive Analysis
- **Financial Health Score** - 100-point scale assessment
- **Real-time Metrics** - Cash flow, savings rate, debt-to-income ratio
- **Interactive Dashboard** - Visual summary of financial status
- **Multi-agent Orchestration** - Coordinated analysis across all domains

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Anthropic API key

### Installation

1. **Clone or download the project files**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set your Anthropic API key**
```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY='your-api-key-here'

# Option 2: Set in code (not recommended for production)
# Edit financial_advisor_app.py and web_app.py
```

4. **Run the application**

**Option A: Web Interface (Recommended)**
```bash
python web_app.py
```
Then open your browser to: `http://localhost:5000`

**Option B: Command Line**
```bash
python financial_advisor_app.py
```

## 📖 Usage Guide

### Web Interface

1. **Upload Documents**
   - Drag and drop financial documents (PDF, DOCX, TXT, CSV, XLSX)
   - Or click to browse and select files
   - Maximum file size: 16MB

2. **Manual Data Entry**
   - Click "Enter Financial Data Manually"
   - Input income, expenses, debts, and goals
   - Add multiple expense categories and debt accounts

3. **View Financial Summary**
   - Automatic calculation of key metrics
   - Financial health score
   - Visual dashboard with 8 key indicators

4. **Agent Analysis**
   - Click any agent tab to get specialized advice
   - "Complete Plan" runs all agents simultaneously
   - Individual agents for targeted analysis

### Command Line

The command line version demonstrates the system with sample data:

```bash
python financial_advisor_app.py
```

Output includes:
- Extracted financial data
- Financial health summary
- Individual agent analyses
- Comprehensive financial plan

## 🏗️ Architecture

### Core Components

```
financial_advisor_app.py    # Multi-agent system engine
├── AgentType (Enum)        # Agent type definitions
├── FinancialData          # Data structure
├── FinancialAdvisorAgent  # Base agent class
└── FinancialAdvisorOrchestrator  # Multi-agent coordinator

web_app.py                 # Flask web application
├── /api/upload           # Document upload endpoint
├── /api/analyze/<type>   # Agent analysis endpoints
├── /api/summary          # Financial summary
└── /api/manual-input     # Manual data entry

templates/
└── index.html            # Web UI

static/
├── css/styles.css        # Modern, responsive styling
└── js/app.js            # Frontend logic
```

### Agent System Architecture

```
User Document → Document Parser Agent → Structured Data
                                            ↓
                              FinancialAdvisorOrchestrator
                                            ↓
                    ┌──────────────────────┴──────────────────────┐
                    ↓                                              ↓
          Individual Agents                          Comprehensive Analysis
         ├── Debt Analyzer                                All Agents
         ├── Savings Strategist                          Coordinated
         ├── Budget Optimizer                            Results
         ├── Investment Advisor
         ├── Tax Planner
         └── Emergency Fund Builder
```

## 🔧 Customization

### Adding New Agents

1. Add agent type to `AgentType` enum:
```python
class AgentType(Enum):
    YOUR_NEW_AGENT = "your_new_agent"
```

2. Add system prompt in `_load_system_prompts()`:
```python
AgentType.YOUR_NEW_AGENT: """Your specialized prompt..."""
```

3. Add analysis method in `FinancialAdvisorOrchestrator`:
```python
def your_agent_analysis(self) -> Dict[str, Any]:
    # Implementation
    pass
```

### Modifying Financial Data Structure

Edit the `FinancialData` dataclass in `financial_advisor_app.py`:

```python
@dataclass
class FinancialData:
    # Add new fields
    your_new_field: Optional[float] = None
```

### Customizing UI

- **Colors/Theme**: Edit `static/css/styles.css`
- **Layout**: Modify `templates/index.html`
- **Behavior**: Update `static/js/app.js`

## 📊 Sample Output

### Financial Health Summary
```
Monthly Income: $6,600.00
Monthly Expenses: $3,915.00
Net Cash Flow: $1,845.00
Total Debt: $51,700.00
Current Savings: $3,700.00
Savings Rate: 27.95%
Debt-to-Income Ratio: 65.28%
Financial Health Score: Good (72/100)
```

### Debt Analysis Example
- Total debt: $51,700
- Weighted avg interest: 12.8%
- Avalanche method: Debt-free in 28 months, save $3,200 in interest
- Snowball method: Debt-free in 30 months, save $2,800 in interest
- Recommended extra payment: $500/month

## 🔒 Security & Privacy

- **No Data Storage**: Financial data is processed in-memory only
- **Session-Based**: Each user session is isolated
- **API Key Security**: Never commit API keys to version control
- **HTTPS Recommended**: Use HTTPS in production
- **File Cleanup**: Uploaded files are deleted after processing

## 🛠️ Troubleshooting

### Common Issues

**"No module named 'anthropic'"**
```bash
pip install -r requirements.txt
```

**"API key not found"**
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

**"Port 5000 already in use"**
```bash
# Change port in web_app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Document parsing errors**
- Ensure file format is supported
- Check file isn't corrupted
- Verify file size < 16MB

## 🚀 Production Deployment

### Recommendations

1. **Environment Variables**
   - Use environment variables for API keys
   - Never hardcode credentials

2. **Database Integration**
   - Add PostgreSQL/MongoDB for data persistence
   - Implement user authentication

3. **Scaling**
   - Use Redis for session management
   - Deploy with Gunicorn + Nginx
   - Consider containerization (Docker)

4. **Security**
   - Enable HTTPS
   - Add rate limiting
   - Implement CSRF protection
   - Add input validation

5. **Monitoring**
   - Add logging (Python logging module)
   - Error tracking (Sentry)
   - Performance monitoring

### Example Production Setup

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

## 📝 API Reference

### POST /api/upload
Upload and parse financial document
- **Body**: multipart/form-data with 'file'
- **Returns**: Structured financial data

### POST /api/analyze/\<agent_type\>
Run specific agent analysis
- **agent_type**: debt, savings, budget, investment, tax, emergency, comprehensive
- **Returns**: Agent-specific recommendations

### GET /api/summary
Get financial health summary
- **Returns**: Key metrics and health score

### POST /api/manual-input
Submit manual financial data
- **Body**: JSON with financial information
- **Returns**: Success confirmation

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional agent types (insurance, estate planning, etc.)
- Enhanced document parsing (OCR, table extraction)
- Data visualization charts
- Export to PDF/Excel
- Multi-currency support
- Historical tracking

## 📄 License

This project is provided as-is for educational and personal use.

## 🙏 Acknowledgments

- Built with Claude 4.5 Sonnet by Anthropic
- Flask web framework
- Modern CSS with gradient designs

## 📧 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the Usage Guide
3. Verify API key is set correctly

---

**Built with ❤️ and Claude AI** | Multi-Agent Intelligence for Better Financial Decisions
