import sqlite3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to allow importing fetch_jira_data if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import snapshot logic from root script (as a module)
try:
    import snapshot_jira_data
    import fetch_jira_data
except ImportError:
    # Fallback or handling if run from different context
    pass

DB_NAME = "dashboard.db"

def get_db_connection():
    # DB is in the root directory relative to backend/
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_NAME)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_history(label_filter=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get snapshots sorted by date
    cursor.execute("SELECT snapshot_id, timestamp FROM snapshots ORDER BY timestamp ASC")
    snapshots = cursor.fetchall()

    # Sort snapshots by timestamp just in case
    snapshots.sort(key=lambda x: x['timestamp'])

    history = []
    last_date = None
    
    # Identify the very last available snapshot ID to ensure it's included
    latest_sid = snapshots[-1]['snapshot_id'] if snapshots else None

    for i, snap in enumerate(snapshots):
        sid = snap['snapshot_id']
        ts_str = snap['timestamp']
        date_full = ts_str.split(' ')[0]
        
        # Filter logic to handle weekly cadence AND ensure latest included
        should_include = False
        is_same_day = (last_date == date_full)

        if is_same_day:
            # If same day, we want to replace the previous entry with this later one
            should_include = True
        elif not last_date:
             # First entry
             should_include = True
        elif sid == latest_sid:
             # Always include the absolute latest (if not same day as last, it's a new day)
             should_include = True
        else:
             # Regular weekly cadence check
            d1 = datetime.strptime(last_date, "%Y-%m-%d")
            d2 = datetime.strptime(date_full, "%Y-%m-%d")
            if (d2 - d1).days >= 7:
                should_include = True
        
        if not should_include:
            continue

        # If same day, remove the previous one to replace it
        if is_same_day:
            history.pop()

        # Construct label clause
        label_clause = f" AND labels LIKE '%{label_filter}%' " if label_filter else ""

        # 1. Open Bugs (Explicit Statuses)
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND type='Bug'{label_clause}", (sid,))
        open_count = cursor.fetchone()[0]
        
        # 2. Critical & High (Explicit Statuses)
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND priority IN ('Critical', 'Blocker') AND type='Bug'{label_clause}", (sid,))
        critical = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND priority = 'High' AND type='Bug'{label_clause}", (sid,))
        high = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND priority = 'Medium' AND type='Bug'{label_clause}", (sid,))
        medium = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND priority = 'Low' AND type='Bug'{label_clause}", (sid,))
        low = cursor.fetchone()[0]

        # 3. Velocity (Weekly)
        cursor.execute("SELECT date(?, '-6 days')", (date_full,))
        week_start = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND date(substr(created_date,1,10)) BETWEEN ? AND ? AND type='Bug'{label_clause}", (sid, week_start, date_full))
        new_count = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND date(substr(resolution_date,1,10)) BETWEEN ? AND ? AND type='Bug'{label_clause}", (sid, week_start, date_full))
        fixed_count = cursor.fetchone()[0]

        history.append({
            "date": date_full,
            "open": open_count,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "new_bugs": new_count,
            "fixed_bugs": fixed_count
        })
        
        last_date = date_full

    conn.close()
    return history

def get_breakdown(label_filter=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use the absolute latest snapshot for the "Current" view
    cursor.execute("SELECT snapshot_id FROM snapshots ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"priority": [], "status": []}
    
    sid = row[0]

    # Construct label clause
    label_clause = f" AND labels LIKE '%{label_filter}%' " if label_filter else ""
    
    # Priority
    cursor.execute(f"SELECT priority, COUNT(*) as count FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND type='Bug'{label_clause} GROUP BY priority", (sid,))
    priority_data = [{"name": r['priority'], "value": r['count']} for r in cursor.fetchall()]
    
    # Status
    cursor.execute(f"SELECT status, COUNT(*) as count FROM issues WHERE snapshot_id=? AND status IN ('New', 'Open', 'In Progress') AND type='Bug'{label_clause} GROUP BY status", (sid,))
    status_data = [{"name": r['status'], "value": r['count']} for r in cursor.fetchall()]

    conn.close()
    return {"priority": priority_data, "status": status_data}

def trigger_snapshot():
    # Reuse the logic from snapshot_jira_data.py
    # We need to load env vars here as well
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    jql = os.getenv("JIRA_JQL_QUERY")
    
    if not all([jira_url, email, api_token, jql]):
        return {"error": "Missing configuration in .env"}

    # Fetch
    issues = fetch_jira_data.fetch_issues(jira_url, jql, email, api_token)
    
    # Save (using the imported module's save function if available, or direct logic)
    # Since snapshot_jira_data.py has the save_snapshot function, we can use it.
    snapshot_jira_data.save_snapshot(issues)
    
    return {"status": "success", "count": len(issues)}

def get_bugs_list(label_filter=None, include_closed=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use the absolute latest snapshot for the "Current" view
    cursor.execute("SELECT snapshot_id FROM snapshots ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return []
    
    sid = row[0]
    
    label_clause = f" AND labels LIKE '%{label_filter}%' " if label_filter else ""
    
    status_clause = " AND status IN ('New', 'Open', 'In Progress') " if not include_closed else ""

    # 2. Query details for this snapshot
    query = f"""
        SELECT key, summary, priority, status, assignee, created_date, reporter, updated_date, labels
        FROM issues 
        WHERE snapshot_id=? 
          AND type='Bug' 
          {status_clause}
          {label_clause}
        ORDER BY 
          CASE priority 
            WHEN 'Critical' THEN 1 
            WHEN 'Blocker' THEN 1 
            WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 
            WHEN 'Low' THEN 4 
            ELSE 5 
          END ASC, 
          CASE status
            WHEN 'New' THEN 1
            WHEN 'Open' THEN 2
            WHEN 'In Progress' THEN 3
            WHEN 'Ready for Test' THEN 4
            WHEN 'In Test' THEN 5
            WHEN 'Resolved' THEN 6
            WHEN 'Closed' THEN 7
            WHEN 'Done' THEN 8
            ELSE 9
          END ASC
    """
    cursor.execute(query, (sid,))
    rows = cursor.fetchall()
    
    bugs = []
    
    # Reload env to ensure JIRA_URL is available
    if not os.getenv("JIRA_URL"):
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    jira_base = os.getenv("JIRA_URL", "")

    for r in rows:
        # Check if reporter/updated/labels are columns (handle transition)
        try:
            reporter = r['reporter']
        except IndexError:
            reporter = 'N/A'
            
        try:
            updated = r['updated_date']
        except IndexError:
            updated = 'N/A'
            
        try:
            labels = r['labels']
        except IndexError:
            labels = ''
            
        key = r['key']
        link = f"{jira_base}/browse/{key}" if jira_base else ""

        bugs.append({
            "key": key,
            "summary": r['summary'],
            "priority": r['priority'],
            "status": r['status'],
            "assignee": r['assignee'],
            "created": r['created_date'],
            "reporter": reporter,
            "updated": updated,
            "labels": labels,
            "link": link
        })
        
    conn.close()
    return bugs
