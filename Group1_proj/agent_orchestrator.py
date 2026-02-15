"""
Agentic Cybersecurity Orchestrator
Powered by Retrieval-Augmented Generation (RAG) with ChromaDB Vector Store

Mission:
- Continuously monitor system and network activity
- Detect threats and enrich with CVE intelligence
- Analyze vulnerabilities and generate remediation playbooks
- Evaluate compliance with full auditability and explainability
"""

import os
import json
import datetime
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_PATH = os.getenv("BASE_PATH", "./cyber_demo")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")

print("[*] Initializing Agentic Cybersecurity Orchestrator...")


class CybersecurityRAGOrchestrator:
    """RAG-powered orchestrator for cybersecurity threat detection and response"""
    
    def __init__(self, vectorstore_path: str = "./cyber_vector_db"):
        """Initialize the orchestrator with ChromaDB connections"""
        print("[*] Connecting to ChromaDB vector store...")
        
        self.vectorstore_path = vectorstore_path
        self.base_chroma = Chroma(persist_directory=vectorstore_path)
        
        # Initialize collection clients
        self.logs_collection = self.base_chroma._client.get_or_create_collection(
            name="logs_collection",
            metadata={"description": "System and network logs"}
        )
        self.cve_collection = self.base_chroma._client.get_or_create_collection(
            name="cve_collection",
            metadata={"description": "CVE vulnerability records"}
        )
        self.vuln_collection = self.base_chroma._client.get_or_create_collection(
            name="vuln_collection",
            metadata={"description": "Vulnerability scan results"}
        )
        self.incident_collection = self.base_chroma._client.get_or_create_collection(
            name="incident_collection",
            metadata={"description": "Historical security incidents"}
        )
        self.policy_collection = self.base_chroma._client.get_or_create_collection(
            name="policy_collection",
            metadata={"description": "Compliance and policy records"}
        )
        
        # Initialize LLM
        print("[*] Initializing OpenRouter LLM...")
        self.llm = ChatOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-4-turbo",
            temperature=0.7
        )
        
        # Audit trail
        self.audit_trail = []
        
        print("[✓] Orchestrator initialized successfully")
    
    
    def log_audit(self, action: str, details: Dict[str, Any], result: Any = None):
        """Log all actions for full auditability"""
        audit_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "result": result
        }
        self.audit_trail.append(audit_entry)
        print(f"[AUDIT] {action} - {datetime.datetime.utcnow().isoformat()}")
    
    
    def rag_query(self, query: str, collection_name: str, top_k: int = 5) -> Tuple[List[Dict], List[str]]:
        """
        RAG Rule - Semantic retrieval from Chroma
        
        Args:
            query: Semantic search query
            collection_name: Target collection name
            top_k: Number of top results (5-8 recommended)
        
        Returns:
            Tuple of (retrieved_documents, retrieved_ids)
        """
        print(f"\n  [RAG] Querying {collection_name} for: '{query}'")
        self.log_audit("rag_query_start", {
            "query": query,
            "collection": collection_name,
            "top_k": top_k
        })
        
        try:
            # Get appropriate collection
            collection_map = {
                "logs": self.logs_collection,
                "cve": self.cve_collection,
                "vuln": self.vuln_collection,
                "incident": self.incident_collection,
                "policy": self.policy_collection
            }
            
            collection = collection_map.get(collection_name)
            if not collection:
                print(f"  [!] Collection '{collection_name}' not found")
                return [], []
            
            # Query with semantic search
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if results and results.get('documents'):
                retrieved_docs = results['documents'][0]
                retrieved_ids = results.get('ids', [[]])[0]
                metadatas = results.get('metadatas', [[]])[0]
                
                print(f"  [✓] Retrieved {len(retrieved_docs)} documents from {collection_name}")
                self.log_audit("rag_query_success", {
                    "collection": collection_name,
                    "results_count": len(retrieved_docs)
                }, retrieved_docs[:2])  # Log first 2 results
                
                return retrieved_docs, metadatas
            else:
                print(f"  [!] No documents found in {collection_name}")
                self.log_audit("rag_query_empty", {"collection": collection_name})
                return [], []
                
        except Exception as e:
            print(f"  [ERROR] RAG query failed: {str(e)}")
            self.log_audit("rag_query_error", {"error": str(e)})
            return [], []
    
    
    def detect_threats(self, alert_query: str) -> Dict[str, Any]:
        """
        Threat Detection Agent
        - Formulate retrieval query
        - Search logs and incidents for similar threats
        - Enrich with CVE intelligence
        - Generate threat assessment
        """
        print(f"\n[AGENT] Threat Detection triggered: {alert_query}")
        self.log_audit("threat_detection_start", {"alert": alert_query})
        
        # Step 1: Search logs for similar patterns
        log_docs, log_meta = self.rag_query(alert_query, "logs", top_k=5)
        
        # Step 2: Search historical incidents
        incident_docs, incident_meta = self.rag_query(alert_query, "incident", top_k=5)
        
        # Step 3: Build response with evidence
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "alert": alert_query,
            "threat_level": "UNKNOWN",
            "retrieved_logs": log_docs[:3],
            "retrieved_incidents": incident_docs[:3],
            "analysis": None,
            "evidence_summary": None,
            "recommendations": []
        }
        
        # Step 4: Generate analysis if evidence found
        if log_docs or incident_docs:
            evidence_text = f"""
            Similar Logs Found: {len(log_docs)} records
            Similar Incidents: {len(incident_docs)} records
            
            Top Log Context:
            {log_docs[0] if log_docs else 'None'}
            
            Top Incident Context:
            {incident_docs[0] if incident_docs else 'None'}
            """
            
            analysis_prompt = f"""
            Given this security alert and retrieved context, assess the threat level:
            
            ALERT: {alert_query}
            
            CONTEXT FROM VECTOR STORE:
            {evidence_text}
            
            Provide:
            1. Threat Level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
            2. Confidence Score (0-100)
            3. Key Indicators
            4. Recommended Actions
            """
            
            try:
                analysis = self.llm.invoke(analysis_prompt)
                response["analysis"] = analysis.content
                response["evidence_summary"] = f"Found {len(log_docs)} log matches and {len(incident_docs)} incident matches"
                
                # Extract threat level from analysis
                if "CRITICAL" in analysis.content.upper():
                    response["threat_level"] = "CRITICAL"
                elif "HIGH" in analysis.content.upper():
                    response["threat_level"] = "HIGH"
                elif "MEDIUM" in analysis.content.upper():
                    response["threat_level"] = "MEDIUM"
                else:
                    response["threat_level"] = "LOW"
                    
            except Exception as e:
                response["analysis"] = f"Analysis generation failed: {str(e)}"
                response["threat_level"] = "UNKNOWN"
        else:
            response["evidence_summary"] = "No similar logs or incidents found in vector store"
            response["threat_level"] = "UNVERIFIED"
        
        self.log_audit("threat_detection_complete", response)
        return response
    
    
    def enrich_with_cve(self, vulnerability_description: str) -> Dict[str, Any]:
        """
        CVE Enrichment Agent
        - Query CVE database for related vulnerabilities
        - Extract affected products and severity scores
        - Return grounded CVE intelligence
        """
        print(f"\n[AGENT] CVE Enrichment triggered: {vulnerability_description[:80]}...")
        self.log_audit("cve_enrichment_start", {"vulnerability": vulnerability_description[:100]})
        
        # Query CVE collection
        cve_docs, cve_meta = self.rag_query(vulnerability_description, "cve", top_k=8)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "vulnerability": vulnerability_description,
            "related_cves": cve_docs[:5],
            "cve_count": len(cve_docs),
            "affected_products": [],
            "max_severity": 0.0,
            "analysis": None,
            "confidence": "LOW" if not cve_docs else "HIGH"
        }
        
        if cve_docs:
            # Extract CVE details from metadata
            for meta in cve_meta:
                if isinstance(meta, dict):
                    if "affected_products" in str(meta):
                        response["affected_products"].append(str(meta))
            
            # Generate CVE analysis
            cve_context = "\n".join(cve_docs[:3]) if cve_docs else "No CVE data found"
            analysis_prompt = f"""
            Based on retrieved CVE data, analyze this vulnerability:
            
            VULNERABILITY: {vulnerability_description}
            
            RETRIEVED CVE DATA:
            {cve_context}
            
            Provide:
            1. Most Relevant CVE IDs (only from retrieved data)
            2. CVSS Score Range
            3. Affected Platforms
            4. Exploitability Assessment
            
            **CRITICAL**: Only cite CVEs and details that appear in the retrieved data above.
            If not found, state explicitly: "No evidence found in vector store"
            """
            
            try:
                analysis = self.llm.invoke(analysis_prompt)
                response["analysis"] = analysis.content
            except Exception as e:
                response["analysis"] = f"Analysis failed: {str(e)}"
        else:
            response["analysis"] = "No related CVEs found in vector store - vulnerability may be novel or internal"
            response["confidence"] = "LOW"
        
        self.log_audit("cve_enrichment_complete", response)
        return response
    
    
    def analyze_vulnerabilities(self, host: str) -> Dict[str, Any]:
        """
        Vulnerability Analysis Agent
        - Search vulnerability scans for host
        - Correlate with CVE data
        - Prioritize by severity
        """
        print(f"\n[AGENT] Vulnerability Analysis for host: {host}")
        self.log_audit("vuln_analysis_start", {"host": host})
        
        # Query vulnerability collection
        vuln_query = f"vulnerability scan on {host}"
        vuln_docs, vuln_meta = self.rag_query(vuln_query, "vuln", top_k=5)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "host": host,
            "vulnerabilities_found": len(vuln_docs),
            "vulnerability_details": vuln_docs[:5],
            "severity_breakdown": {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            },
            "remediation_required": [],
            "analysis": None
        }
        
        # Count by severity
        for doc in vuln_docs:
            if "CRITICAL" in doc.upper():
                response["severity_breakdown"]["CRITICAL"] += 1
            elif "HIGH" in doc.upper():
                response["severity_breakdown"]["HIGH"] += 1
            elif "MEDIUM" in doc.upper():
                response["severity_breakdown"]["MEDIUM"] += 1
            else:
                response["severity_breakdown"]["LOW"] += 1
        
        if vuln_docs:
            analysis_prompt = f"""
            Analyze vulnerabilities found on host {host}:
            
            VULNERABILITY SCAN RESULTS:
            {chr(10).join(vuln_docs[:3])}
            
            Provide prioritized remediation focus areas (top 3):
            """
            
            try:
                analysis = self.llm.invoke(analysis_prompt)
                response["analysis"] = analysis.content
            except Exception as e:
                response["analysis"] = f"Analysis failed: {str(e)}"
        else:
            response["analysis"] = f"No vulnerabilities found for {host} in vector store"
        
        self.log_audit("vuln_analysis_complete", response)
        return response
    
    
    def generate_remediation_playbook(self, threat: str, severity: str) -> Dict[str, Any]:
        """
        Remediation Playbook Generation Agent
        - Search historical incidents for similar threats
        - Query policies and vulnerability scans
        - Generate actionable playbook with evidence
        """
        print(f"\n[AGENT] Generating Remediation Playbook for {threat} [{severity}]")
        self.log_audit("playbook_generation_start", {"threat": threat, "severity": severity})
        
        # Search incidents
        incident_docs, _ = self.rag_query(threat, "incident", top_k=5)
        
        # Search policies
        policy_docs, _ = self.rag_query(f"remediation for {threat}", "policy", top_k=5)
        
        # Search vulnerabilities
        vuln_docs, _ = self.rag_query(threat, "vuln", top_k=5)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "threat": threat,
            "severity": severity,
            "incident_context": incident_docs[:2],
            "policy_context": policy_docs[:2],
            "playbook_steps": [],
            "estimated_resolution_time": "UNKNOWN",
            "required_resources": [],
            "compliance_considerations": []
        }
        
        # Generate playbook
        playbook_prompt = f"""
        Create a cybersecurity remediation playbook based on:
        
        THREAT: {threat}
        SEVERITY: {severity}
        
        SIMILAR INCIDENTS:
        {chr(10).join(incident_docs[:2]) if incident_docs else 'No historical data'}
        
        RELEVANT POLICIES:
        {chr(10).join(policy_docs[:2]) if policy_docs else 'No policies found'}
        
        RELATED VULNERABILITIES:
        {chr(10).join(vuln_docs[:2]) if vuln_docs else 'No vulnerabilities found'}
        
        Generate step-by-step playbook with:
        1. Immediate Actions (0-1 hour)
        2. Short-term Actions (1-24 hours)
        3. Investigation Steps
        4. Recovery Procedures
        5. Validation Checks
        
        Base recommendations only on the retrieved context. Clearly state if no historical data exists.
        """
        
        try:
            playbook = self.llm.invoke(playbook_prompt)
            response["playbook_steps"] = playbook.content
            
            # Extract severity-based timeline
            if severity == "CRITICAL":
                response["estimated_resolution_time"] = "< 30 minutes"
                response["required_resources"] = ["SOC Lead", "Incident Commander", "Threat Intel", "Network Engineering"]
            elif severity == "HIGH":
                response["estimated_resolution_time"] = "1-4 hours"
                response["required_resources"] = ["SOC Analyst", "System Admin"]
            else:
                response["estimated_resolution_time"] = "4-24 hours"
                response["required_resources"] = ["SOC Analyst"]
                
        except Exception as e:
            response["playbook_steps"] = f"Playbook generation failed: {str(e)}"
        
        self.log_audit("playbook_generation_complete", response)
        return response
    
    
    def evaluate_compliance(self, host: str) -> Dict[str, Any]:
        """
        Compliance Evaluation Agent
        - Query policy collection for host
        - Assess compliance status
        - Identify policy violations
        """
        print(f"\n[AGENT] Compliance Evaluation for host: {host}")
        self.log_audit("compliance_evaluation_start", {"host": host})
        
        # Query policies
        policy_query = f"compliance policy check on {host}"
        policy_docs, policy_meta = self.rag_query(policy_query, "policy", top_k=8)
        
        response = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "host": host,
            "total_policies_checked": len(policy_docs),
            "policy_results": policy_docs[:5],
            "compliance_status": {
                "PASS": 0,
                "FAIL": 0,
                "UNKNOWN": 0
            },
            "violations": [],
            "remediation_required": [],
            "analysis": None
        }
        
        # Count compliance status
        for doc in policy_docs:
            if "PASS" in doc.upper():
                response["compliance_status"]["PASS"] += 1
            elif "FAIL" in doc.upper():
                response["compliance_status"]["FAIL"] += 1
                response["violations"].append(doc[:100])
            else:
                response["compliance_status"]["UNKNOWN"] += 1
        
        # Generate compliance analysis
        if policy_docs:
            compliance_prompt = f"""
            Evaluate compliance for host {host} based on policy results:
            
            POLICY CHECK RESULTS:
            {chr(10).join(policy_docs[:3])}
            
            Provide:
            1. Overall Compliance Score (%)
            2. Critical Violations
            3. Remediation Priority
            4. Audit Findings Summary
            """
            
            try:
                analysis = self.llm.invoke(compliance_prompt)
                response["analysis"] = analysis.content
            except Exception as e:
                response["analysis"] = f"Analysis failed: {str(e)}"
        else:
            response["analysis"] = f"No policy records found for {host}"
        
        self.log_audit("compliance_evaluation_complete", response)
        return response
    
    
    def get_audit_trail(self, last_n: int = 20) -> List[Dict]:
        """Retrieve audit trail for full transparency"""
        return self.audit_trail[-last_n:]
    
    
    def export_report(self, filename: str = None) -> str:
        """Export complete audit trail and findings"""
        if filename is None:
            filename = f"cybersec_report_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "audit_trail": self.audit_trail,
            "total_actions": len(self.audit_trail),
            "summary": {
                "threats_detected": sum(1 for a in self.audit_trail if "threat_detection" in a["action"]),
                "analyses_performed": sum(1 for a in self.audit_trail if "analysis" in a["action"]),
                "policies_evaluated": sum(1 for a in self.audit_trail if "compliance" in a["action"])
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[✓] Report exported to {filename}")
        return filename


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("AGENTIC CYBERSECURITY ORCHESTRATOR - RAG-POWERED THREAT INTELLIGENCE")
    print("="*80)
    
    try:
        # Initialize orchestrator
        orchestrator = CybersecurityRAGOrchestrator()
        
        print("\n[*] Running demonstration scenarios...\n")
        
        # Scenario 1: Threat Detection
        print("\n" + "-"*80)
        print("SCENARIO 1: THREAT DETECTION")
        print("-"*80)
        threat_result = orchestrator.detect_threats(
            "Brute force attack detected on port 22 from 122.161.239.59"
        )
        print(f"\n[RESULT] Threat Level: {threat_result['threat_level']}")
        print(f"         Evidence: {threat_result['evidence_summary']}")
        
        # Scenario 2: CVE Enrichment
        print("\n" + "-"*80)
        print("SCENARIO 2: CVE ENRICHMENT")
        print("-"*80)
        cve_result = orchestrator.enrich_with_cve(
            "Weak cipher suite vulnerability in TLS implementation"
        )
        print(f"\n[RESULT] CVEs Found: {cve_result['cve_count']}")
        print(f"         Confidence: {cve_result['confidence']}")
        
        # Scenario 3: Vulnerability Analysis
        print("\n" + "-"*80)
        print("SCENARIO 3: VULNERABILITY ANALYSIS")
        print("-"*80)
        vuln_result = orchestrator.analyze_vulnerabilities("114.210.246.246")
        print(f"\n[RESULT] Vulnerabilities Found: {vuln_result['vulnerabilities_found']}")
        print(f"         Severity Breakdown: {vuln_result['severity_breakdown']}")
        
        # Scenario 4: Remediation Playbook
        print("\n" + "-"*80)
        print("SCENARIO 4: REMEDIATION PLAYBOOK GENERATION")
        print("-"*80)
        playbook = orchestrator.generate_remediation_playbook(
            "Brute force attack",
            "HIGH"
        )
        print(f"\n[RESULT] Estimated Resolution Time: {playbook['estimated_resolution_time']}")
        print(f"         Required Resources: {playbook['required_resources']}")
        
        # Scenario 5: Compliance Evaluation
        print("\n" + "-"*80)
        print("SCENARIO 5: COMPLIANCE EVALUATION")
        print("-"*80)
        compliance = orchestrator.evaluate_compliance("9.251.108.218")
        print(f"\n[RESULT] Policies Checked: {compliance['total_policies_checked']}")
        print(f"         Compliance Status: {compliance['compliance_status']}")
        
        # Export report
        print("\n" + "="*80)
        print("EXPORTING AUDIT TRAIL AND FINDINGS")
        print("="*80)
        report_file = orchestrator.export_report()
        print(f"\n[✓] Full audit trail exported: {report_file}")
        
    except Exception as e:
        print(f"\n[ERROR] Orchestrator execution failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
