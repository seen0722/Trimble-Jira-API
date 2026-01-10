# Trimble Jira API & Dashboard

A specialized tool for fetching, analyzing, and generating reports from Trimble Jira data.

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

> **Note**: Make sure you have added your server's SSH public key to your [GitHub account](https://github.com/settings/keys).

2. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your JIRA_API_KEY, JIRA_URL, etc.
   vim .env
   ```

3. **Start the services**
   ```bash
   docker-compose up -d --build
   ```

### Accessing the App

- **Frontend**: http://your-vultr-ip
- **Backend API**: http://your-vultr-ip:8000/docs (Swagger UI)

---

## 🛠 Project Structure

- `frontend/`: Vite-based dashboard.
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
