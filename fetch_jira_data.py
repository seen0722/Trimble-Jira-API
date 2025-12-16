import os
import json
import base64
import datetime
import requests
from dotenv import load_dotenv

def get_jira_headers(email, match_string, auth_type="basic"):
    if auth_type.lower() == "bearer":
        return {
            "Authorization": f"Bearer {match_string}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    # Default to Basic
    auth_str = f"{email}:{match_string}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    return {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def fetch_issues(jira_url, jql, email, api_token, max_results=1000):
    url = f"{jira_url}/rest/api/2/search" # Use api/2 for broader compatibility (Server/DC)
    issues = []
    start_at = 0
    
    print(f"Fetching issues with JQL: {jql}")
    print(f"Request URL: {url}")
    
    # Initial attempt with Basic Auth
    headers = get_jira_headers(email, api_token, "basic")
    
    # Test connection and auth type
    test_params = {"jql": jql, "maxResults": 1}
    response = requests.get(url, headers=headers, params=test_params)
    
    if response.status_code == 401:
        print("Basic Auth failed (401). Trying Bearer Auth (PAT) for Data Center...")
        headers = get_jira_headers(email, api_token, "bearer")
        response = requests.get(url, headers=headers, params=test_params)
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code} - {response.text}")
        return []

    print("Authentication successful.")

    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": 100,
            "fields": ["summary", "status", "assignee", "created", "priority", "description", "resolutiondate", "issuetype", "reporter", "updated", "labels"]
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        batch = data.get("issues", [])
        if not batch:
            break
            
        issues.extend(batch)
        print(f"Fetched {len(batch)} issues (Total: {len(issues)})")
        
        start_at += len(batch)
        if start_at >= data.get("total", 0) or len(issues) >= max_results:
            break
            
    return issues

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {filename}")

def main():
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    jql_query = os.getenv("JIRA_JQL_QUERY")
    
    if not all([jira_url, email, api_token, jql_query]):
        print("Error: Missing environment variables. Please check your .env file.")
        print("Required: JIRA_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN, JIRA_JQL_QUERY")
        return

    headers = None # Handled inside fetch_issues now
    issues = fetch_issues(jira_url, jql_query, email, api_token)
    
    if issues:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jira_data_{timestamp}.json"
        save_to_json(issues, filename)
    else:
        print("No issues found.")

if __name__ == "__main__":
    main()
