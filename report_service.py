"""
Real-time report generation service.
Fetches Jira issues and generates LLM summaries on-demand.
"""
import os
import datetime
import json
from dotenv import load_dotenv
from collections import Counter
from fetch_jira_data import fetch_issues, get_jira_headers
from llm_service import llm_service

load_dotenv()

def generate_realtime_report(progress_callback=None, provider=None):
    """
    Generate a weekly report in real-time by fetching Jira and calling LLM.
    
    Args:
        progress_callback: Optional function(current, total, status, issue_key) for progress updates
        provider: Optional LLM provider override ('openai', 'cambrian', etc.)
    
    Yields:
        Progress updates as dict, final yield is the complete report
    """
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    
    # Calculate date 7 days ago
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    date_str = now.strftime("%Y-%m-%d")
    start_date = seven_days_ago.strftime("%Y-%m-%d")
    
    # Build JQL for all open issues (no date filter)
    jql = f'project = "THRPI" AND status IN ("New", "Open", "In Progress")'
    
    yield {"type": "progress", "current": 0, "total": 0, "status": "Fetching issues from Jira...", "issue_key": None}
    
    # Fetch issues from Jira
    issues = fetch_issues(jira_url, jql, email, api_token)
    total_issues = len(issues)
    
    if total_issues == 0:
        yield {"type": "progress", "current": 0, "total": 0, "status": "No issues found", "issue_key": None}
        yield {"type": "complete", "content": "# Weekly Report\n\nNo issues found for the last 7 days.", "filename": f"weekly_report_{date_str}.md"}
        return
    
    yield {"type": "progress", "current": 0, "total": total_issues, "status": f"Found {total_issues} issues. Starting LLM analysis...", "issue_key": None}
    
    # Process each issue
    processed_issues = []
    for idx, issue in enumerate(issues):
        fields = issue.get('fields', {})
        key = issue.get('key')
        summary = fields.get('summary', '')
        status = fields.get('status', {}).get('name', 'Unknown')
        priority = fields.get('priority', {}).get('name', 'None')
        assignee = fields.get('assignee', {})
        assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
        updated = fields.get('updated', '')
        
        # Get comments
        comments = fields.get('comment', {}).get('comments', [])
        
        yield {"type": "progress", "current": idx + 1, "total": total_issues, "status": f"Analyzing {key}...", "issue_key": key}
        
        # Generate LLM summary
        llm_summary = llm_service.summarize_comments(key, summary, comments, provider=provider)
        
        # Get latest comment
        latest_comment = comments[-1].get('body', '') if comments else ""
        
        # Check if updated recently
        is_stale = False
        if updated:
            try:
                updated_date = datetime.datetime.strptime(updated[:10], "%Y-%m-%d")
                if updated_date < seven_days_ago:
                    is_stale = True
            except:
                pass
        
        processed_issues.append({
            "key": key,
            "summary": summary,
            "status": status,
            "priority": priority,
            "assignee": assignee_name,
            "updated": updated,
            "llm_summary": llm_summary,
            "latest_comment": latest_comment,
            "is_stale": is_stale
        })
    
    yield {"type": "progress", "current": total_issues, "total": total_issues, "status": "Generating report...", "issue_key": None}
    
    # Sort by priority (Critical/Blocker first)
    priority_order = {
        'Critical': 1,
        'Blocker': 1,
        'High': 2,
        'Medium': 3,
        'Low': 4,
        'None': 5,
        'Undecided': 5
    }
    processed_issues.sort(key=lambda x: priority_order.get(x['priority'], 5))
    
    # Build report
    report_content = build_report_markdown(processed_issues, date_str, start_date, jira_url)
    
    yield {"type": "complete", "content": report_content, "filename": f"weekly_report_{date_str}.md", "issue_count": total_issues}


def build_report_markdown(issues, date_str, start_date, jira_url):
    """Build the markdown report from processed issues."""
    lines = []
    lines.append(f"# Weekly Jira Update Report - {date_str}\n")
    lines.append(f"> [!NOTE]")
    lines.append(f"> This report includes issues in **New**, **Open**, or **In Progress** status that have been updated in the last 7 days.\n")
    
    lines.append(f"## Summary")
    lines.append(f"- **Reporting Period**: `{start_date}` to `{date_str}`")
    lines.append(f"- **Total Active Issues Updated**: {len(issues)}\n")

    # Status distribution
    status_counts = Counter(i['status'] for i in issues)
    lines.append("### Status Distribution")
    lines.append("| Status | Count |")
    lines.append("|---|---|")
    for status in ['New', 'Open', 'In Progress']:
        if status_counts[status] > 0:
            lines.append(f"| **{status}** | {status_counts[status]} |")
    lines.append("\n---\n")

    lines.append("## Detailed Issue List\n")
    if issues:
        lines.append("| Key | Priority | Status | Summary | Latest Update / Comment | Assignee |")
        lines.append("|---|---|---|---|---|---|")
        for issue in issues:
            key = issue['key']
            link = f"{jira_url}/browse/{key}" if jira_url else key
            summary = issue['summary'].replace("|", "\\|")
            
            llm_summary = issue['llm_summary'] or "*(No summary available)*"
            llm_summary_display = llm_summary.replace("\n", "<br>")
            
            latest_comment = issue['latest_comment'] or ""
            latest_comment_preview = latest_comment.replace("\n", " ").replace("\r", "")
            if len(latest_comment_preview) > 100:
                latest_comment_preview = latest_comment_preview[:97] + "..."
            
            assignee = issue['assignee'] or "Unassigned"
            updated_at = issue['updated'][:16].replace('T', ' ') if issue['updated'] else "N/A"
            
            summary_display = f"**{summary}**"
            
            # Add stale indicator if not updated recently (with line break before Summary)
            stale_badge = "⚠️ _No recent update_<br><br>" if issue.get('is_stale') else ""
            comment_display = f"{stale_badge}**Summary:**<br>{llm_summary_display}<br><br>**Latest Team Update:**<br>_{latest_comment_preview or 'N/A'}_"

            priority = issue['priority']
            if priority in ['Critical', 'Blocker']:
                priority = f"🔥 **{priority}**"
            
            lines.append(f"| [{key}]({link}) | {priority} | {issue['status']} | {summary_display} | {comment_display} <br><small>Updated: {updated_at}</small> | {assignee} |")
    else:
        lines.append("*No issues matching the criteria were updated in the last 7 days.*")

    lines.append("\n\n---")
    lines.append("*Report generated by Jira Dashboard API Tool*")

    return "\n".join(lines)
