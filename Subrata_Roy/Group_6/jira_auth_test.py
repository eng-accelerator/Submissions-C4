"""
JIRA Authentication Test Script

Sample script to verify JIRA credentials and connectivity.
Focus: Authentication — logs each step and common auth failure cases.
Run: python jira_auth_test.py
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"jira_auth_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("jira_auth_test")


def log_section(title: str) -> None:
    logger.info("")
    logger.info("=" * 60)
    logger.info("  %s", title)
    logger.info("=" * 60)


def main() -> int:
    log_section("JIRA Authentication Test")

    # -----------------------------------------------------------------------
    # 1. Load environment
    # -----------------------------------------------------------------------
    log_section("1. Loading environment variables")

    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info(".env loaded (if present)")
    except ImportError:
        logger.warning("python-dotenv not installed; using process env only")

    # JIRA_SERVER = (os.getenv("JIRA_SERVER") or "").strip()
    # JIRA_EMAIL = (os.getenv("JIRA_EMAIL") or "").strip()
    # JIRA_API_TOKEN = (os.getenv("JIRA_API_TOKEN") or "").strip()
    # JIRA_PROJECT_KEY = (os.getenv("JIRA_PROJECT_KEY") or "KAN").strip().split()[0]

    JIRA_SERVER='https://johnyquest743.atlassian.net'
    JIRA_EMAIL='johnyquest743@gmail.com'
    # JIRA_API_TOKEN='ATATT3xFfGF08Nnq1F9L5_4X8ZhSvdG9YDMEUlwdQx5dLOv7Wc9H0D32ymCqMSE8k_CRD7ZdwfQOEBlpkYmC9qRCzuWI1j6TU-b7f-6sfZxaYM_kfCYEdYLtdxRaFDavJkiL1XX-PIEyac-GoXzHx0ZArDt1tEZ5OUcimCHD2NlCWhDuGi8uFxU=2B8E0873'
    JIRA_API_TOKEN='ATATT3xFfGF0cw6Z7MP8h2Z6o4YeYQJGhcjgnUfz5hP5mlcz4bpCR2u6Bpdvfafa2IupE52mh4QQzwsTnT4uJjwiBM72Sjvgd5SnsmofndmY0JcyRo-PXWdHjuGMVl4n7trMtdR82BnvhYNDe8xdtoCPMo4DG1xrqi0LEx2GcJ9bYN39UhfbfoI=22492296'
    JIRA_PROJECT_KEY='KAN'

    logger.debug("JIRA_SERVER: %s", "SET" if JIRA_SERVER else "MISSING")
    logger.debug("JIRA_EMAIL: %s", "SET" if JIRA_EMAIL else "MISSING")
    logger.debug("JIRA_API_TOKEN: %s", "SET (length=%s)" % (len(JIRA_API_TOKEN),) if JIRA_API_TOKEN else "MISSING")
    logger.debug("JIRA_PROJECT_KEY: %s", JIRA_PROJECT_KEY or "MISSING")

    # -----------------------------------------------------------------------
    # 2. Validate credentials (auth prerequisites)
    # -----------------------------------------------------------------------
    log_section("2. Validating credentials (auth prerequisites)")

    auth_issues = []

    # Server
    if not JIRA_SERVER:
        auth_issues.append("JIRA_SERVER is not set")
        logger.error("AUTH CHECK FAIL: JIRA_SERVER is missing")
    else:
        if not JIRA_SERVER.startswith("https://"):
            auth_issues.append("JIRA_SERVER must use https://")
            logger.error("AUTH CHECK FAIL: JIRA_SERVER should start with https://")
        if JIRA_SERVER.rstrip("/") != JIRA_SERVER:
            auth_issues.append("JIRA_SERVER should not end with /")
            logger.warning("AUTH CHECK WARN: JIRA_SERVER has trailing slash")
        logger.info("AUTH CHECK OK: JIRA_SERVER present and https")

    # Email
    if not JIRA_EMAIL:
        auth_issues.append("JIRA_EMAIL is not set")
        logger.error("AUTH CHECK FAIL: JIRA_EMAIL is missing")
    elif "@" not in JIRA_EMAIL:
        auth_issues.append("JIRA_EMAIL must be a valid email")
        logger.error("AUTH CHECK FAIL: JIRA_EMAIL does not look like an email")
    else:
        logger.info("AUTH CHECK OK: JIRA_EMAIL present")

    # API token
    if not JIRA_API_TOKEN:
        auth_issues.append("JIRA_API_TOKEN is not set")
        logger.error("AUTH CHECK FAIL: JIRA_API_TOKEN is missing")
    else:
        if len(JIRA_API_TOKEN) < 50:
            auth_issues.append("JIRA_API_TOKEN seems too short")
            logger.error("AUTH CHECK FAIL: JIRA_API_TOKEN length=%s (expected ~50+)", len(JIRA_API_TOKEN))
        if not JIRA_API_TOKEN.startswith("ATATT") and not JIRA_API_TOKEN.startswith("ATCTT"):
            logger.warning("AUTH CHECK WARN: JIRA_API_TOKEN usually starts with ATATT or ATCTT")
        logger.info("AUTH CHECK OK: JIRA_API_TOKEN present (length=%s)", len(JIRA_API_TOKEN))

    # Project key (needed for task creation, not for auth itself)
    if not JIRA_PROJECT_KEY:
        auth_issues.append("JIRA_PROJECT_KEY is not set")
        logger.error("AUTH CHECK FAIL: JIRA_PROJECT_KEY is missing")
    else:
        logger.info("AUTH CHECK OK: JIRA_PROJECT_KEY=%s", JIRA_PROJECT_KEY)

    if auth_issues:
        logger.error("Stopping: fix environment variables. Issues: %s", auth_issues)
        return 1

    # -----------------------------------------------------------------------
    # 3. Create JIRA client (first real auth attempt)
    # -----------------------------------------------------------------------
    log_section("3. Creating JIRA client (authentication attempt)")

    try:
        from jira import JIRA
        from jira.exceptions import JIRAError
    except ImportError as e:
        logger.error("AUTH SETUP FAIL: Missing dependency: %s", e)
        logger.info("Install with: pip install jira")
        return 1

    # Normalize server URL (no trailing path for API)
    server_url = JIRA_SERVER.rstrip("/")
    if "/" in server_url.replace("https://", "").replace("http://", ""):
        base = server_url.split("/")[0] + "//" + server_url.split("/")[2]
        server_url = base
        logger.debug("Normalized JIRA_SERVER to base URL: %s", server_url)

    logger.info("Connecting to: %s", server_url)
    logger.debug("Using basic_auth with email and API token")

    try:
        jira = JIRA(
            server=server_url,
            basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
            options={"verify": True},
        )
        logger.info("AUTH OK: JIRA client created successfully")
    except JIRAError as e:
        logger.error("AUTH FAIL: JIRA API error")
        logger.error("  status_code: %s", getattr(e, "status_code", "?"))
        logger.error("  text: %s", getattr(e, "text", str(e)))
        if getattr(e, "status_code", None) == 401:
            logger.error("  401 Unauthorized: wrong email or API token (or token revoked)")
            logger.info("  Fix: create new token at https://id.atlassian.com/manage-profile/security/api-tokens")
        elif getattr(e, "status_code", None) == 403:
            logger.error("  403 Forbidden: valid auth but insufficient permissions")
        elif getattr(e, "status_code", None) == 404:
            logger.error("  404: server URL may be wrong or resource not found")
        return 1
    except Exception as e:
        logger.error("AUTH FAIL: Connection/SSL or other error: %s", type(e).__name__)
        logger.error("  %s", str(e))
        logger.debug("Full traceback:", exc_info=True)
        return 1

    # -----------------------------------------------------------------------
    # 4. Verify auth with current user
    # -----------------------------------------------------------------------
    log_section("4. Verifying authentication (current user)")

    try:
        current_user = jira.current_user()
        logger.info("AUTH OK: Authenticated as: %s", current_user)
    except JIRAError as e:
        logger.error("AUTH VERIFY FAIL: current_user() failed")
        logger.error("  status_code: %s | text: %s", getattr(e, "status_code", "?"), getattr(e, "text", str(e)))
        return 1

    # -----------------------------------------------------------------------
    # 5. Optional: create a test task (proves write + project access)
    # -----------------------------------------------------------------------
    log_section("5. Test task creation (optional)")

    try:
        project = jira.project(JIRA_PROJECT_KEY)
        logger.info("Project '%s' accessible: %s", JIRA_PROJECT_KEY, getattr(project, "name", "OK"))
    except JIRAError as e:
        logger.error("Project access fail: %s - %s", getattr(e, "status_code", "?"), getattr(e, "text", str(e)))
        logger.info("Authentication succeeded but project '%s' not found or no access", JIRA_PROJECT_KEY)
        return 1

    try:
        issue = jira.create_issue(
            project=JIRA_PROJECT_KEY,
            summary="[Auth Test] Automated test ticket - safe to delete",
            description="Created by jira_auth_test.py to verify JIRA authentication and task creation.",
            issuetype={"name": "Task"},
        )
        logger.info("TASK CREATION OK: Issue created: %s", issue.key)
        logger.info("  URL: %s/browse/%s", server_url, issue.key)
    except JIRAError as e:
        logger.error("TASK CREATION FAIL: %s", getattr(e, "text", str(e)))
        logger.error("  status_code: %s", getattr(e, "status_code", "?"))
        if getattr(e, "status_code", None) == 403:
            logger.error("  403: User may not have permission to create issues in this project")
        return 1

    log_section("Result")
    logger.info("All authentication checks passed. JIRA is ready to use.")
    logger.info("Log file: %s", LOG_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
