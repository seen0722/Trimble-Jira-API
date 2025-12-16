import json
import glob
import os
import datetime

def find_latest_json():
    files = glob.glob("jira_data_*.json")
    if not files:
        return None
    return max(files, key=os.path.getctime)

def generate_markdown(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        issues = json.load(f)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    output_file = f"jira_report_{timestamp}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Jira Report - {timestamp}\n\n")
        f.write(f"**Source:** `{input_file}`\n")
        f.write(f"**Total Issues:** {len(issues)}\n\n")
        
        # Table Header
        f.write("| Key | Summary | Status | Assignee | Priority |\n")
        f.write("| --- | --- | --- | --- | --- |\n")

        for issue in issues:
            key = issue.get('key', '')
            fields = issue.get('fields', {})
            summary = fields.get('summary', '').replace('|', r'\|') # Escape pipes for markdown table
            status = fields.get('status', {}).get('name', 'Unknown')
            
            assignee = fields.get('assignee')
            assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
            
            priority = fields.get('priority', {}).get('name', 'None')

            # Attempt to construct browser URL from API 'self' link
            self_url = issue.get('self', '')
            link = key
            if '/rest/api' in self_url:
                base_url = self_url.split('/rest/api')[0]
                link = f"[{key}]({base_url}/browse/{key})"
            
            f.write(f"| {link} | {summary} | {status} | {assignee_name} | {priority} |\n")

    print(f"Successfully generated report: {output_file}")

if __name__ == "__main__":
    latest_file = find_latest_json()
    if latest_file:
        print(f"Processing latest file: {latest_file}")
        generate_markdown(latest_file)
    else:
        print("No jira_data_*.json files found.")
