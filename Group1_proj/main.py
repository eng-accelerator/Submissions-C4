"""
FastAPI Entry Point
RESTful API for the Cybersecurity Orchestrator
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

from orchestrator.supervisor import SecurityOrchestrator
from evaluation.simulator import SecuritySimulator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Cybersecurity Orchestrator API",
    description="RAG-powered threat detection, vulnerability analysis, and incident response",
    version="1.0.0"
)

# Initialize orchestrator
orchestrator = SecurityOrchestrator()

# Request models
class ThreatAlertRequest(BaseModel):
    alert: str
    source: Optional[str] = None


class HostAnalysisRequest(BaseModel):
    host: str


class IncidentRequest(BaseModel):
    threat: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW


class ComplianceRequest(BaseModel):
    host: Optional[str] = None
    standard: Optional[str] = None


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "operational",
        "service": "Cybersecurity Orchestrator",
        "version": "1.0.0"
    }


@app.post("/api/threat/detect")
async def detect_threat(request: ThreatAlertRequest):
    """Detect and analyze security threats"""
    try:
        result = orchestrator.detect_threat(request.alert)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vulnerabilities/analyze")
async def analyze_vulnerabilities(request: HostAnalysisRequest):
    """Analyze host vulnerabilities"""
    try:
        result = orchestrator.analyze_host_vulnerabilities(request.host)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/incident/respond")
async def respond_to_incident(request: IncidentRequest):
    """Generate incident response playbook"""
    try:
        result = orchestrator.handle_incident(request.threat, request.severity)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/evaluate")
async def evaluate_compliance(request: ComplianceRequest):
    """Evaluate security compliance"""
    try:
        result = orchestrator.evaluate_compliance(host=request.host)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/assessment/full")
async def full_security_assessment(request: HostAnalysisRequest):
    """Execute full security assessment"""
    try:
        result = orchestrator.full_security_assessment(host=request.host)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/trail")
async def get_audit_trail(last_n: int = 20):
    """Retrieve audit trail"""
    try:
        trail = orchestrator.get_audit_trail(last_n=last_n)
        return {
            "status": "success",
            "data": trail
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audit/export")
async def export_audit_report(filename: Optional[str] = None):
    """Export audit report"""
    try:
        filepath = orchestrator.export_report(filename=filename)
        return {
            "status": "success",
            "file": filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluation/run")
async def run_evaluation(background_tasks: BackgroundTasks):
    """Run full evaluation suite"""
    try:
        simulator = SecuritySimulator(orchestrator=orchestrator)
        results = simulator.run_full_evaluation()
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": str(__import__('datetime').datetime.utcnow()),
        "orchestrator": "operational",
        "vectorstore": "connected"
    }


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    print(f"\n[*] Starting Cybersecurity Orchestrator API on port {port}...")
    print(f"[*] Docs available at http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
