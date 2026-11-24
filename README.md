# AutoTube AI

AI-assisted YouTube production workspace for bilingual (Hindi/English) technology content.
Supports Shorts and long-form videos. Every video must pass human approval before publishing.

## Architecture

- `apps/web`: Next.js creator dashboard
- `apps/api`: FastAPI backend
- `infra`: local PostgreSQL and Redis
- `docs`: architecture and implementation plan

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop

## Start infrastructure

```powershell
docker compose up -d
```

## Start API

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload --port 8000
```

API health: http://localhost:8000/health

## Start web app

```powershell
cd apps/web
npm install
npm run dev
```

Web app: http://localhost:3000

## Safety and publishing rule

Generated videos are drafts by default. Publishing is blocked unless a user explicitly approves
the final rendered asset and its title/description. Never place API keys in source control.
