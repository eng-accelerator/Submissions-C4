# 🔧 Troubleshooting Guide

## Common Error: "Unexpected token '<'"

This error means the JavaScript is receiving HTML instead of JSON from the server.

### **Root Causes & Solutions:**

#### 1. **API Key Not Set** ⚠️
**Symptom:** Server crashes when trying to call Claude API

**Solution:**
```bash
# Set your API key before running the app
export ANTHROPIC_API_KEY='your-api-key-here'

# Then run
python web_app.py
```

**To verify it's set:**
```bash
echo $ANTHROPIC_API_KEY
```

#### 2. **No Financial Data Loaded** 📄
**Symptom:** Error when clicking agent tabs

**Solution:**
1. Upload a financial document first, OR
2. Click "Enter Financial Data Manually" and fill in the form
3. Wait for "Document processed successfully" message
4. THEN click the agent tabs

#### 3. **Missing Python Libraries** 📦
**Symptom:** Import errors in server logs

**Solution:**
```bash
pip install -r requirements.txt --break-system-packages
```

Or install individually:
```bash
pip install anthropic flask PyPDF2 python-docx pandas openpyxl
```

#### 4. **Server Error (500)** 🔴
**Symptom:** Agent analysis fails

**Solution:**
1. Check the terminal where you ran `python web_app.py`
2. Look for error messages
3. Common issues:
   - API key invalid/expired → Get new key from https://console.anthropic.com/
   - Rate limit exceeded → Wait a few minutes
   - Network error → Check internet connection

---

## Step-by-Step Debugging

### **1. Check Server is Running**
```bash
python web_app.py
```

You should see:
```
🏦 Vérité Financial - Multi-Agent AI Advisor
Starting server...
Open your browser to: http://localhost:5000
```

### **2. Check API Key**
```bash
# Linux/Mac
echo $ANTHROPIC_API_KEY

# Windows CMD
echo %ANTHROPIC_API_KEY%

# Windows PowerShell
echo $env:ANTHROPIC_API_KEY
```

Should show your key (starts with `sk-ant-...`)

### **3. Test with Manual Input**
1. Open http://localhost:5000
2. Click "Enter Financial Data Manually"
3. Fill in simple data:
   - Monthly Income: 5000
   - Savings: 1000
   - Add one expense: Rent, 1500
   - Add one debt: Credit Card, 2000, 18%, 50
4. Click "Save & Analyze"
5. Try "Complete Plan" tab

### **4. Check Browser Console**
1. Press F12 in your browser
2. Go to "Console" tab
3. Look for red error messages
4. Share these if asking for help

### **5. Check Server Logs**
Look at the terminal running `python web_app.py`
- Red text = errors
- Look for stack traces
- Look for "Error:" messages

---

## Specific Error Messages

### "No financial data available"
**Fix:** Upload a document or enter data manually first

### "Failed to extract text from document"
**Fix:** 
- Make sure file is not corrupted
- Try a .txt file with financial info as plain text
- Check file size is under 16MB

### "ANTHROPIC_API_KEY not found"
**Fix:**
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

### "Module not found: anthropic"
**Fix:**
```bash
pip install anthropic
```

### "Connection refused" or "Cannot connect"
**Fix:**
- Server not running → Run `python web_app.py`
- Wrong URL → Use `http://localhost:5000` not `https://`

---

## Testing Without Claude API

To test the interface without needing an API key:

1. Comment out the API calls in `financial_advisor_app.py`:
```python
def analyze(self, data: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    # TEMPORARY: Return mock data for testing
    return {
        "response": "This is test data. Set your API key to get real analysis."
    }
    
    # Comment out the real API call:
    # response = self.client.messages.create(...)
```

2. This lets you test the UI without API costs

---

## Still Having Issues?

### Check:
1. ✅ Python 3.8+ installed: `python --version`
2. ✅ All packages installed: `pip list | grep anthropic`
3. ✅ API key set: `echo $ANTHROPIC_API_KEY`
4. ✅ Server running: Terminal shows "Running on http://0.0.0.0:5000"
5. ✅ Browser console clear: F12 → Console tab
6. ✅ Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Get Help:
1. Copy the error message from browser console (F12)
2. Copy the error from server terminal
3. Note what you were doing when error occurred
4. Check if API key is valid at https://console.anthropic.com/

---

## Quick Test Script

Save this as `test_api.py` to verify your API key works:

```python
import anthropic
import os

api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    print("❌ ANTHROPIC_API_KEY not set!")
    exit(1)

print(f"✅ API key found: {api_key[:15]}...")

try:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("✅ API key works!")
    print(f"Response: {response.content[0].text}")
except Exception as e:
    print(f"❌ API error: {e}")
```

Run with: `python test_api.py`

---

**Most Common Fix:** Set your API key and make sure you upload/enter data before clicking agent tabs! 🎯
