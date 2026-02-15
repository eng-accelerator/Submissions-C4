# Quick Start Guide

## Get Started in 5 Minutes

This guide will help you get the DevOps Incident Analysis Suite running quickly.

---

## Option 1: Local Setup (Fastest for Development)

### Step 1: Install Dependencies

```bash
# Clone the repository
cd devops-incident-suite

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get API Keys

1. **OpenRouter API Key** (Required)
   - Sign up at: https://openrouter.ai/
   - Get your API key from dashboard
   - Free tier available!

2. **Slack Webhook** (Optional)
   - Create webhook at: https://api.slack.com/messaging/webhooks
   - Copy webhook URL

3. **JIRA API Token** (Optional)
   - Generate at: https://id.atlassian.com/manage-profile/security/api-tokens
   - Note your JIRA URL and email

### Step 3: Run the Application

```bash
python main.py
```

The app will open at: http://localhost:8501

### Step 4: Configure in UI

1. Open http://localhost:8501
2. In sidebar, enter your OpenRouter API Key
3. (Optional) Enter Slack and JIRA credentials
4. Click "Load Sample Log" to test
5. Click "Analyze Incident"

**That's it!** 🎉

---

## Option 2: Docker (Fastest for Production)

### Step 1: Install Docker

Download from: https://www.docker.com/get-started

### Step 2: Build and Run

```bash
# Build the image
docker build -t devops-incident-suite .

# Run the container
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=your_key_here \
  devops-incident-suite
```

Open: http://localhost:8501

### With All Configurations

```bash
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -e SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... \
  -e JIRA_URL=https://your-domain.atlassian.net \
  -e JIRA_USERNAME=your-email@example.com \
  -e JIRA_API_TOKEN=your_token \
  devops-incident-suite
```

---

## Option 3: Docker Compose (Easiest)

### Step 1: Create .env File

```bash
cp .env.example .env
# Edit .env with your credentials
```

### Step 2: Start Services

```bash
docker-compose up -d
```

Open: http://localhost:8501

### Step 3: View Logs

```bash
docker-compose logs -f
```

### Step 4: Stop Services

```bash
docker-compose down
```

---

## Testing the System

### Sample Log to Analyze

```
2024-02-14 10:23:45 CRITICAL [payment-service] Database connection timeout after 30s
Connection pool exhausted: max_connections=100, active=100, idle=0
Error code: DB_CONN_TIMEOUT_001
Failed to process payment transaction for order #12345
Stack trace: at com.payment.db.ConnectionPool.getConnection(ConnectionPool.java:145)
```

### Expected Output

1. **Classified Incident**
   - Type: DatabaseConnectionTimeout
   - Severity: CRITICAL
   - Service: payment-service

2. **Remediation Plan**
   - Root cause: Connection pool exhaustion
   - Fixes: Increase pool size, add leak detection, etc.

3. **Cookbook**
   - Step-by-step runbook
   - Validation steps
   - Rollback plan

4. **JIRA Ticket** (if configured)
   - Auto-created ticket with link

5. **Slack Notification** (if configured)
   - Message sent with summary

---

## Common Issues

### Issue: "OpenRouter API Error"

**Solution**: Check your API key is valid
```bash
# Test your key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

### Issue: "Port 8501 already in use"

**Solution**: Change the port
```bash
# Local
streamlit run ui/streamlit_app.py --server.port=8502

# Docker
docker run -p 8502:8501 ...
```

### Issue: "ModuleNotFoundError"

**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: "JIRA ticket creation failed"

**Solution**: Verify credentials
- Check JIRA URL format: `https://your-domain.atlassian.net`
- Verify API token is valid
- Ensure user has permission to create tickets

---

## Next Steps

### 1. Customize Knowledge Base

Edit `agents/remediation.py`:
```python
INCIDENT_PATTERNS = {
    "YourCustomPattern": {
        "common_causes": ["cause1", "cause2"],
        "typical_fixes": ["fix1", "fix2"]
    }
}
```

### 2. Try Different Models

In UI sidebar, select:
- `openai/gpt-4o` (recommended, balanced)
- `openai/gpt-4-turbo` (faster)
- `anthropic/claude-3.5-sonnet` (excellent reasoning)
- `google/gemini-pro` (cost-effective)

### 3. Integrate with Your Systems

**Slack**: Set up webhook in your workspace

**JIRA**: Create dedicated project for incidents

**Logs**: Connect to your log aggregation system

### 4. Automate Log Ingestion

Create a cron job or webhook to automatically send logs:

```python
import requests

logs = get_logs_from_system()

response = requests.post(
    "http://localhost:8501/analyze",  # Need to implement API endpoint
    json={"log": logs}
)
```

---

## Production Deployment

### Recommended Setup

```
Load Balancer (NGINX/HAProxy)
  ↓
Multiple Docker Containers
  ↓
Shared Redis (for state)
  ↓
PostgreSQL (for persistence)
```

### Environment Variables

Always use environment variables for secrets:

```bash
# .env file
OPENROUTER_API_KEY=sk-or-v1-xxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxx
JIRA_URL=https://company.atlassian.net
JIRA_USERNAME=bot@company.com
JIRA_API_TOKEN=xxx
```

### Monitoring

Set up alerts for:
- Container health
- API failures
- High error rates
- LLM token usage

---

## Getting Help

1. **Documentation**: Read `README.md` and `ARCHITECTURE.md`
2. **Examples**: Check sample logs in UI
3. **Issues**: Open GitHub issue with logs
4. **Community**: Join discussions

---

## Success Criteria

You're successfully running when you see:

✅ Streamlit UI loads at http://localhost:8501  
✅ Sample log analysis completes without errors  
✅ All 5 result sections display  
✅ (Optional) Slack notification appears in channel  
✅ (Optional) JIRA ticket is created  

---

**Estimated Setup Time**: 5-10 minutes  
**Skill Level Required**: Intermediate  
**Cost**: Free tier available for all services

Happy analyzing! 🚀
