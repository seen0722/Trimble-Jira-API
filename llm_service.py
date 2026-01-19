import os
import requests
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "cambrian").lower()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL") # For Ollama or vLLM
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if self.provider == "openai" and self.api_key:
            self.client = OpenAI(api_key=self.api_key, timeout=30.0)
        else:
            self.client = None

        # Cambrian Configuration
        self.cambrian_base_url = os.getenv("CAMBRIAN_BASE_URL")
        self.cambrian_api_key = os.getenv("CAMBRIAN_API_KEY", "dummy-key")
        self.cambrian_model = os.getenv("CAMBRIAN_MODEL", "cambrian-1")
        
        if self.cambrian_base_url:
            # Normalize URL to ensure it ends with /v1
            if not self.cambrian_base_url.rstrip("/").endswith("/v1"):
                self.cambrian_base_url = f"{self.cambrian_base_url.rstrip('/')}/v1"

            # Use httpx client with verify=False for internal endpoint
            http_client = httpx.Client(verify=False)
            self.cambrian_client = OpenAI(
                base_url=self.cambrian_base_url,
                api_key=self.cambrian_api_key,
                http_client=http_client,
                timeout=60.0
            )
        else:
            self.cambrian_client = None

    def summarize_comments(self, issue_key, summary, comments, provider=None):
        if not comments:
            return "No comments available for summary."
        
        target_provider = provider if provider else self.provider
        
        # Check active client based on provider
        active_client = None
        if target_provider == "openai":
            active_client = self.client
        elif target_provider == "cambrian":
            active_client = self.cambrian_client
        
        if not active_client and target_provider in ["openai", "cambrian"]:
            if target_provider == "openai":
                return "[Error: OPENAI_API_KEY not configured]"
            else:
                return "[Error: CAMBRIAN_BASE_URL not configured]"

        # Combine comments into a single string
        comment_text = "\n".join([f"- {c.get('author', {}).get('displayName', 'User')}: {c.get('body', '')}" for c in comments])
        
        prompt = f"""
Summarize the current progress and key discussion points for the following Jira issue based on its comments.
Issue: {issue_key} - {summary}

Comments:
{comment_text}

Provide a concise summary (max 2-3 sentences) focusing on the latest status and any blockers.
Format: Bullet points or a short paragraph.
"""

        try:
            if target_provider == "openai":
                response = active_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional project manager summarizing technical issue progress."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            
            elif target_provider == "cambrian":
                response = active_client.chat.completions.create(
                    model=self.cambrian_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()

            elif target_provider == "ollama":
                url = self.base_url or "http://localhost:11434/api/generate"
                payload = {
                    "model": self.model if self.model != "gpt-4o-mini" else "llama3",
                    "prompt": prompt,
                    "stream": False
                }
                resp = requests.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
                else:
                    return f"[Error: Ollama request failed with status {resp.status_code}]"
            
            return "[Error: Unsupported LLM provider]"

        except Exception as e:
            return f"[Error: LLM summarization failed: {str(e)}]"

# Singleton instance
llm_service = LLMService()
