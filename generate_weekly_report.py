import sqlite3
import datetime
import os
from dotenv import load_dotenv
from collections import Counter

# Path configuration
DB_NAME = "dashboard.db"
load_dotenv()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_weekly_report(return_content=False):
    """Generate a weekly report.
    
    Args:
        return_content: If True, return the report content as a string instead of writing to file.
    
    Returns:
        If return_content is True, returns a dict with 'content' and 'filename'.
        Otherwise returns None after writing to file.
    """
    print("Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Get latest snapshot
    cursor.execute("SELECT snapshot_id, timestamp FROM snapshots ORDER BY timestamp DESC LIMIT 1")
    snapshot = cursor.fetchone()
    if not snapshot:
        print("No snapshots found in database.")
        if return_content:
            return {"error": "No snapshots found in database."}
        return
    
    sid = snapshot['snapshot_id']
    snap_time = snapshot['timestamp']
    print(f"Using latest snapshot ID: {sid} (Created at: {snap_time})")
    
    # 2. Calculate date 7 days ago
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    # Jira date format: 2026-01-05T06:46:06.000+0000
    date_threshold = seven_days_ago.strftime("%Y-%m-%dT%H:%M:%S")

    # 3. Query Updated Issues (Open/In Progress/New)
    print(f"Querying issues updated since {seven_days_ago.strftime('%Y-%m-%d')}...")
    query = """
        SELECT key, summary, status, priority, assignee, reporter, updated_date, created_date, labels, latest_comment, llm_summary
        FROM issues
        WHERE snapshot_id = ?
        AND status IN ('New', 'Open', 'In Progress')
        AND updated_date >= ?
        ORDER BY 
          CASE priority 
            WHEN 'Critical' THEN 1 
            WHEN 'Blocker' THEN 1 
            WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 
            WHEN 'Low' THEN 4 
            ELSE 5 
          END ASC,
          updated_date DESC
    """
    cursor.execute(query, (sid, date_threshold))
    updated_issues = [dict(row) for row in cursor.fetchall()]

    # 4. Query Newly Created Issues (regardless of status if needed, but sticking to user request)
    # User asked for Open/In-progress/New.
    # Most newly created issues will be "New" anyway.
    newly_created = [i for i in updated_issues if i['created_date'] >= date_threshold]

    # Generate MD
    date_str = now.strftime("%Y-%m-%d")
    report_filename = f"weekly_report_{date_str}.md"
    
    jira_url = os.getenv("JIRA_URL", "")

    print(f"Generating report: {report_filename} with {len(updated_issues)} issues...")

    # Build report content
    lines = []
    lines.append(f"# Weekly Jira Update Report - {date_str}\n")
    lines.append(f"> [!NOTE]")
    lines.append(f"> This report includes issues in **New**, **Open**, or **In Progress** status that have been updated in the last 7 days.\n")
    
    lines.append(f"## Summary")
    lines.append(f"- **Reporting Period**: `{seven_days_ago.strftime('%Y-%m-%d')}` to `{date_str}`")
    lines.append(f"- **Snapshot Used**: `{sid}` ({snap_time})")
    lines.append(f"- **Total Active Issues Updated**: {len(updated_issues)}")
    lines.append(f"- **Newly Created in Period**: {len(newly_created)}\n")

    # Status distribution of updated issues
    status_counts = Counter(i['status'] for i in updated_issues)
    lines.append("### Status Distribution")
    lines.append("| Status | Count |")
    lines.append("|---|---|")
    for status in ['New', 'Open', 'In Progress']:
        if status_counts[status] > 0:
            lines.append(f"| **{status}** | {status_counts[status]} |")
    lines.append("\n---\n")

    lines.append("## Detailed Issue List\n")
    if updated_issues:
        lines.append("| Key | Priority | Status | Summary | Latest Update / Comment | Assignee |")
        lines.append("|---|---|---|---|---|---|")
        for issue in updated_issues:
            key = issue['key']
            link = f"{jira_url}/browse/{key}" if jira_url else key
            summary = issue['summary'].replace("|", "\\|")
            
            # Format comment/summary
            latest_comment = issue['latest_comment'] or ""
            llm_summary = issue['llm_summary'] or "*(No summary available)*"

            # Clean up LLM summary for table (Markdown tables require no real newlines)
            llm_summary_display = llm_summary.replace("\n", "<br>")
            
            # Clean up latest comment preview
            latest_comment_preview = latest_comment.replace("\n", " ").replace("\r", "")
            if len(latest_comment_preview) > 100:
                latest_comment_preview = latest_comment_preview[:97] + "..."
            
            assignee = issue['assignee'] or "Unassigned"
            updated_at = issue['updated_date'][:16].replace('T', ' ')
            
            summary_display = f"**{summary}**"
            
            # Combine LLM Summary and Latest Comment with clear labels
            comment_display = f"**AI Analytical Summary:**<br>{llm_summary_display}<br><br>**Latest Team Update:**<br>_{latest_comment_preview or 'N/A'}_"

            # Highlight critical/blocker
            priority = issue['priority']
            if priority in ['Critical', 'Blocker']:
                priority = f"🔥 **{priority}**"
            
            lines.append(f"| [{key}]({link}) | {priority} | {issue['status']} | {summary_display} | {comment_display} <br><small>Updated: {updated_at}</small> | {assignee} |")
    else:
        lines.append("*No issues matching the criteria were updated in the last 7 days.*")

    lines.append("\n\n---")
    lines.append("*Report generated by Jira Dashboard API Tool*")

    report_content = "\n".join(lines)
    conn.close()

    if return_content:
        return {"content": report_content, "filename": report_filename, "issue_count": len(updated_issues)}
    
    # Write to file
    with open(report_filename, "w", encoding='utf-8') as f:
        f.write(report_content)

    print(f"Successfully created {report_filename}")

if __name__ == "__main__":
    generate_weekly_report()
