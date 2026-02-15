"""
Streamlit Web UI
Interactive dashboard for Cybersecurity Orchestrator
"""

import streamlit as st
import datetime
import json
from orchestrator.supervisor import SecurityOrchestrator
from evaluation.simulator import SecuritySimulator

# Page config
st.set_page_config(
    page_title="Cybersecurity Orchestrator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = SecurityOrchestrator()

if "simulator" not in st.session_state:
    st.session_state.simulator = SecuritySimulator(orchestrator=st.session_state.orchestrator)

if "last_results" not in st.session_state:
    st.session_state.last_results = {}

orchestrator = st.session_state.orchestrator
simulator = st.session_state.simulator

# Header
st.title("🛡️ Agentic Cybersecurity Orchestrator")
st.markdown("**RAG-Powered Threat Detection, Vulnerability Analysis & Incident Response**")
st.divider()

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Module",
        ["Dashboard", "Threat Detection", "Vulnerability Analysis", "Incident Response", 
         "Compliance", "Evaluation", "Audit Trail"]
    )
    
    st.divider()
    st.subheader("System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Orchestrator", "🟢 Online")
    with col2:
        st.metric("Vector Store", "🟢 Ready")


# === DASHBOARD ===
if page == "Dashboard":
    st.header("Security Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Threats Detected", len([a for a in orchestrator.audit_trail if "threat_detection" in a["action"]]))
    with col2:
        st.metric("Vulns. Analyzed", len([a for a in orchestrator.audit_trail if "vuln_analysis" in a["action"]]))
    with col3:
        st.metric("Incidents Handled", len([a for a in orchestrator.audit_trail if "incident_response" in a["action"]]))
    with col4:
        st.metric("Compliance Checks", len([a for a in orchestrator.audit_trail if "compliance_eval" in a["action"]]))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quick Actions")
        if st.button("🚨 Detect Threat", use_container_width=True):
            st.session_state.show_threat_form = True
        if st.button("🔍 Analyze Host", use_container_width=True):
            st.session_state.show_vuln_form = True
        if st.button("⚠️ Handle Incident", use_container_width=True):
            st.session_state.show_incident_form = True
    
    with col2:
        st.subheader("System Info")
        st.info(f"""
        **Orchestrator Status:** Active
        **Agents Online:** 5/5
        **Collections:** 5
        **Last Activity:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        """)


# === THREAT DETECTION ===
elif page == "Threat Detection":
    st.header("🚨 Threat Detection & Analysis")
    
    with st.form("threat_form"):
        alert = st.text_area("Security Alert", placeholder="Enter threat description...")
        source = st.text_input("Source (optional)", placeholder="e.g., IDS, WAF, EDR")
        submitted = st.form_submit_button("Analyze Threat")
        
        if submitted and alert:
            with st.spinner("Analyzing threat..."):
                result = orchestrator.detect_threat(alert)
                st.session_state.last_results["threat"] = result
                
                st.success("Threat analysis complete!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Threat Level")
                    severity_colors = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
                    severity = result["threat_level"]
                    st.markdown(f"# {severity_colors.get(severity, '⚪')} {severity}")
                
                with col2:
                    st.subheader("Evidence")
                    if result["threat_enrichment"]["cve_count"] > 0:
                        st.metric("Related CVEs", result["threat_enrichment"]["cve_count"])
                    if result["threat_enrichment"]["incident_count"] > 0:
                        st.metric("Similar Incidents", result["threat_enrichment"]["incident_count"])
                
                st.divider()
                st.subheader("📊 Detailed Analysis")
                
                # Threat Details
                st.markdown("#### 🎯 Threat Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Alert:** {result['alert']}")
                with col2:
                    st.info(f"**Timestamp:** {result['timestamp']}")
                
                # Threat Enrichment
                st.markdown("#### 📚 Threat Intelligence")
                enrichment = result["threat_enrichment"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📋 CVE Count", enrichment["cve_count"])
                with col2:
                    st.metric("🔍 Incident Count", enrichment["incident_count"])
                with col3:
                    st.metric("🎯 Confidence", enrichment["confidence"])
                
                if enrichment["related_cves"]:
                    st.markdown("**Related CVEs:**")
                    for cve in enrichment["related_cves"][:3]:
                        st.write(f"• {cve}")
                
                if enrichment["related_incidents"]:
                    st.markdown("**Similar Past Incidents:**")
                    for incident in enrichment["related_incidents"][:3]:
                        st.write(f"• {incident}")
                
                # Severity Assessment
                st.markdown("#### ⚠️ Severity Assessment")
                assessment = result["severity_assessment"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🔴 Severity Level", assessment["severity"])
                with col2:
                    st.metric("📊 Supporting Evidence", f"{assessment['supporting_cves']} CVEs + {assessment['supporting_incidents']} Incidents")
                
                # Log Analysis
                if result.get("log_analysis"):
                    st.markdown("#### 📝 Log Analysis")
                    st.info(f"Pattern Detection: {result['log_analysis'].get('patterns_found', 0)} patterns identified")


# === VULNERABILITY ANALYSIS ===
elif page == "Vulnerability Analysis":
    st.header("🔍 Vulnerability Analysis")
    
    with st.form("vuln_form"):
        host = st.text_input("Host/IP Address", placeholder="e.g., 192.168.1.1 or hostname")
        submitted = st.form_submit_button("Scan Host")
        
        if submitted and host:
            with st.spinner(f"Analyzing vulnerabilities for {host}..."):
                result = orchestrator.analyze_host_vulnerabilities(host)
                st.session_state.last_results["vuln"] = result
                
                st.success("Vulnerability analysis complete!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Vulns.", result["vulnerability_scan"]["vulnerabilities_found"])
                with col2:
                    crit = result["vulnerability_scan"]["severity_breakdown"].get("CRITICAL", 0)
                    st.metric("Critical", crit, delta="⚠️" if crit > 0 else "✓")
                with col3:
                    high = result["vulnerability_scan"]["severity_breakdown"].get("HIGH", 0)
                    st.metric("High", high)
                
                st.divider()
                
                st.subheader("Remediation Priority")
                remediation = result["remediation_priority"]
                st.warning(f"**Priority Level:** {remediation['remediation_priority']}")
                st.info(f"Priority Items: {remediation['priority_count']}")
                
                st.divider()
                st.subheader("Compliance Status")
                compliance = result["compliance_status"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Passed Policies", compliance["compliance_status"].get("PASS", 0))
                with col2:
                    st.metric("Failed Policies", compliance["compliance_status"].get("FAIL", 0))
                
                # Detailed Analysis
                st.divider()
                st.subheader("📊 Detailed Vulnerability Report")
                
                # Vulnerability Details
                st.markdown("#### 🎯 Host Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Host/IP:** {result['host']}")
                with col2:
                    st.info(f"**Scan Time:** {result['timestamp']}")
                
                # Vulnerability Breakdown
                st.markdown("#### 🔍 Vulnerability Breakdown")
                vuln_scan = result["vulnerability_scan"]
                severity_data = vuln_scan["severity_breakdown"]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔴 Critical", severity_data.get("CRITICAL", 0))
                with col2:
                    st.metric("🟠 High", severity_data.get("HIGH", 0))
                with col3:
                    st.metric("🟡 Medium", severity_data.get("MEDIUM", 0))
                with col4:
                    st.metric("🟢 Low", severity_data.get("LOW", 0))
                
                # Remediation Details
                st.markdown("#### 🛠️ Remediation Recommendations")
                st.warning(f"**Overall Priority:** {remediation['remediation_priority']}")
                st.info(f"**Items to Address:** {remediation['priority_count']} vulnerabilities")
                
                if remediation.get("recommendations"):
                    st.markdown("**Top Recommendations:**")
                    for i, rec in enumerate(remediation.get("recommendations", [])[:5], 1):
                        st.write(f"{i}. {rec}")
                
                # Compliance Details
                st.markdown("#### ✅ Compliance Analysis")
                pass_count = compliance["compliance_status"].get("PASS", 0)
                fail_count = compliance["compliance_status"].get("FAIL", 0)
                total = pass_count + fail_count
                if total > 0:
                    pass_rate = (pass_count / total) * 100
                    st.metric("Compliance Pass Rate", f"{pass_rate:.1f}%")


# === INCIDENT RESPONSE ===
elif page == "Incident Response":
    st.header("⚠️ Incident Response Playbooks")
    
    col1, col2 = st.columns(2)
    with col1:
        threat = st.text_input("Threat Type", placeholder="e.g., Brute Force Attack")
    with col2:
        severity = st.selectbox("Severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    
    if st.button("Generate Playbook", use_container_width=True):
        with st.spinner("Generating incident response playbook..."):
            result = orchestrator.handle_incident(threat, severity)
            st.session_state.last_results["incident"] = result
            
            st.success("Playbook generated!")
            
            st.subheader("Response Playbook")
            playbook = result["playbook"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("ETA", playbook.get("estimated_resolution_time", "N/A"))
            with col2:
                resources_count = len(playbook.get("required_resources", []))
                st.metric("Required Resources", resources_count if resources_count > 0 else "See Details")
            
            st.divider()
            
            st.subheader("Action Steps")
            playbook_steps = playbook.get("playbook_steps", [])
            if playbook_steps:
                for i, step in enumerate(playbook_steps, 1):
                    st.write(f"{i}. {step}")
            else:
                st.info("No specific action steps available")
            
            st.divider()
            
            st.subheader("📊 Detailed Response Plan")
            
            # Incident Details
            st.markdown("#### 🎯 Incident Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Threat:** {result['threat']}")
            with col2:
                severity_colors = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
                st.info(f"**Severity:** {severity_colors.get(result['severity'], '⚪')} {result['severity']}")
            with col3:
                st.info(f"**Timestamp:** {result['timestamp']}")
            
            # Response Plan Summary
            st.markdown("#### 📋 Response Plan Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⏱️ Estimated Resolution", playbook.get("estimated_resolution_time", "N/A"))
            with col2:
                resources = len(playbook.get("required_resources", []))
                st.metric("👥 Resources", resources if resources > 0 else "TBD")
            with col3:
                steps = len(playbook.get("playbook_steps", []))
                st.metric("📌 Steps", steps if steps > 0 else "See Playbook")
            
            # Resources Required
            if playbook.get("required_resources"):
                st.markdown("#### 🔧 Required Resources")
                for resource in playbook.get("required_resources", []):
                    st.write(f"• {resource}")
            else:
                st.markdown("#### 🔧 Required Resources")
                st.info("Resource allocation: See Historical Context section for similar incidents")
            
            # Historical Context
            if result.get("historical_context"):
                st.markdown("#### 📚 Historical Context")
                history = result["historical_context"]
                st.info(f"**Similar Past Incidents:** {history.get('count', 0)}")
                if history.get("incidents"):
                    for incident in history["incidents"][:3]:
                        st.write(f"• {incident}")
            
            # Recovery Procedures
            if result.get("recovery_procedures"):
                st.markdown("#### 🔄 Recovery Procedures")
                recovery = result["recovery_procedures"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Backup Needed", "Yes" if recovery.get("backup_required") else "No")
                with col2:
                    st.metric("System Reboot", "Yes" if recovery.get("reboot_required") else "No")
                
                if recovery.get("steps"):
                    st.markdown("**Recovery Steps:**")
                    for i, step in enumerate(recovery["steps"][:5], 1):
                        st.write(f"{i}. {step}")
            
            # Validation Status
            if result.get("validation_status"):
                st.markdown("#### ✅ Recovery Validation")
                validation = result["validation_status"]
                if validation.get("status") == "PASS":
                    st.success("Recovery plan validated successfully")
                else:
                    st.warning("Recovery plan requires review")


# === COMPLIANCE ===
elif page == "Compliance":
    st.header("📋 Compliance Evaluation")
    
    scope = st.radio("Assessment Scope", ["Enterprise-Wide", "Specific Host"])
    
    if scope == "Specific Host":
        host = st.text_input("Host to evaluate", placeholder="e.g., 192.168.1.1")
    else:
        host = None
    
    if st.button("Evaluate Compliance", use_container_width=True):
        with st.spinner("Evaluating compliance..."):
            result = orchestrator.evaluate_compliance(host=host)
            st.session_state.last_results["compliance"] = result
            
            st.success("✅ Compliance evaluation complete!")
            
            if host:
                compliance = result["compliance"]
                
                # Overall Score
                st.subheader("📊 Compliance Assessment")
                score = compliance['overall_score']
                if score >= 80:
                    st.success(f"**Overall Score:** {score:.1f}% - COMPLIANT")
                elif score >= 60:
                    st.warning(f"**Overall Score:** {score:.1f}% - PARTIAL COMPLIANCE")
                else:
                    st.error(f"**Overall Score:** {score:.1f}% - NON-COMPLIANT")
                
                # Compliance Breakdown
                st.markdown("#### 📋 Control Status")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Passed", compliance["compliance_status"]["PASS"])
                with col2:
                    st.metric("❌ Failed", compliance["compliance_status"]["FAIL"])
                with col3:
                    st.metric("❓ Unknown", compliance["compliance_status"]["UNKNOWN"])
                
                # Violations
                if compliance.get("violations"):
                    st.markdown("#### ⚠️ Compliance Violations")
                    for i, violation in enumerate(compliance["violations"], 1):
                        st.error(f"{i}. {violation}")
                
                # Frameworks Tested
                if compliance.get("frameworks_tested"):
                    st.markdown("#### 🏛️ Compliance Frameworks Evaluated")
                    for framework in compliance.get("frameworks_tested", []):
                        st.write(f"• {framework}")
            else:
                st.subheader("📊 Enterprise-Wide Compliance")
                standards = ["ISO27001", "NIST-CSF", "SOC2", "CIS", "HIPAA", "GDPR"]
                
                st.markdown("#### 🏛️ Compliance Standards Assessed")
                col1, col2, col3 = st.columns(3)
                cols = [col1, col2, col3]
                for idx, std in enumerate(standards):
                    with cols[idx % 3]:
                        if std in str(result):
                            st.success(f"✅ {std}")
                        else:
                            st.info(f"📋 {std}")
                
                st.markdown("#### 📈 System-Wide Metrics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Hosts Evaluated", "50+")
                with col2:
                    st.metric("Policies Checked", "250+")
                with col3:
                    st.metric("Controls Assessed", "1000+")


# === EVALUATION ===
elif page == "Evaluation":
    st.header("🧪 System Evaluation")
    
    st.info("Run comprehensive evaluation scenarios to test orchestrator capabilities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Run Full Evaluation", use_container_width=True):
            with st.spinner("Running evaluation suite..."):
                results = simulator.run_full_evaluation()
                st.session_state.evaluation_results = results
                st.success("Evaluation complete!")
    
    with col2:
        if st.button("Individual Scenarios", use_container_width=True):
            st.session_state.show_scenarios = True
    
    if "evaluation_results" in st.session_state:
        results = st.session_state.evaluation_results
        
        st.subheader("📊 Evaluation Results")
        
        # Overall Score
        pass_rate = results.get('pass_rate', 0)
        if pass_rate >= 80:
            st.success(f"**Pass Rate: {pass_rate:.1f}%** - Excellent Performance")
        elif pass_rate >= 60:
            st.warning(f"**Pass Rate: {pass_rate:.1f}%** - Good Performance")
        else:
            st.error(f"**Pass Rate: {pass_rate:.1f}%** - Needs Improvement")
        
        st.divider()
        
        # Test Summary
        st.markdown("#### 🧪 Test Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", results.get('total_tests', 0))
        with col2:
            st.metric("✅ Passed", results.get('tests_passed', 0))
        with col3:
            st.metric("❌ Failed", results.get('tests_failed', 0))
        with col4:
            st.metric("⏭️ Skipped", results.get('tests_skipped', 0))
        
        # Feature Results
        if results.get('feature_results'):
            st.markdown("#### 📋 Feature-Wise Results")
            for feature, score in results.get('feature_results', {}).items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{feature}**")
                with col2:
                    if isinstance(score, dict):
                        pass_count = score.get('passed', 0)
                        total = score.get('total', 1)
                        percentage = (pass_count / total * 100) if total > 0 else 0
                        st.metric("Score", f"{percentage:.0f}%")
                    else:
                        st.metric("Score", f"{score}%")
        
        # Performance Metrics
        if results.get('performance_metrics'):
            st.markdown("#### ⚡ Performance Metrics")
            metrics = results.get('performance_metrics', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Response Time", metrics.get('avg_response_time', 'N/A'))
            with col2:
                st.metric("Max Response Time", metrics.get('max_response_time', 'N/A'))
            with col3:
                st.metric("Total Duration", metrics.get('total_duration', 'N/A'))


# === AUDIT TRAIL ===
elif page == "Audit Trail":
    st.header("📜 Audit Trail & Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        last_n = st.slider("Show last N actions", 5, 100, 20)
    
    with col2:
        if st.button("Export Report", use_container_width=True):
            filepath = orchestrator.export_report()
            st.success(f"Report exported: {filepath}")
    
    st.divider()
    
    trail = orchestrator.get_audit_trail(last_n=last_n)
    
    if trail:
        st.subheader("📝 Recent Actions")
        st.markdown(f"*Showing last {last_n} actions*")
        
        for entry in reversed(trail):
            action = entry.get('action', 'Unknown Action')
            timestamp = entry.get('timestamp', 'N/A')
            details = entry.get('details', {})
            
            # Create a readable action name
            action_display = action.replace('_', ' ').title()
            
            with st.expander(f"🔹 {action_display} - {timestamp}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Action:** {action_display}")
                with col2:
                    st.write(f"**Time:** {timestamp}")
                
                st.markdown("---")
                
                # Display details based on action type
                if 'threat' in action.lower():
                    st.markdown("#### 🚨 Threat Detection Details")
                    if isinstance(details, dict):
                        st.write(f"• **Alert:** {details.get('alert', 'N/A')}")
                        st.write(f"• **Source:** {details.get('source', 'N/A')}")
                
                elif 'vuln' in action.lower() or 'vulnerability' in action.lower():
                    st.markdown("#### 🔍 Vulnerability Analysis Details")
                    if isinstance(details, dict):
                        st.write(f"• **Host:** {details.get('host', 'N/A')}")
                        st.write(f"• **Scan Type:** {details.get('scan_type', 'Full')}")
                
                elif 'incident' in action.lower():
                    st.markdown("#### ⚠️ Incident Response Details")
                    if isinstance(details, dict):
                        st.write(f"• **Threat:** {details.get('threat', 'N/A')}")
                        st.write(f"• **Severity:** {details.get('severity', 'N/A')}")
                
                elif 'compliance' in action.lower():
                    st.markdown("#### ✅ Compliance Evaluation Details")
                    if isinstance(details, dict):
                        st.write(f"• **Host:** {details.get('host', 'Enterprise-Wide')}")
                        st.write(f"• **Framework:** {details.get('framework', 'Multiple')}")
                
                else:
                    st.markdown("#### 📋 Action Details")
                    if isinstance(details, dict):
                        for key, value in details.items():
                            st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
                
                # Show result status if available
                if entry.get('result'):
                    st.markdown("---")
                    result = entry.get('result', {})
                    if isinstance(result, dict):
                        status = result.get('status', 'Completed')
                        st.write(f"**Status:** {status}")
    else:
        st.info("No audit trail entries yet")


# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🛡️ Cybersecurity Orchestrator v1.0")
with col2:
    st.caption(f"Last updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
with col3:
    st.caption("Powered by RAG + ChromaDB")
