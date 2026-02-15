"""
FastAPI application: log upload and incident analysis API.
"""

from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.workflow import build_incident_graph
from config import OPENROUTER_API_KEY

app = FastAPI(
    title="DevOps Incident Analysis API",
    description="Upload ops logs for analysis; returns parsed entries, classified issues, remediations, and cookbook.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    """Inline log content for analysis (alternative to file upload)."""
    content: str


class AnalysisResponse(BaseModel):
    """Response after running incident analysis."""
    parsed_entries_count: int
    classified_issues_count: int
    remediations_count: int
    cookbook_preview: str
    notifications_sent: bool = False
    jira_ticket_id: Optional[str] = None
    state: Optional[dict] = None


def _run_analysis(raw_logs: str) -> dict:
    graph = build_incident_graph()
    initial = {
        "raw_logs": raw_logs,
        "parsed_entries": [],
        "classified_issues": [],
        "remediations": [],
        "cookbook": "",
        "notifications_sent": False,
        "jira_ticket_id": None,
    }
    result = graph.invoke(initial)
    return result


@app.get("/health")
def health():
    return {"status": "ok", "openrouter_configured": bool(OPENROUTER_API_KEY)}


@app.post("/upload", response_model=AnalysisResponse)
async def upload_log(file: UploadFile = File(...)):
    """Upload a log file and run full incident analysis."""
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    content = await file.read()
    try:
        raw_logs = content.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(400, "File could not be decoded as UTF-8")
    return _analysis_to_response(_run_analysis(raw_logs))


@app.post("/analyze", response_model=AnalysisResponse)
def analyze_logs(request: AnalysisRequest):
    """Run incident analysis on inline log content."""
    return _analysis_to_response(_run_analysis(request.content))


def _analysis_to_response(state: dict) -> AnalysisResponse:
    parsed = state.get("parsed_entries") or []
    issues = state.get("classified_issues") or []
    remediations = state.get("remediations") or []
    cookbook = state.get("cookbook") or ""
    return AnalysisResponse(
        parsed_entries_count=len(parsed),
        classified_issues_count=len(issues),
        remediations_count=len(remediations),
        cookbook_preview=cookbook[:2000] + ("..." if len(cookbook) > 2000 else ""),
        notifications_sent=state.get("notifications_sent", False),
        jira_ticket_id=state.get("jira_ticket_id"),
        state={
            "parsed_entries": parsed,
            "classified_issues": issues,
            "remediations": remediations,
            "cookbook": cookbook,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
