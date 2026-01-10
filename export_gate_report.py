from backend import services
import datetime
import os

def generate_report():
    print("Fetching Gate Backlog (OS_FCS)...")
    # Fetch all issues including closed, filtered by OS_FCS
    bugs = services.get_bugs_list(label_filter="OS_FCS", include_closed=True)
    
    if not bugs:
        print("No issues found for OS_FCS.")
        return

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"gate_report_{date_str}.md"
    
    print(f"Generating {filename} with {len(bugs)} issues...")
    
    
    # Calculate Status Counts
    from collections import Counter
    status_counts = Counter(b['status'] for b in bugs)
    
    # Define logical order for summary
    status_order = ['New', 'Open', 'In Progress', 'Ready for Test', 'In Test', 'Resolved', 'Closed', 'Done']
    
    # Priority/Status mapping for sorting
    priority_order = {
        'Critical': 1, 'Blocker': 1, 'High': 2, 'Medium': 3, 'Low': 4, 'None': 5
    }
    status_order_map = {
        'New': 1, 'Open': 2, 'In Progress': 3, 'Ready for Test': 4, 
        'In Test': 5, 'Resolved': 6, 'Closed': 7, 'Done': 8
    }

    # Sort bugs: Status first, then Priority
    bugs.sort(key=lambda x: (
        status_order_map.get(x['status'], 99),
        priority_order.get(x['priority'], 99)
    ))

    with open(filename, "w") as f:
        f.write(f"# Gate Backlog Report - {date_str}\n\n")
        f.write(f"**Filter**: Label = `OS_FCS` (Includes all statuses)\n")
        f.write(f"**Total Issues**: {len(bugs)}\n\n")
        
        # Summary Dashboard
        f.write("## Status Overview\n")
        f.write("| Status | Count |\n")
        f.write("|---|---|\n")
        for status in status_order:
            if status_counts[status] > 0:
                f.write(f"| **{status}** | {status_counts[status]} |\n")
        
        # Add any statuses not in the standard list
        for status, count in status_counts.items():
            if status not in status_order:
                 f.write(f"| **{status}** | {count} |\n")
        f.write("\n---\n\n")
        f.write("## Detailed Issue List\n\n")
        
        # Table Header
        f.write("| Key | Priority | Status | Summary | Assignee | Reporter | Remark |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        
        # Table Rows
        for bug in bugs:
            # Create link manually if bug['link'] is just the URL, or use [Key](URL) if feasible
            # logic in services.py sets 'link' to full URL.
            key_link = f"[{bug['key']}]({bug['link']})" if bug['link'] else bug['key']
            
            # Format table row
            # Escape pipes strictly speaking, but summary usually fine.
            summary = bug['summary'].replace("|", "\\|")
            assignee = bug['assignee'] or "Unassigned"
            reporter = bug['reporter'] or "-"
            
            # Remark column empty
            row = f"| {key_link} | {bug['priority']} | {bug['status']} | {summary} | {assignee} | {reporter} |   |\n"
            f.write(row)
            
    print(f"Successfully created {filename}")

if __name__ == "__main__":
    generate_report()
