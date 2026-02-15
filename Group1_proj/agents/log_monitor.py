"""
Log Monitor Agent
Continuously monitors system and network logs, detects anomalies
"""

from typing import Dict, List, Any
import datetime
from vectorstore.chroma_client import ChromaVectorStore


class LogMonitorAgent:
    """Monitor logs and detect suspicious activity"""
    
    def __init__(self, vectorstore: ChromaVectorStore):
        self.vectorstore = vectorstore
        self.name = "LogMonitorAgent"
    
    
    def analyze_logs(self, host: str = None, severity: str = None) -> Dict[str, Any]:
        """
        Analyze logs for anomalies and threats
        
        Args:
            host: Target host to analyze (optional)
            severity: Filter by severity level (optional)
        
        Returns:
            Analysis results with suspicious patterns
        """
        query = f"suspicious activity patterns on {host}" if host else "anomalous network activity"
        
        documents, metadatas = self.vectorstore.query("logs", query, top_k=5)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "host": host,
            "severity_filter": severity,
            "logs_analyzed": len(documents),
            "suspicious_patterns": documents[:3],
            "metadata": metadatas[:3],
            "alert_count": len(documents),
            "status": "COMPLETED"
        }
    
    
    def detect_brute_force(self, src_ip: str = None) -> Dict[str, Any]:
        """Detect brute force attack patterns"""
        query = f"brute force attack from {src_ip}" if src_ip else "repeated failed login attempts"
        
        documents, metadatas = self.vectorstore.query("logs", query, top_k=5)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "attack_type": "BRUTE_FORCE",
            "source_ip": src_ip,
            "evidence_count": len(documents),
            "evidence": documents[:2],
            "detected": len(documents) > 0
        }
    
    
    def detect_port_scanning(self) -> Dict[str, Any]:
        """Detect port scanning activity"""
        query = "port scan detected network reconnaissance"
        
        documents, metadatas = self.vectorstore.query("logs", query, top_k=5)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent": self.name,
            "attack_type": "PORT_SCAN",
            "evidence_count": len(documents),
            "evidence": documents[:2],
            "detected": len(documents) > 0
        }
