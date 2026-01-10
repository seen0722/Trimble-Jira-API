import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL") # For Ollama or vLLM
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if self.provider == "openai" and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def summarize_comments(self, issue_key, summary, comments):
        if not comments:
            return "No comments available for summary."
        
        if not self.client and self.provider == "openai":
            return "[Error: OPENAI_API_KEY not configured]"

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
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional project manager summarizing technical issue progress."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "ollama":
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
