from jira import JIRA

# Jira server details and authentication
JIRA_SERVER = 'https://your-jira-instance-url.atlassian.net'
API_TOKEN = '<YOUR-PERSONAL-ACCESS-TOKEN>'  # Use a PAT for better security
USER_EMAIL = '<YOUR-EMAIL>' # Email associated with the PAT

# Connect to Jira using the email and API token
jira = JIRA(JIRA_SERVER, basic_auth=(USER_EMAIL, API_TOKEN))

# Define the fields for the new issue
issue_dict = {
    'project': {'key': '<YOUR_PROJECT_KEY>'},
    'summary': 'New issue from jira-python script',
    'description': 'Look into this one; the issue was created via the Python API.',
    'issuetype': {'name': 'Task'},  # Can be 'Bug', 'Story', 'Epic', etc.
}

try:
    # Create the issue
    new_issue = jira.create_issue(fields=issue_dict)
    print(f"✅ Jira issue created successfully! Issue key: {new_issue.key}")
    print(f"View issue at: {JIRA_SERVER}/browse/{new_issue.key}")

except Exception as e:
    print(f"An error occurred: {e}")
    # Print the response text from the API for detailed errors
    if hasattr(e, 'response'):
        print(e.response.text)

