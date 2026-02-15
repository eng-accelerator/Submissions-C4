"""
Vulnerability Scanner Agent
Analyzes vulnerability scans and correlates with CVE data
"""

from typing import Dict, List, Any
import datetime
from vectorstore.chroma_client import ChromaVectorStore


class VulnerabilityAnalysisAgent:
    """Analyze vulnerabilities and correlate with CVE data"""
    
    def __init__(self, vectorstore: ChromaVectorStore):
        self.vectorstore = vectorstore
        self.name = "VulnerabilityAnalysisAgent"
    
    
    def scan_host(self, host: str) -> Dict[str, Any]:
        """
        Analyze vulnerabilities on a specific host
        
        Args:
            host: Target hostname or IP
        
        Returns:
            Vulnerability analysis results
        """
        vuln_docs, vuln_meta = self.vectorstore.query("vuln", f"vulnerability on {host}", top_k=5)
        
        severity_breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for doc in vuln_docs:
            if "CRITICAL" in doc.upper():
                severity_breakdown["CRITICAL"] += 1
            elif "HIGH" in doc.upper():
                severity_breakdown["HIGH"] += 1
            elif "MEDIUM" in doc.upper():
                severity_breakdown["MEDIUM"] += 1
            else:
                severity_breakdown["LOW"] += 1
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "host": host,
            "vulnerabilities_found": len(vuln_docs),
            "vulnerability_details": vuln_docs[:3],
            "severity_breakdown": severity_breakdown,
            "status": "COMPLETED"
        }
    
    
    def get_vulnerabilities_by_severity(self, severity: str) -> Dict[str, Any]:
        """Get vulnerabilities filtered by severity"""
        vuln_docs, vuln_meta = self.vectorstore.query("vuln", f"{severity} severity vulnerability", top_k=8)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "severity_level": severity,
            "vulnerabilities": vuln_docs,
            "count": len(vuln_docs),
            "metadata": vuln_meta
        }
    
    
    def correlate_with_cves(self, vulnerability_id: str) -> Dict[str, Any]:
        """Correlate vulnerability with related CVEs"""
        cve_docs, cve_meta = self.vectorstore.query("cve", vulnerability_id, top_k=5)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "vulnerability_id": vulnerability_id,
            "related_cves": cve_docs,
            "cve_count": len(cve_docs),
            "cve_metadata": cve_meta
        }
    
    
    def remediation_priority(self, host: str) -> Dict[str, Any]:
        """Calculate remediation priority for host"""
        vuln_docs, vuln_meta = self.vectorstore.query("vuln", f"remediation for {host}", top_k=5)
        
        priority_vulns = [d for d in vuln_docs if "CRITICAL" in d.upper() or "HIGH" in d.upper()]
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "host": host,
            "total_vulnerabilities": len(vuln_docs),
            "priority_count": len(priority_vulns),
            "priority_items": priority_vulns[:3],
            "remediation_priority": "URGENT" if len(priority_vulns) > 0 else "LOW"
        }
