# Multi-agent DevOps Incident Analysis Suite

An application that lets you upload ops logs for live analysis.

**Workflow diagram:** See [docs/workflow_diagram.md](docs/workflow_diagram.md) for Mermaid flowcharts (view in GitHub, VS Code, or any Mermaid renderer). Multiple agents (log classifier, remediation, cookbook synthesizer, Slack notifier, JIRA ticket) work together under a **LangGraph** orchestrator to parse logs, classify issues, suggest fixes, and optionally notify Slack and create JIRA tickets.

## Features

- **Universal log parser**: JSON, syslog, Apache, Nginx, custom formats; multi-line stack traces.
- **Log classifier agent**: Categories (database, network, application, infrastructure) and severity (CRITICAL/HIGH/MEDIUM/LOW).
- **Remediation agent**: RAG over a runbook knowledge base (ChromaDB) to map issues to fixes.
- **Cookbook synthesizer**: Produces one actionable markdown cookbook per run.
- **Slack notification agent**: Block Kit messages, channel routing by severity.
- **JIRA ticket agent**: Creates tickets for CRITICAL issues with duplicate detection.
- **LangGraph workflow**: Parse → Classify → Find remediations → Generate cookbook → (optional) Notify Slack → (optional) Create JIRA.
- **Streamlit UI**: Upload file, select sample logs, or paste text; run analysis and view results.
- **REST API**: `POST /upload` and `POST /analyze` for integration.

## Setup

1. **Clone and install**

   ```bash
   cd devops_incident_handler
   pip install -r requirements.txt
   ```

2. **Environment**

   Copy `.env.example` to `.env` and set at least:

   - `OPENROUTER_API_KEY` – required for LLM (classification, remediation, cookbook).
   - Optionally: `OPENAI_API_KEY` for embeddings (if not set, a local embedding fallback may be used where applicable).
   - Optional: `SLACK_BOT_TOKEN`, `JIRA_*` for notifications and tickets.

3. **Seed runbooks (recommended)**

   ```bash
   python seed_runbooks.py
   ```

4. **Run UI**

   ```bash
   streamlit run app.py
   ```

5. **Run API**

   ```bash
   uvicorn api_main:app --reload --host 0.0.0.0 --port 8000
   ```

## API

- **GET /health** – Health check; indicates if OpenRouter is configured.
- **POST /upload** – Body: multipart file upload. Runs full analysis and returns parsed entries, issues, remediations, cookbook preview, and notification/JIRA info.
- **POST /analyze** – Body: `{"content": "<log text>"}`. Same pipeline on inline content.

## Sample logs

Place sample logs in `sample_logs/` or use the ones provided:

- `syslog_nginx_errors.txt` – Nginx syslog-style errors
- `json_app_logs.json` – JSON application logs
- `apache_combined.log` – Apache combined log
- `stacktrace.log` – Application stack trace

## Project layout

- `config.py` – Env-based config (OpenRouter, Slack, JIRA, ChromaDB).
- `models.py` – `LogEntry`, `ClassifiedIssue`, `RemediationPlan`.
- `utils/log_parser.py` – Universal log parser.
- `utils/knowledge_base.py` – ChromaDB remediation KB and RAG.
- `agents/log_classifier.py` – Issue classification agent.
- `agents/remediation_agent.py` – Remediation mapping agent.
- `agents/cookbook_synthesizer.py` – Cookbook generation agent.
- `agents/slack_notifier.py` – Slack Block Kit notifier.
- `agents/jira_agent.py` – JIRA ticket creation/comment.
- `agents/workflow.py` – LangGraph incident workflow.
- `app.py` – Streamlit UI.
- `api_main.py` – FastAPI upload/analyze API.
- `seed_runbooks.py` – Seed sample runbooks into the KB.
- `tests/test_log_parser.py` – Parser unit tests.

## Tests

```bash
pytest tests/ -v
```

## Notes

- **OpenRouter**: The app uses the OpenRouter API for the main LLM; set `OPENROUTER_BASE_URL` and `OPENROUTER_MODEL` in `.env` if you need a different model.
- **Embeddings**: ChromaDB uses OpenAI-style embeddings when `OPENAI_API_KEY` is set; otherwise a local embedding model may be used (e.g. sentence-transformers if installed).
- **Slack/JIRA**: Notifications and JIRA creation are best-effort; missing tokens are skipped without failing the pipeline.
