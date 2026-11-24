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

## Production endpoints\n\n- `POST /api/v1/scripts/generate` — provider-backed bilingual script generation.\n- `POST /api/v1/voice/generate` — ElevenLabs narration; stores an MP3 under `/media/`.\n- `POST /api/v1/render/title-card` — FFmpeg title-card MP4 render, optionally with a generated narration asset.\n- `POST /api/v1/seo/generate` — provider-backed YouTube metadata JSON.\n\nThese endpoints require server-side configuration and are not a replacement for a full multi-scene editor or a live YouTube publishing integration.\n\n## Provider configuration

Copy `.env.example` to `.env` for local configuration. Keep all secrets on the API/server side. Never commit API keys or OAuth tokens.

The current release includes local workflow records plus optional real production endpoints. Configure OPENAI_API_KEY for provider-backed script and SEO generation, ELEVENLABS_API_KEY plus ELEVENLABS_VOICE_ID for narration, and install FFmpeg on the API host for title-card MP4 rendering. Missing providers return explicit errors; the app does not fabricate successful assets. Live trend discovery, full timeline editing, image/video generation, YouTube OAuth uploads, and real channel analytics still require their dedicated integrations and services.

## Publishing safety

- New videos are created in review state.
- Only an explicitly approved video can enter the scheduling endpoint.
- The API rejects scheduling for unapproved videos.
- YouTube OAuth must be configured before scheduling can proceed.
- Review the final rendered file and metadata before approving.

## Production hardening still required

Before public deployment: replace the local SQLite starter store with PostgreSQL migrations, add authentication and per-user authorization, configure durable object storage, add Redis/Celery workers, implement provider adapters, complete YouTube OAuth/token refresh and upload reconciliation, and add rate limits, audit logging and deployment secrets management.
