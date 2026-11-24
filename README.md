# AutoTube AI

A bilingual (Hindi/English) AI & technology YouTube production workspace for Shorts and long-form videos. The platform is designed around a strict human approval gate before publishing.

## Workspace modules

- Dashboard and channel configuration
- Topic ideas and research briefs
- Hindi/English script studio
- Voice, media library and asset provenance workflows
- Video editing/rendering workflow planning
- Thumbnail and SEO workspaces
- Approval queue with approve/reject actions
- YouTube publishing and scheduling boundary
- Analytics overview
- Automation status and provider settings

## Stack

- Web: Next.js 15, React 19, TypeScript
- API: FastAPI + Pydantic
- Local persistence: SQLite starter store (replace with PostgreSQL for deployment)
- Infrastructure: PostgreSQL and Redis services in Docker Compose
- Planned production workers: Redis/Celery + FFmpeg
- External integrations: AI/LLM, TTS, media generation, YouTube Data API and YouTube Analytics API

## Run locally (PowerShell)

Start from the repository root.

```powershell
# Terminal 1: API
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

```powershell
# Terminal 2: web app
cd apps/web
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs.

## Tests and checks

```powershell
# API
cd apps/api
pytest

# Web
cd apps/web
npm run typecheck
npm run lint
npm run build
```

## Provider configuration

Copy `.env.example` to `.env` for local configuration. Keep all secrets on the API/server side. Never commit API keys or OAuth tokens.

The current release provides a working local workflow foundation and provider boundaries. Research and script endpoints use clearly labelled template fallbacks until an AI/search provider is configured. Voice generation, generated media, FFmpeg rendering, real YouTube OAuth uploads, and real channel analytics require their respective provider credentials and background services; they are not simulated as successful.

## Publishing safety

- New videos are created in review state.
- Only an explicitly approved video can enter the scheduling endpoint.
- The API rejects scheduling for unapproved videos.
- YouTube OAuth must be configured before scheduling can proceed.
- Review the final rendered file and metadata before approving.

## Production hardening still required

Before public deployment: replace the local SQLite starter store with PostgreSQL migrations, add authentication and per-user authorization, configure durable object storage, add Redis/Celery workers, implement provider adapters, complete YouTube OAuth/token refresh and upload reconciliation, and add rate limits, audit logging and deployment secrets management.
