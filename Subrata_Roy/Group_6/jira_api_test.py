"""
JIRA Integration Script with Detailed Logging
This script connects to JIRA and creates a test task with comprehensive logging.
"""

import os
import sys
import logging
from datetime import datetime
from jira import JIRA
from jira.exceptions import JIRAError
from dotenv import load_dotenv

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
log_filename = f"logs/jira_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================================

logger.info("=" * 70)
logger.info("JIRA Integration Script Started")
logger.info("=" * 70)

logger.info("Step 1: Loading environment variables from .env file")
load_dotenv()

# Get environment variables
JIRA_SERVER = os.getenv('JIRA_SERVER')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')

# ============================================================================
# VALIDATE ENVIRONMENT VARIABLES
# ============================================================================

logger.info("Step 2: Validating environment variables")

def validate_env_variables():
    """Validate all required environment variables are set"""
    errors = []
    
    # Check JIRA_SERVER
    logger.debug(f"Checking JIRA_SERVER...")
    if not JIRA_SERVER:
        errors.append("❌ JIRA_SERVER is not set")
        logger.error("JIRA_SERVER is missing!")
    else:
        logger.info(f"✅ JIRA_SERVER: {JIRA_SERVER}")
        
        # Validate format
        if not JIRA_SERVER.startswith('https://'):
            errors.append("❌ JIRA_SERVER must start with 'https://'")
            logger.error(f"JIRA_SERVER has wrong format: {JIRA_SERVER}")
        if JIRA_SERVER.endswith('/'):
            errors.append("⚠️  JIRA_SERVER should not end with '/'")
            logger.warning(f"JIRA_SERVER ends with '/': {JIRA_SERVER}")
    
    # Check JIRA_EMAIL
    logger.debug(f"Checking JIRA_EMAIL...")
    if not JIRA_EMAIL:
        errors.append("❌ JIRA_EMAIL is not set")
        logger.error("JIRA_EMAIL is missing!")
    else:
        logger.info(f"✅ JIRA_EMAIL: {JIRA_EMAIL}")
        
        # Validate format
        if '@' not in JIRA_EMAIL:
            errors.append("❌ JIRA_EMAIL must be a valid email address")
            logger.error(f"JIRA_EMAIL is not valid: {JIRA_EMAIL}")
    
    # Check JIRA_API_TOKEN
    logger.debug(f"Checking JIRA_API_TOKEN...")
    if not JIRA_API_TOKEN:
        errors.append("❌ JIRA_API_TOKEN is not set")
        logger.error("JIRA_API_TOKEN is missing!")
    else:
        # Don't log the full token for security
        token_preview = f"{JIRA_API_TOKEN[:10]}...{JIRA_API_TOKEN[-10:]}"
        logger.info(f"✅ JIRA_API_TOKEN: {token_preview} (length: {len(JIRA_API_TOKEN)})")
        
        # Validate format
        if not JIRA_API_TOKEN.startswith('ATATT'):
            errors.append("⚠️  JIRA_API_TOKEN should start with 'ATATT'")
            logger.warning(f"JIRA_API_TOKEN doesn't start with ATATT: {JIRA_API_TOKEN[:10]}...")
        if len(JIRA_API_TOKEN) < 50:
            errors.append("❌ JIRA_API_TOKEN seems too short")
            logger.error(f"JIRA_API_TOKEN is only {len(JIRA_API_TOKEN)} characters")
    
    # Check JIRA_PROJECT_KEY
    logger.debug(f"Checking JIRA_PROJECT_KEY...")
    if not JIRA_PROJECT_KEY:
        errors.append("❌ JIRA_PROJECT_KEY is not set")
        logger.error("JIRA_PROJECT_KEY is missing!")
    else:
        logger.info(f"✅ JIRA_PROJECT_KEY: {JIRA_PROJECT_KEY}")
        
        # Validate format
        if not JIRA_PROJECT_KEY.isupper():
            errors.append("⚠️  JIRA_PROJECT_KEY should be uppercase")
            logger.warning(f"JIRA_PROJECT_KEY is not uppercase: {JIRA_PROJECT_KEY}")
        if ' ' in JIRA_PROJECT_KEY:
            errors.append("❌ JIRA_PROJECT_KEY should not contain spaces")
            logger.error(f"JIRA_PROJECT_KEY contains spaces: {JIRA_PROJECT_KEY}")
    
    return errors

# Validate
validation_errors = validate_env_variables()

if validation_errors:
    logger.error("\n" + "=" * 70)
    logger.error("VALIDATION FAILED - Found the following issues:")
    logger.error("=" * 70)
    for error in validation_errors:
        logger.error(error)
    logger.error("=" * 70)
    logger.error("Please fix these issues in your .env file and try again.")
    sys.exit(1)
else:
    logger.info("\n✅ All environment variables validated successfully!\n")

# ============================================================================
# CONNECT TO JIRA
# ============================================================================

logger.info("Step 3: Connecting to JIRA")

try:
    logger.debug(f"Creating JIRA connection to {JIRA_SERVER}")
    logger.debug(f"Using email: {JIRA_EMAIL}")
    logger.debug(f"Using token: {JIRA_API_TOKEN[:10]}...{JIRA_API_TOKEN[-10:]}")
    
    jira = JIRA(
        server=JIRA_SERVER,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        options={'verify': True}  # Verify SSL certificates
    )
    
    logger.info("✅ Successfully created JIRA client object")
    
except Exception as e:
    logger.error(f"❌ Failed to create JIRA client: {type(e).__name__}")
    logger.error(f"Error details: {str(e)}")
    logger.debug("Full traceback:", exc_info=True)
    sys.exit(1)

# ============================================================================
# TEST CONNECTION
# ============================================================================

logger.info("Step 4: Testing JIRA connection")

try:
    # Get server info
    logger.debug("Fetching server info...")
    server_info = jira.server_info()
    
    logger.info("✅ Connection successful!")
    logger.info(f"   Server URL: {server_info.get('baseUrl', 'N/A')}")
    logger.info(f"   Server Version: {server_info.get('version', 'N/A')}")
    logger.info(f"   Build Number: {server_info.get('buildNumber', 'N/A')}")
    
    # Get current user
    logger.debug("Fetching current user info...")
    current_user = jira.current_user()
    logger.info(f"   Authenticated as: {current_user}")
    
except JIRAError as e:
    logger.error(f"❌ JIRA API Error: {e.status_code}")
    logger.error(f"   Error message: {e.text}")
    
    if e.status_code == 401:
        logger.error("\n🔑 AUTHENTICATION FAILED!")
        logger.error("   Possible causes:")
        logger.error("   1. Invalid API token")
        logger.error("   2. Wrong email address")
        logger.error("   3. Token has been revoked")
        logger.error("\n   Solutions:")
        logger.error("   1. Generate a new API token at:")
        logger.error("      https://id.atlassian.com/manage-profile/security/api-tokens")
        logger.error("   2. Verify your email is correct")
    elif e.status_code == 404:
        logger.error("\n🔍 SERVER NOT FOUND!")
        logger.error("   Possible causes:")
        logger.error("   1. Wrong JIRA_SERVER URL")
        logger.error("   2. Typo in the domain name")
        logger.error("\n   Solutions:")
        logger.error("   1. Check your JIRA_SERVER URL")
        logger.error("   2. Make sure it's: https://yoursite.atlassian.net")
    
    logger.debug("Full error details:", exc_info=True)
    sys.exit(1)
    
except Exception as e:
    logger.error(f"❌ Unexpected error: {type(e).__name__}")
    logger.error(f"   Error message: {str(e)}")
    logger.debug("Full traceback:", exc_info=True)
    sys.exit(1)

# ============================================================================
# LIST AVAILABLE PROJECTS
# ============================================================================

logger.info("\nStep 5: Listing available projects")

try:
    logger.debug("Fetching all projects...")
    projects = jira.projects()
    
    logger.info(f"✅ Found {len(projects)} project(s):")
    for project in projects:
        logger.info(f"   📁 {project.key}: {project.name}")
        logger.debug(f"      ID: {project.id}")
        logger.debug(f"      Lead: {getattr(project, 'lead', 'N/A')}")
    
    # Check if our project exists
    project_keys = [p.key for p in projects]
    if JIRA_PROJECT_KEY in project_keys:
        logger.info(f"\n✅ Target project '{JIRA_PROJECT_KEY}' found!")
    else:
        logger.error(f"\n❌ Target project '{JIRA_PROJECT_KEY}' NOT found!")
        logger.error(f"   Available projects: {', '.join(project_keys)}")
        logger.error(f"\n   Please update JIRA_PROJECT_KEY in .env to one of:")
        for key in project_keys:
            logger.error(f"   - {key}")
        sys.exit(1)
    
except JIRAError as e:
    logger.error(f"❌ Failed to list projects: {e.text}")
    logger.debug("Full error:", exc_info=True)
    sys.exit(1)

# ============================================================================
# GET PROJECT DETAILS
# ============================================================================

logger.info(f"\nStep 6: Getting details for project '{JIRA_PROJECT_KEY}'")

try:
    logger.debug(f"Fetching project: {JIRA_PROJECT_KEY}")
    project = jira.project(JIRA_PROJECT_KEY)
    
    logger.info(f"✅ Project Details:")
    logger.info(f"   Name: {project.name}")
    logger.info(f"   Key: {project.key}")
    logger.info(f"   ID: {project.id}")
    
    # Get issue types for this project
    logger.debug("Fetching available issue types...")
    issue_types = jira.issue_types_for_project(project.id)
    
    logger.info(f"\n   Available Issue Types:")
    for issue_type in issue_types:
        logger.info(f"   - {issue_type.name} (ID: {issue_type.id})")
    
except JIRAError as e:
    logger.error(f"❌ Failed to get project details: {e.text}")
    logger.debug("Full error:", exc_info=True)
    sys.exit(1)

# ============================================================================
# CREATE JIRA TASK
# ============================================================================

logger.info(f"\nStep 7: Creating JIRA task in project '{JIRA_PROJECT_KEY}'")

# Prepare task data
task_summary = "TEST: DevOps Incident Bot Integration"
task_description = f"""This is a test task created by the DevOps Incident Bot.

*Test Information:*
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Purpose: Verify JIRA API integration
- Status: Test successful ✅

*Integration Details:*
- Python JIRA library working correctly
- Authentication successful
- API token valid
- Project access confirmed

*Next Steps:*
You can safely delete this test task or use it to verify:
1. Task creation works
2. Descriptions are formatted correctly
3. API integration is functional

---
_This task was created automatically by the DevOps Incident Analysis Suite._
"""

logger.debug("Task details:")
logger.debug(f"  Summary: {task_summary}")
logger.debug(f"  Description: {task_description[:100]}...")
logger.debug(f"  Project: {JIRA_PROJECT_KEY}")
logger.debug(f"  Issue Type: Task")

try:
    # Create issue dictionary
    issue_dict = {
        'project': {'key': JIRA_PROJECT_KEY},
        'summary': task_summary,
        'description': task_description,
        'issuetype': {'name': 'Task'},  # Try 'Task' first
    }
    
    logger.debug("Attempting to create issue...")
    logger.debug(f"Issue dict: {issue_dict}")
    
    new_issue = jira.create_issue(fields=issue_dict)
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ SUCCESS! JIRA Task Created Successfully!")
    logger.info("=" * 70)
    logger.info(f"   Task Key: {new_issue.key}")
    logger.info(f"   Task ID: {new_issue.id}")
    logger.info(f"   URL: {JIRA_SERVER}/browse/{new_issue.key}")
    logger.info("=" * 70)
    
    # Get full issue details
    logger.debug("\nFetching full issue details...")
    issue = jira.issue(new_issue.key)
    logger.info(f"\n   Full Issue Details:")
    logger.info(f"   - Status: {issue.fields.status.name}")
    logger.info(f"   - Reporter: {issue.fields.reporter.displayName}")
    logger.info(f"   - Created: {issue.fields.created}")
    
except JIRAError as e:
    logger.error(f"\n❌ Failed to create task!")
    logger.error(f"   Status Code: {e.status_code}")
    logger.error(f"   Error Message: {e.text}")
    
    if "issuetype" in str(e.text).lower():
        logger.error("\n   Issue Type Error!")
        logger.error("   The issue type 'Task' might not be available.")
        logger.error("   Try one of these instead:")
        for issue_type in issue_types:
            logger.error(f"   - {issue_type.name}")
        logger.error("\n   Change 'Task' to one of the above in the code.")
    
    logger.debug("\nFull error details:", exc_info=True)
    sys.exit(1)

except Exception as e:
    logger.error(f"\n❌ Unexpected error creating task: {type(e).__name__}")
    logger.error(f"   Error: {str(e)}")
    logger.debug("Full traceback:", exc_info=True)
    sys.exit(1)

# ============================================================================
# ADD COMMENT TO TASK
# ============================================================================

logger.info("\nStep 8: Adding comment to the task")

try:
    comment_text = """✅ Integration Test Complete

This comment was added automatically to verify comment functionality.

All features working:
- Task creation ✅
- Comment addition ✅
- API integration ✅
"""
    
    logger.debug(f"Adding comment to {new_issue.key}")
    jira.add_comment(new_issue.key, comment_text)
    logger.info(f"✅ Comment added successfully to {new_issue.key}")
    
except JIRAError as e:
    logger.error(f"❌ Failed to add comment: {e.text}")
    logger.debug("Full error:", exc_info=True)

# ============================================================================
# SUMMARY
# ============================================================================

logger.info("\n" + "=" * 70)
logger.info("🎉 JIRA INTEGRATION TEST COMPLETED SUCCESSFULLY!")
logger.info("=" * 70)
logger.info(f"\n📊 Summary:")
logger.info(f"   ✅ Connected to: {JIRA_SERVER}")
logger.info(f"   ✅ Authenticated as: {JIRA_EMAIL}")
logger.info(f"   ✅ Accessed project: {JIRA_PROJECT_KEY}")
logger.info(f"   ✅ Created task: {new_issue.key}")
logger.info(f"   ✅ Added comment to task")
logger.info(f"\n🔗 View your task at:")
logger.info(f"   {JIRA_SERVER}/browse/{new_issue.key}")
logger.info(f"\n📝 Log file saved to: {log_filename}")
logger.info("\n" + "=" * 70)