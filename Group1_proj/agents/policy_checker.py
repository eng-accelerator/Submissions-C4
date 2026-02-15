"""
Policy Checker Agent
Evaluates compliance with security policies and standards
"""

from typing import Dict, List, Any
import datetime
from vectorstore.chroma_client import ChromaVectorStore


class PolicyCheckerAgent:
    """Evaluate compliance with security policies"""
    
    def __init__(self, vectorstore: ChromaVectorStore):
        self.vectorstore = vectorstore
        self.name = "PolicyCheckerAgent"
    
    
    def check_host_compliance(self, host: str) -> Dict[str, Any]:
        """
        Check compliance status for a specific host
        
        Args:
            host: Target hostname or IP
        
        Returns:
            Compliance report for host
        """
        policy_docs, policy_meta = self.vectorstore.query("policy", f"compliance policy check on {host}", top_k=8)
        
        compliance_status = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0}
        violations = []
        
        for doc in policy_docs:
            if "PASS" in doc.upper():
                compliance_status["PASS"] += 1
            elif "FAIL" in doc.upper():
                compliance_status["FAIL"] += 1
                violations.append(doc[:100])
            else:
                compliance_status["UNKNOWN"] += 1
        
        overall_score = (compliance_status["PASS"] / max(sum(compliance_status.values()), 1)) * 100
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "host": host,
            "policies_checked": sum(compliance_status.values()),
            "compliance_status": compliance_status,
            "overall_score": round(overall_score, 2),
            "violations": violations,
            "status": "COMPLETED"
        }
    
    
    def get_standard_compliance(self, standard: str) -> Dict[str, Any]:
        """Get compliance level for a specific standard (ISO27001, NIST, SOC2, etc.)"""
        policy_docs, policy_meta = self.vectorstore.query("policy", f"{standard} compliance", top_k=8)
        
        compliant = sum(1 for d in policy_docs if "PASS" in d.upper())
        non_compliant = sum(1 for d in policy_docs if "FAIL" in d.upper())
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "standard": standard,
            "total_checks": len(policy_docs),
            "compliant": compliant,
            "non_compliant": non_compliant,
            "compliance_rate": (compliant / max(len(policy_docs), 1)) * 100,
            "details": policy_docs[:3]
        }
    
    
    def identify_violations(self) -> Dict[str, Any]:
        """Identify all policy violations"""
        policy_docs, policy_meta = self.vectorstore.query("policy", "policy failure violations non-compliance", top_k=10)
        
        violations = [d for d in policy_docs if "FAIL" in d.upper()]
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "total_violations": len(violations),
            "violations": violations,
            "critical_violations": len([v for v in violations if "CRITICAL" in v.upper()])
        }
    
    
    def audit_report(self, host: str = None) -> Dict[str, Any]:
        """Generate compliance audit report"""
        if host:
            policy_docs, _ = self.vectorstore.query("policy", f"audit report {host}", top_k=5)
        else:
            policy_docs, _ = self.vectorstore.query("policy", "audit report compliance check", top_k=10)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "host": host if host else "ENTERPRISE",
            "audit_findings": policy_docs,
            "total_findings": len(policy_docs),
            "report_status": "GENERATED"
        }
