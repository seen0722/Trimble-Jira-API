import os
import requests
import base64
from dotenv import load_dotenv

def get_jira_headers(email, match_string, auth_type="basic"):
    if auth_type.lower() == "bearer":
        return {
            "Authorization": f"Bearer {match_string}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    auth_str = f"{email}:{match_string}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    return {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def list_projects():
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, email, api_token]):
        print("Error: Missing environment variables.")
        return

    url = f"{jira_url}/rest/api/2/project"
    print(f"Fetching projects from: {url}")
    
    # Try Basic Auth first
    headers = get_jira_headers(email, api_token, "basic")
    response = requests.get(url, headers=headers)
    
    # Fallback to Bearer Auth
    if response.status_code == 401:
        print("Basic Auth failed (401). Trying Bearer Auth...")
        headers = get_jira_headers(email, api_token, "bearer")
        response = requests.get(url, headers=headers)
        
    if response.status_code != 200:
        print(f"Error fetching projects: {response.status_code} - {response.text}")
        return

    projects = response.json()
    print(f"\nFound {len(projects)} projects:")
    print("-" * 50)
    print(f"{'KEY':<15} | {'NAME'}")
    print("-" * 50)
    
    for p in projects:
        print(f"{p['key']:<15} | {p['name']}")

if __name__ == "__main__":
    list_projects()
