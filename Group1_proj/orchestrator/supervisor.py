"""
Orchestrator Supervisor
Coordinates all agents and manages the RAG-powered cybersecurity workflow
"""

import datetime
import json
from typing import Dict, List, Any
from vectorstore.chroma_client import ChromaVectorStore
from agents.log_monitor import LogMonitorAgent
from agents.threat_intel import ThreatIntelligenceAgent
from agents.vuln_scanner import VulnerabilityAnalysisAgent
from agents.incident_response import IncidentResponseAgent
from agents.policy_checker import PolicyCheckerAgent


class SecurityOrchestrator:
    """Master orchestrator for coordinating all security agents"""
    
    def __init__(self, vectorstore_path: str = "./cyber_vector_db"):
        """Initialize orchestrator with all agents"""
        print("\n[*] Initializing Security Orchestrator...")
        
        # Initialize vectorstore
        self.vectorstore = ChromaVectorStore(vectorstore_path=vectorstore_path)
        
        # Initialize all agents
        self.log_monitor = LogMonitorAgent(self.vectorstore)
        self.threat_intel = ThreatIntelligenceAgent(self.vectorstore)
        self.vuln_scanner = VulnerabilityAnalysisAgent(self.vectorstore)
        self.incident_response = IncidentResponseAgent(self.vectorstore)
        self.policy_checker = PolicyCheckerAgent(self.vectorstore)
        
        # Audit trail
        self.audit_trail = []
        
        print("[✓] Orchestrator initialized with all agents")
    
    
    def _log_action(self, action: str, details: Dict[str, Any], result: Any = None):
        """Internal audit logging"""
        audit_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "result": result
        }
        self.audit_trail.append(audit_entry)
    
    
    def detect_threat(self, alert: str) -> Dict[str, Any]:
        """
        Orchestrated threat detection workflow
        1. Monitor logs for patterns
        2. Enrich with threat intelligence
        3. Assess severity
        """
        print(f"\n[ORCHESTRATOR] Threat Detection: {alert}")
        self._log_action("threat_detection_start", {"alert": alert})
        
        # Step 1: Analyze logs
        log_analysis = self.log_monitor.analyze_logs()
        
        # Step 2: Enrich with threat intel
        threat_enrichment = self.threat_intel.enrich_threat(alert)
        
        # Step 3: Assess severity
        severity_assessment = self.threat_intel.assess_threat_severity(alert)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "alert": alert,
            "threat_level": severity_assessment["severity"],
            "log_analysis": log_analysis,
            "threat_enrichment": threat_enrichment,
            "severity_assessment": severity_assessment,
            "status": "COMPLETE"
        }
        
        self._log_action("threat_detection_complete", response)
        return response
    
    
    def analyze_host_vulnerabilities(self, host: str) -> Dict[str, Any]:
        """
        Orchestrated vulnerability analysis workflow
        1. Scan host vulnerabilities
        2. Get remediation priorities
        3. Check compliance
        """
        print(f"\n[ORCHESTRATOR] Vulnerability Analysis: {host}")
        self._log_action("vuln_analysis_start", {"host": host})
        
        # Step 1: Scan vulnerabilities
        vuln_scan = self.vuln_scanner.scan_host(host)
        
        # Step 2: Get remediation priorities
        remediation = self.vuln_scanner.remediation_priority(host)
        
        # Step 3: Check compliance
        compliance = self.policy_checker.check_host_compliance(host)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "host": host,
            "vulnerability_scan": vuln_scan,
            "remediation_priority": remediation,
            "compliance_status": compliance,
            "status": "COMPLETE"
        }
        
        self._log_action("vuln_analysis_complete", response)
        return response
    
    
    def handle_incident(self, threat: str, severity: str) -> Dict[str, Any]:
        """
        Orchestrated incident response workflow
        1. Generate playbook
        2. Get historical context
        3. Determine recovery procedures
        4. Validate recovery
        """
        print(f"\n[ORCHESTRATOR] Incident Response: {threat} [{severity}]")
        self._log_action("incident_response_start", {"threat": threat, "severity": severity})
        
        # Step 1: Generate playbook
        playbook = self.incident_response.generate_playbook(threat, severity)
        
        # Step 2: Historical context
        history = self.incident_response.get_historical_response(threat)
        
        # Step 3: Recovery procedures
        recovery = self.incident_response.get_recovery_procedures(threat)
        
        # Step 4: Validation
        validation = self.incident_response.validate_recovery(f"INC-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "threat": threat,
            "severity": severity,
            "playbook": playbook,
            "historical_context": history,
            "recovery_procedures": recovery,
            "validation_status": validation,
            "status": "READY"
        }
        
        self._log_action("incident_response_complete", response)
        return response
    
    
    def evaluate_compliance(self, host: str = None) -> Dict[str, Any]:
        """Evaluate compliance across enterprise or specific host"""
        print(f"\n[ORCHESTRATOR] Compliance Evaluation: {host if host else 'ENTERPRISE'}")
        self._log_action("compliance_eval_start", {"host": host})
        
        if host:
            compliance = self.policy_checker.check_host_compliance(host)
        else:
            # Enterprise-wide compliance
            iso_compliance = self.policy_checker.get_standard_compliance("ISO27001")
            nist_compliance = self.policy_checker.get_standard_compliance("NIST-CSF")
            soc2_compliance = self.policy_checker.get_standard_compliance("SOC2")
            
            compliance = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "scope": "ENTERPRISE",
                "iso27001": iso_compliance,
                "nist_csf": nist_compliance,
                "soc2": soc2_compliance,
                "status": "COMPLETE"
            }
        
        violations = self.policy_checker.identify_violations()
        audit_report = self.policy_checker.audit_report(host)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "host": host if host else "ENTERPRISE",
            "compliance": compliance,
            "violations": violations,
            "audit_report": audit_report,
            "status": "COMPLETE"
        }
        
        self._log_action("compliance_eval_complete", response)
        return response
    
    
    def full_security_assessment(self, host: str = None) -> Dict[str, Any]:
        """Execute comprehensive security assessment"""
        print(f"\n[ORCHESTRATOR] Full Security Assessment: {host if host else 'ENTERPRISE'}")
        
        results = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "scope": host if host else "ENTERPRISE",
            "assessment_modules": {}
        }
        
        if host:
            # Host-specific assessment
            results["assessment_modules"]["vulnerabilities"] = self.analyze_host_vulnerabilities(host)
            results["assessment_modules"]["compliance"] = self.evaluate_compliance(host)
        else:
            # Enterprise assessment
            results["assessment_modules"]["compliance"] = self.evaluate_compliance()
        
        return results
    
    
    def get_audit_trail(self, last_n: int = 20) -> List[Dict]:
        """Retrieve audit trail"""
        return self.audit_trail[-last_n:]
    
    
    def export_report(self, filename: str = None) -> str:
        """Export full audit trail and findings"""
        if filename is None:
            filename = f"security_report_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "audit_trail": self.audit_trail,
            "total_actions": len(self.audit_trail),
            "summary": {
                "threat_detections": sum(1 for a in self.audit_trail if "threat_detection" in a["action"]),
                "vulnerability_analyses": sum(1 for a in self.audit_trail if "vuln_analysis" in a["action"]),
                "incident_responses": sum(1 for a in self.audit_trail if "incident_response" in a["action"]),
                "compliance_evaluations": sum(1 for a in self.audit_trail if "compliance_eval" in a["action"])
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[✓] Report exported to {filename}")
        return filename
