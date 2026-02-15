# 🔍 Debugging: Financial Health Dashboard Not Updating

If the Financial Health Dashboard doesn't update after uploading a bank statement, follow these steps:

## Step 1: Check Browser Console

1. Open browser (with the app running)
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Upload a document or enter manual data
5. Look for these messages:

**Expected output:**
```
Loading financial summary...
Summary response status: 200
Summary result: {success: true, data: {...}}
Displaying summary with data: {...}
Summary section displayed
```

**If you see errors, note them!**

## Step 2: Check Network Tab

1. In Developer Tools, go to **Network** tab
2. Upload a document
3. Look for these requests:
   - `POST /api/upload` - Should return 200
   - `GET /api/summary` - Should return 200

**Click on each request to see:**
- Status code (should be 200)
- Response (should have success: true)

## Step 3: Check Server Logs

Look at the terminal running `python web_app.py`:

**Should see:**
```
🔍 Document Parser Agent: Analyzing your financial documents...
✅ Financial data extracted successfully!
```

**If you see errors:**
- Check API key is set
- Check document format is valid

## Common Issues & Fixes

### Issue 1: Summary Section Hidden

**Symptom:** Console shows "Summary section displayed" but nothing visible

**Fix:**
Check if `summarySection` element exists:
```javascript
// In browser console, type:
document.getElementById('summarySection')
```

Should return the HTML element, not `null`.

### Issue 2: API Returns 400 Error

**Symptom:** Console shows "Summary response status: 400"

**Cause:** No session or no data loaded

**Fix:**
1. Make sure document upload succeeded first
2. Check for "Document processed successfully" message
3. Try manual data entry instead

### Issue 3: Data is Null/Undefined

**Symptom:** Console shows "Summary response missing data"

**Cause:** Backend calculation failed

**Fix:**
Check server logs for Python errors. Common causes:
- Division by zero (income = 0)
- Missing data fields
- Type errors

### Issue 4: Session Lost

**Symptom:** Works once, then fails on second upload

**Cause:** Session cookies cleared

**Fix:**
- Check browser isn't in incognito mode
- Check cookies are enabled
- Try refreshing the page

## Manual Test

Test the API directly in browser console:

```javascript
// After uploading/entering data, run:
fetch('/api/summary')
  .then(r => r.json())
  .then(data => console.log('Summary:', data))
  .catch(e => console.error('Error:', e));
```

Should output:
```javascript
Summary: {
  success: true,
  data: {
    monthly_income: 5000,
    monthly_expenses: 3000,
    // ... more fields
  }
}
```

## Step-by-Step Manual Fix

If automatic loading still doesn't work:

### Option A: Force Refresh
```javascript
// In browser console after uploading:
loadSummary();
```

### Option B: Manual Display
```javascript
// In browser console:
fetch('/api/summary')
  .then(r => r.json())
  .then(result => {
    if (result.success) {
      displaySummary(result.data);
      document.getElementById('summarySection').style.display = 'block';
    }
  });
```

## Verify Upload Success

After uploading a document, check:

```javascript
// In browser console:
fetch('/api/summary')
  .then(r => r.json())
  .then(d => console.log('Income:', d.data.monthly_income));
```

Should show your income amount, not 0.

## Hard Refresh

Sometimes the old JavaScript is cached:

**Windows/Linux:** `Ctrl + Shift + R` or `Ctrl + F5`
**Mac:** `Cmd + Shift + R`

## Check HTML Structure

Make sure these elements exist:

```javascript
// In browser console:
console.log('Summary Section:', document.getElementById('summarySection'));
console.log('Summary Grid:', document.getElementById('summaryGrid'));
console.log('Agents Section:', document.getElementById('agentsSection'));
```

All should return HTML elements, not `null`.

## Test with Manual Entry

Instead of uploading a document:

1. Click "Enter Financial Data Manually"
2. Fill in simple data:
   - Income: 5000
   - Savings: 1000
   - One expense: Rent, 1500
3. Click "Save & Analyze"
4. Watch browser console for logs

## Still Not Working?

### Check this checklist:

- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Check browser console for errors
- [ ] Check Network tab shows 200 responses
- [ ] Check server terminal shows no errors
- [ ] API key is set correctly
- [ ] Session cookies enabled
- [ ] Not in incognito/private mode
- [ ] JavaScript console has no errors
- [ ] `/api/summary` returns data manually

### Get the exact error:

1. Open browser console
2. Clear the console
3. Upload document
4. Copy ALL the console output
5. Copy the Network tab responses

This will help identify the exact issue!

## Quick Fix: Add Debug Button

Add this to your page to manually trigger summary load:

1. Open browser console
2. Paste and run:
```javascript
const btn = document.createElement('button');
btn.textContent = '🔄 Reload Dashboard';
btn.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;padding:10px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;';
btn.onclick = () => loadSummary();
document.body.appendChild(btn);
```

Now you have a reload button in the top-right corner!

---

**Most likely cause:** Browser cache. Try hard refresh first! 🔄
