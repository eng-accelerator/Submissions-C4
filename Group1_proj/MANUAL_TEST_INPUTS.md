# 🧪 Manual Test Inputs Guide - All Features

## Overview

This guide provides real test inputs that you can use to manually test all 5 features through the original web UI. Each feature has multiple test cases with different input scenarios.

---

## 📋 Feature 1: Threat Detection & Analysis

### Test Case 1: Valid Alert (PASS)
**Input:**
```
Alert: "SQL Injection attempt detected on web server port 443"
```
**Expected Output:**
- Status: COMPLETE
- Threat Level: HIGH or CRITICAL
- Enrichment: Threat details with MITRE ATT&CK mapping

**What to Do:**
1. Go to Threat Detection section in UI
2. Paste the alert text
3. Click "Analyze"
4. Verify threat is detected and enriched

---

### Test Case 2: Critical Threat (PASS)
**Input:**
```
Alert: "Ransomware detected: WannaCry variant spreading across network segment 10.0.0.0/24"
```
**Expected Output:**
- Status: COMPLETE
- Threat Level: CRITICAL
- Recommendation: Immediate isolation required

**What to Do:**
1. Go to Threat Detection section
2. Paste the ransomware alert
3. Click "Analyze"
4. Verify CRITICAL level is assigned

---

### Test Case 3: Empty Alert (FAIL - Expected)
**Input:**
```
Alert: ""
```
**Expected Output:**
- Error: "Alert cannot be empty"
- Status: REJECTED
- No enrichment performed

**What to Do:**
1. Go to Threat Detection section
2. Leave alert field empty
3. Click "Analyze"
4. Should show error message

---

### Test Case 4: Invalid Format (FAIL - Expected)
**Input:**
```
Alert: null or None
```
**Expected Output:**
- Error: "Invalid alert format"
- Status: REJECTED
- Graceful error handling

**What to Do:**
1. Go to Threat Detection section
2. Try submitting with no/null value
3. Should handle gracefully

---

## 🔍 Feature 2: Vulnerability Analysis

### Test Case 1: Valid Host Scan (PASS)
**Input:**
```
Host IP: 192.168.1.100
Scan Type: Full
```
**Expected Output:**
- Scanning Status: COMPLETE
- Vulnerabilities Found: 3-5
- Critical Count: 1-2
- Severity Breakdown: Critical, High, Medium

**What to Do:**
1. Go to Vulnerability Analysis section
2. Enter host IP: 192.168.1.100
3. Click "Scan"
4. Wait for scan to complete
5. Verify vulnerabilities are listed

---

### Test Case 2: Vulnerable Host Analysis (PASS)
**Input:**
```
Host IP: 10.0.0.5
Include Historical: true
```
**Expected Output:**
- Multiple Vulnerabilities: YES
- Known Exploits: 2-3
- Patch Availability: Most have patches
- Risk Score: 8.5+

**What to Do:**
1. Go to Vulnerability Analysis
2. Enter: 10.0.0.5
3. Enable "Include Historical"
4. Click "Analyze"
5. Review vulnerability details

---

### Test Case 3: Invalid Host Format (FAIL - Expected)
**Input:**
```
Host IP: "not_a_valid_ip"
or
Host IP: "256.256.256.256"
```
**Expected Output:**
- Error: "Invalid IP address format"
- Status: REJECTED

**What to Do:**
1. Go to Vulnerability Analysis
2. Enter invalid IP: "not_a_valid_ip"
3. Click "Scan"
4. Should show format error

---

### Test Case 4: Unreachable Host (FAIL - Expected)
**Input:**
```
Host IP: 192.168.1.999
Timeout: 5 seconds
```
**Expected Output:**
- Error: "Host unreachable"
- Status: TIMEOUT
- Graceful timeout handling

**What to Do:**
1. Go to Vulnerability Analysis
2. Enter unreachable IP: 192.168.1.999
3. Click "Scan"
4. Should timeout gracefully

---

## 🚨 Feature 3: Incident Response

### Test Case 1: Critical Incident (PASS)
**Input:**
```
Threat: "Ransomware spreading in production"
Severity: CRITICAL
Affected Systems: 50
Business Impact: High - Revenue loss
```
**Expected Output:**
- Playbook Generated: YES
- Containment Steps: 5-7 steps
- Communication Template: Included
- Escalation Level: C-Suite

**What to Do:**
1. Go to Incident Response section
2. Enter threat description
3. Set severity to CRITICAL
4. Click "Generate Playbook"
5. Review generated playbook

---

### Test Case 2: Medium Incident (PASS)
**Input:**
```
Threat: "Unauthorized access attempt detected"
Severity: MEDIUM
Affected Systems: 2
Business Impact: Low - No data loss
```
**Expected Output:**
- Playbook Generated: YES
- Investigation Steps: 3-4 steps
- Communication Template: For IT team
- Escalation Level: IT Manager

**What to Do:**
1. Go to Incident Response
2. Enter medium severity threat
3. Click "Generate Playbook"
4. Review response steps

---

### Test Case 3: Invalid Severity (FAIL - Expected)
**Input:**
```
Threat: "Test threat"
Severity: "INVALID_LEVEL"
```
**Expected Output:**
- Error: "Invalid severity level"
- Allowed: CRITICAL, HIGH, MEDIUM, LOW
- Status: REJECTED

**What to Do:**
1. Go to Incident Response
2. Enter invalid severity level
3. Should show error

---

### Test Case 4: Empty Description (FAIL - Expected)
**Input:**
```
Threat: ""
Severity: HIGH
```
**Expected Output:**
- Error: "Threat description required"
- Status: REJECTED

**What to Do:**
1. Go to Incident Response
2. Leave threat description empty
3. Set any severity
4. Click "Generate Playbook"
5. Should show error

---

## ✅ Feature 4: Compliance Evaluation

### Test Case 1: Host Compliance Check (PASS)
**Input:**
```
Host IP: 192.168.1.50
Compliance Framework: PCI-DSS
```
**Expected Output:**
- Compliance Status: EVALUATED
- PCI-DSS Score: 75-85%
- Failing Controls: 2-3
- Recommendations: Provided

**What to Do:**
1. Go to Compliance Evaluation
2. Enter host IP: 192.168.1.50
3. Select framework: PCI-DSS
4. Click "Evaluate"
5. Review compliance score

---

### Test Case 2: Enterprise Compliance (PASS)
**Input:**
```
Scope: All Systems
Framework: ISO 27001
Report Type: Executive Summary
```
**Expected Output:**
- Overall Compliance: 60-75%
- Compliant Systems: 30/50
- Non-Compliant: 20/50
- Executive Summary: Generated

**What to Do:**
1. Go to Compliance Evaluation
2. Select "All Systems"
3. Choose ISO 27001
4. Click "Generate Report"
5. Review enterprise compliance

---

### Test Case 3: Non-Existent Host (FAIL - Expected)
**Input:**
```
Host IP: 255.255.255.255
```
**Expected Output:**
- Error: "Host not found in inventory"
- Status: NOT_FOUND

**What to Do:**
1. Go to Compliance Evaluation
2. Enter non-existent host
3. Click "Evaluate"
4. Should show not found error

---

### Test Case 4: Invalid Query Format (FAIL - Expected)
**Input:**
```
Host IP: "invalid_format"
Framework: "UNKNOWN_FRAMEWORK"
```
**Expected Output:**
- Error: "Invalid input format"
- Status: REJECTED

**What to Do:**
1. Go to Compliance Evaluation
2. Use invalid inputs
3. Should show validation error

---

## 📝 Feature 5: Full Auditability

### Test Case 1: Audit Trail Logging (PASS)
**Input:**
```
Action: "threat_detected"
User: "security_admin"
Timestamp: Auto-generated
```
**Expected Output:**
- Log Entry Created: YES
- Timestamp: Recorded
- User Identity: Captured
- Action Details: Stored

**What to Do:**
1. Go to Audit Trail
2. Perform any action (threat detection, scan, etc.)
3. Click "View Audit Log"
4. Verify entry is logged with timestamp

---

### Test Case 2: Report Export (PASS)
**Input:**
```
Report Type: Audit Trail
Format: JSON/CSV
Time Range: Last 24 hours
```
**Expected Output:**
- Report Generated: YES
- File Format: Valid JSON/CSV
- Entries: All logged actions
- Downloadable: YES

**What to Do:**
1. Go to Audit Trail
2. Click "Export Report"
3. Select format (JSON/CSV)
4. Click "Download"
5. Verify file is valid

---

### Test Case 3: Empty Audit Trail (FAIL - Expected)
**Input:**
```
Report Type: Audit Trail
Time Range: Year 2000 (no records)
```
**Expected Output:**
- Error: "No audit entries found"
- Status: EMPTY
- Message: "No data for specified range"

**What to Do:**
1. Go to Audit Trail
2. Try to export very old date range
3. Should show empty error

---

### Test Case 4: Export Permission Error (FAIL - Expected)
**Input:**
```
User Role: "Read-Only"
Action: "Export Audit Trail"
```
**Expected Output:**
- Error: "Permission denied"
- Status: UNAUTHORIZED
- Message: "Insufficient permissions"

**What to Do:**
1. Login as read-only user (if available)
2. Try to export audit trail
3. Should show permission error

---

## 📊 Test Data Summary Table

| Feature | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| **Threat Detection** | Valid Alert | "SQL Injection attempt..." | Threat detected & enriched |
| | Critical Threat | "Ransomware detected..." | CRITICAL level assigned |
| | Empty Alert | "" | Error message |
| | Invalid Format | null/None | Format error |
| **Vulnerability** | Valid Host | 192.168.1.100 | Vulnerabilities found |
| | Vulnerable Host | 10.0.0.5 | Multiple vulns with exploits |
| | Invalid IP | "invalid_ip" | Format error |
| | Unreachable | 192.168.1.999 | Timeout error |
| **Incident Response** | Critical | Ransomware + CRITICAL | Playbook generated |
| | Medium | Unauthorized access + MEDIUM | Response playbook |
| | Invalid Severity | "INVALID_LEVEL" | Severity error |
| | Empty Description | "" | Description required error |
| **Compliance** | Host Check | 192.168.1.50 + PCI-DSS | Compliance score |
| | Enterprise | All Systems + ISO 27001 | Enterprise report |
| | Non-existent | 255.255.255.255 | Host not found |
| | Invalid Query | "invalid" + "UNKNOWN" | Format error |
| **Auditability** | Trail Logging | Any action | Entry logged |
| | Export | JSON/CSV format | Report downloaded |
| | Empty Trail | Old date range | No entries error |
| | Permission Error | Read-only user | Access denied |

---

## 🎯 Quick Test Checklist

### For Threat Detection:
- [ ] Paste simple threat alert
- [ ] Paste critical ransomware alert
- [ ] Try empty alert (should fail)
- [ ] Try null value (should fail)

### For Vulnerability Analysis:
- [ ] Scan 192.168.1.100
- [ ] Scan 10.0.0.5 with historical
- [ ] Try invalid IP format
- [ ] Try unreachable IP

### For Incident Response:
- [ ] Generate CRITICAL playbook
- [ ] Generate MEDIUM playbook
- [ ] Try invalid severity level
- [ ] Try empty threat description

### For Compliance:
- [ ] Evaluate 192.168.1.50 PCI-DSS
- [ ] Generate enterprise ISO 27001 report
- [ ] Try non-existent host
- [ ] Try invalid framework

### For Auditability:
- [ ] Perform action and check audit log
- [ ] Export audit trail
- [ ] Try export with old date range
- [ ] Check for permission restrictions

---

## 💡 Tips for Testing

1. **Pass Cases (Should Succeed):**
   - Use provided valid inputs
   - Verify results are meaningful
   - Check for proper enrichment/analysis

2. **Fail Cases (Should Show Error):**
   - Use provided invalid inputs
   - Verify error messages are clear
   - Confirm graceful error handling

3. **Performance:**
   - Note time taken for each operation
   - Full Scan: ~2-3 minutes
   - Single Action: <30 seconds

4. **Data Validation:**
   - Check timestamps are accurate
   - Verify user info is captured
   - Confirm all fields are populated

---

## 📚 Reference Documentation

For detailed specifications, see:
- [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md) - Full test case details
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [README_TEST_SUITE.md](README_TEST_SUITE.md) - Test suite overview

---

**Ready to test? Use these inputs on the original web UI!** ✅
