import os
import sqlite3
import datetime
from datetime import timedelta
from dotenv import load_dotenv
from fetch_jira_data import fetch_issues

DB_NAME = "dashboard.db"

def get_status_at_date(issue, check_date):
    """
    Determine the status of an issue on a specific date.
    Simplified logic: 
    - If Created > Check Date: Does not exist yet.
    - If Resolved <= Check Date: 'Closed' (or actual resolution status).
    - Else: 'Open' (or actual current status if we tracked history accurately, 
      but for backfill we assume 'Open' if not resolved).
    """
    fields = issue.get('fields', {})
    created_str = fields.get('created')
    resolution_date_str = fields.get('resolutiondate')
    
    if not created_str:
        return None # Should not happen

    # Parse dates (Jira format: 2025-12-10T03:31:09.000+0000)
    # We only care about the date part for daily snapshots
    created_date = datetime.datetime.strptime(created_str.split('T')[0], "%Y-%m-%d").date()
    check_date_obj = check_date.date()
    
    if created_date > check_date_obj:
        return None # Issue didn't exist yet

    if resolution_date_str:
        res_date = datetime.datetime.strptime(resolution_date_str.split('T')[0], "%Y-%m-%d").date()
        if res_date <= check_date_obj:
            # It was resolved by this date.
            # Ideally we check status category, but simplified:
            return fields.get('status', {}).get('name', 'Closed')
    
    # If not resolved, or resolved AFTER check_date, it's considered OPEN on this date
    # Limitation: We don't know if it was "In Progress" or "To Do" historically without changelog.
    # We will use the CURRENT status if it's still open, or "Open" as a fallback.
    current_status = fields.get('status', {}).get('name', 'Open')
    
    # If currently closed, but was open on check_date, forced status needs care.
    # For simplification in backfill: "Open"
    return "Open"

def backfill():
    if not os.path.exists(DB_NAME):
        print("Database not found. Initializing...")
        import init_db
        init_db.init_db()

    load_dotenv()
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    
    # Override JQL to fetch broader history for backfill
    # Extract project key from env JQL if possible, or assume user configured it right.
    # We'll try to fetch ALL issues for the project to ensure we have full history.
    # user JQL: project = "THRPI" ...
    base_jql = os.getenv("JIRA_JQL_QUERY", "")
    project_part = base_jql.split("AND")[0].strip() # Very rough parsing
    
    # Robostness: specific JQL for backfill
    history_jql = f"{project_part}" # Just the project part, no time limit
    print(f"Backfilling using JQL: {history_jql}")
    
    issues = fetch_issues(jira_url, history_jql, email, api_token)
    if not issues:
        print("No issues found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Clear existing data to avoid duplicates during backfill experiment
    cursor.execute("DELETE FROM issues")
    cursor.execute("DELETE FROM snapshots")
    print("Cleared existing database data.")

    # Generate dates: Today - 180 days to Today, Weekly (every 7 days)
    end_date = datetime.datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Align to the start date
    current_date = start_date
    while current_date <= end_date:
        snapshot_timestamp = current_date.strftime("%Y-%m-%d 23:59:59")
        print(f"Processing Weekly Snapshot for: {current_date.strftime('%Y-%m-%d')}")
        
        daily_issues = []
        for issue in issues:
            simulated_status = get_status_at_date(issue, current_date)
            # filter out None status (didn't exist yet)
            if simulated_status:
                fields = issue.get('fields', {})
                key = issue.get('key')
                summary = fields.get('summary', '')
                priority = fields.get('priority', {}).get('name', 'None')
                assignee = fields.get('assignee')
                assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                created = fields.get('created')
                resolution_date = fields.get('resolutiondate')
                issuetype = fields.get('issuetype', {}).get('name', 'Unknown')
                components = fields.get('components', [])
                component_str = ", ".join([c.get('name') for c in components]) if components else ""
                
                daily_issues.append((
                    key, summary, simulated_status, priority, assignee_name,
                    created, resolution_date, issuetype, component_str
                ))

        # Save Snapshot
        cursor.execute("INSERT INTO snapshots (timestamp, total_issues, note) VALUES (?, ?, ?)", 
                       (snapshot_timestamp, len(daily_issues), "Weekly Backfill"))
        snapshot_id = cursor.lastrowid
        
        # Save Issues - Bulk insert is faster
        if daily_issues:
            cursor.executemany('''
                INSERT INTO issues (
                    snapshot_id, key, summary, status, priority, 
                    assignee, created_date, resolution_date, type, component
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [(snapshot_id,) + di for di in daily_issues])
            
        current_date += timedelta(weeks=1)

    conn.commit()
    conn.close()
    print("Backfill complete.")

if __name__ == "__main__":
    backfill()
