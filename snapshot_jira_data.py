import os
import sqlite3
import datetime
from dotenv import load_dotenv
from fetch_jira_data import fetch_issues
from llm_service import llm_service

# Database configuration
DB_NAME = "dashboard.db"

def save_snapshot(issues):
    # 1. Prepare data first (heavy lifting, especially LLM calls)
    campaign_data_partial = []
    print(f"Processing {len(issues)} issues for snapshot...")
    
    for issue in issues:
        fields = issue.get('fields', {})
        
        key = issue.get('key')
        summary = fields.get('summary', '')
        status = fields.get('status', {}).get('name', 'Unknown')
        priority = fields.get('priority', {}).get('name', 'None')
        
        assignee = fields.get('assignee')
        assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
        
        created = fields.get('created')
        resolution_date = fields.get('resolutiondate') # Note: Jira field is 'resolutiondate' usually
        
        issuetype = fields.get('issuetype', {}).get('name', 'Unknown')
        
        reporter = fields.get('reporter')
        reporter_name = reporter.get('displayName', 'Unknown') if reporter else 'Unknown'
        
        updated = fields.get('updated')
        
        # Handle labels (list of strings)
        labels = fields.get('labels', [])
        labels_str = ", ".join(labels) if labels else ""
        
        # Handle components (can be multiple, join with comma)
        components = fields.get('components', [])
        component_str = ", ".join([c.get('name') for c in components]) if components else ""

        # Handle latest comment
        comments = fields.get('comment', {}).get('comments', [])
        latest_comment_body = ""
        if comments:
            latest_comment_body = comments[-1].get('body', '')

        # Handle LLM Summary
        # Disabled for snapshot performance (to prevent timeouts on Refresh Data)
        # LLM summaries are generated on-demand for the Weekly Report.
        llm_summary = ""
        # if comments:
        #     llm_summary = llm_service.summarize_comments(key, summary, comments)
        # else:
        #     llm_summary = ""

        # Store tuple without snapshot_id for now
        campaign_data_partial.append((
            key, summary, status, priority, 
            assignee_name, created, resolution_date, issuetype, component_str,
            reporter_name, updated, labels_str, latest_comment_body, llm_summary
        ))

    # 2. Database operations (Short transaction)
    conn = sqlite3.connect(DB_NAME, timeout=30.0) # Increase timeout just in case
    cursor = conn.cursor()

    try:
        # Create a new snapshot record
        total_count = len(issues)
        cursor.execute('''
            INSERT INTO snapshots (total_issues) VALUES (?)
        ''', (total_count,))
        snapshot_id = cursor.lastrowid
        print(f"Created Snapshot ID: {snapshot_id} (Issues: {total_count})")

        # Add snapshot_id to data
        campaign_data = []
        for row in campaign_data_partial:
            # Preprend snapshot_id to the tuple
            campaign_data.append((snapshot_id,) + row)

        cursor.executemany('''
            INSERT INTO issues (
                snapshot_id, key, summary, status, priority, 
                assignee, created_date, resolution_date, type, component,
                reporter, updated_date, labels, latest_comment, llm_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', campaign_data)

        conn.commit()
        print("Snapshot data saved successfully.")
    except Exception as e:
        print(f"Error saving snapshot to DB: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    # Ensure DB exists
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found. Please run init_db.py first.")
        return

    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    jql_query = os.getenv("JIRA_JQL_QUERY")
    
    if not all([jira_url, email, api_token, jql_query]):
        print("Error: Missing environment variables.")
        return

    print("Fetching latest data from Jira...")
    # Reuse the fetch logic from our existing script
    issues = fetch_issues(jira_url, jql_query, email, api_token)
    
    if issues:
        save_snapshot(issues)
    else:
        print("No issues found to snapshot.")

if __name__ == "__main__":
    main()
