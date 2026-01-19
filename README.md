# Trimble Jira API & Dashboard

A specialized tool for fetching, analyzing, and generating reports from Trimble Jira data.

## 🚀 Docker Hub Images (Multi-Architecture)
Pre-built images for Linux/AMD64 are available on Docker Hub:
```bash
docker pull seen0516/jira-api-backend:latest
docker pull seen0516/jira-api-frontend:latest
```

## 🧠 LLM Providers
This project supports multiple LLM providers for generating weekly summaries:
1. **OpenAI** (default): Uses `gpt-4o-mini` or other models.
2. **Cambrian** (Internal): Pegatron's internal secure LLM gateway (drop-in replacement).
   - *Note: SSL verification is disabled for internal Cambrian endpoints.*

## 🚀 Deployment (Vultr / VPS)

This project is containerized using Docker for easy deployment.

### Prerequisites

- Docker and Docker Compose installed on your server.
- A GitHub personal access token (if the repo is private).

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone git@github.com:seen0722/Trimble-Jira-API.git
   cd Trimble-Jira-API
   ```

2. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env to configure Jira keys and LLM provider
   vim .env
   ```
   
   **Key .env settings:**
   - `LLM_PROVIDER`: Set to `cambrian` (default) or `openai`.
   - `CAMBRIAN_BASE_URL`: Endpoint for internal LLM (e.g., `https://api.cambrian.pegatroncorp.com`).
   - `CAMBRIAN_MODEL`: Model name (e.g., `LLAMA 3.3 70B`).

3. **Start the services**
   ```bash
   docker compose up -d --build
   ```

### Accessing the App

- **Frontend**: http://your-vultr-ip:8081
- **Backend API**: http://your-vultr-ip:8081/api/docs (Swagger UI)

---

## 🛠 Project Structure

- `frontend/`: Vite-based dashboard (React + Recharts).
- `backend/`: FastAPI services.
- `docker-compose.yml`: Full-stack orchestration.
- `nginx.conf`: Routing and API proxying.

## 🧪 Local Development

Backend:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```
