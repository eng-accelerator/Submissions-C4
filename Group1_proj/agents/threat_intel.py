"""
Threat Intelligence Agent
Enriches security alerts with CVE data and vulnerability intelligence
"""

from typing import Dict, List, Any
import datetime
from vectorstore.chroma_client import ChromaVectorStore


class ThreatIntelligenceAgent:
    """Enrich threats with CVE and intelligence data"""
    
    def __init__(self, vectorstore: ChromaVectorStore):
        self.vectorstore = vectorstore
        self.name = "ThreatIntelligenceAgent"
    
    
    def enrich_threat(self, threat_description: str) -> Dict[str, Any]:
        """
        Enrich a threat with related CVE intelligence
        
        Args:
            threat_description: Description of the threat
        
        Returns:
            Enriched threat data with CVE context
        """
        cve_docs, cve_meta = self.vectorstore.query("cve", threat_description, top_k=8)
        incident_docs, incident_meta = self.vectorstore.query("incident", threat_description, top_k=5)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "threat": threat_description,
            "related_cves": cve_docs[:3],
            "cve_count": len(cve_docs),
            "related_incidents": incident_docs[:3],
            "incident_count": len(incident_docs),
            "confidence": "HIGH" if (cve_docs or incident_docs) else "LOW",
            "status": "COMPLETED"
        }
    
    
    def get_cve_details(self, vulnerability: str) -> Dict[str, Any]:
        """Retrieve CVE details for a vulnerability"""
        cve_docs, cve_meta = self.vectorstore.query("cve", vulnerability, top_k=5)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "query": vulnerability,
            "cves_found": cve_docs,
            "cve_metadata": cve_meta,
            "total_cves": len(cve_docs)
        }
    
    
    def get_incident_history(self, threat_type: str) -> Dict[str, Any]:
        """Retrieve historical incidents of a specific threat type"""
        incident_docs, incident_meta = self.vectorstore.query("incident", threat_type, top_k=8)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "threat_type": threat_type,
            "historical_incidents": incident_docs,
            "incident_metadata": incident_meta,
            "total_incidents": len(incident_docs)
        }
    
    
    def assess_threat_severity(self, threat: str) -> Dict[str, Any]:
        """Assess threat severity based on intelligence"""
        cve_docs, _ = self.vectorstore.query("cve", threat, top_k=5)
        incident_docs, _ = self.vectorstore.query("incident", threat, top_k=5)
        
        severity = "LOW"
        if len(cve_docs) >= 3 or len(incident_docs) >= 3:
            severity = "CRITICAL"
        elif len(cve_docs) >= 1 or len(incident_docs) >= 1:
            severity = "HIGH"
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "threat": threat,
            "severity": severity,
            "supporting_cves": len(cve_docs),
            "supporting_incidents": len(incident_docs)
        }
