# AutoTube AI

A Hindi/English YouTube production workspace for Shorts and long-form videos, with a mandatory human approval boundary before upload.

## Implemented in this branch

- FastAPI workflow API and Next.js creator workspace
- SQLite-backed local record store for the existing prototype workflows
- Provider-backed script and SEO generation through an OpenAI-compatible API
- ElevenLabs MP3 narration endpoint
- FFmpeg title-card rendering and a basic multi-scene vertical title-card renderer
- Local PNG thumbnail generation with Pillow
- Live YouTube search signals using YouTube Data API v3
- Google OAuth authorization flow for YouTube scopes
- Encrypted-at-rest OAuth token file using Fernet
- YouTube Analytics reporting endpoint
- Approval-gated resumable video upload endpoint
- PostgreSQL schema migration draft and SQLAlchemy connection module
- Celery/Redis worker foundation and job enqueue/status endpoints
- Docker Compose services for PostgreSQL, Redis, API and worker

## Important limitations

This is an integrated development batch, not a production-complete SaaS release. The Celery task currently validates and records a pipeline job; it does not yet orchestrate every provider stage. The multi-scene renderer creates visual title cards, not full narration-synchronized edits. Captions, transitions, music mixing and generated scene footage are not implemented as a complete editor. Thumbnail generation is a local template renderer, not AI image generation. YouTube OAuth and upload paths require live Google Cloud configuration and have not been verified against a real channel in this repository session.

The current primary record CRUD and review flows still use the local SQLite store. The PostgreSQL migration and SQLAlchemy module are groundwork; the API's existing records have not yet been migrated to PostgreSQL. Account endpoints are an initial registration/login foundation; bearer-token enforcement and per-user authorization are not yet applied across all application routes. Do not expose this build publicly until that is completed.

## Run locally (PowerShell)

Copy `.env.example` to `.env` and fill only the provider credentials you have. Never commit `.env`.

API:
```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Web:
```powershell
cd apps/web
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Docker infrastructure and API/worker:
```powershell
docker compose up --build
```

Apply the SQL migration manually to the configured PostgreSQL database before attempting to use the schema:
```powershell
psql "$env:DATABASE_URL" -f apps/api/migrations/versions/001_initial_schema.sql
```

## Provider configuration

- `OPENAI_API_KEY`: script and SEO generation; image generation endpoint
- `OPENAI_IMAGE_MODEL`: image model name (default configured in API)
- `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`: narration
- `YOUTUBE_DATA_API_KEY`: live YouTube search/trend signals
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REDIRECT_URI`: Google OAuth
- `AUTOTUBE_TOKEN_ENCRYPTION_KEY`: Fernet key for stored OAuth tokens
- `AUTOTUBE_SECRET_KEY`: application signing secret
- `DATABASE_URL` and `REDIS_URL`: PostgreSQL and Celery

Generate a Fernet key with:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Key API routes

- `GET /api/v1/research/trends?q=artificial%20intelligence&region=IN`
- `POST /api/v1/media/image`
- `POST /api/v1/videos/render-project`
- `POST /api/v1/thumbnails/generate`
- `GET /api/v1/auth/google/start`
- `GET /api/v1/auth/google/callback`
- `POST /api/v1/publishing/youtube/upload`
- `GET /api/v1/analytics/youtube?start_date=2026-11-01&end_date=2026-11-24`
- `POST /api/v1/automation/queue`
- `GET /api/v1/automation/jobs/{job_id}`

## Safety and release checklist

- The YouTube upload endpoint checks that the video record is in `approved` state and references a local rendered media asset.
- Keep uploads private while testing; review the rendered file and metadata before approving.
- Configure OAuth redirect URIs exactly as registered in Google Cloud Console.
- Add authentication dependencies to all private routes and enforce per-user ownership before deployment.
- Move media and OAuth tokens to durable, access-controlled storage for multi-instance deployment.
- Complete the PostgreSQL migration of all CRUD code, real pipeline orchestration, caption rendering, worker integration tests, API/web tests, and deployment hardening.
- Run `pytest`, `npm run typecheck`, `npm run lint`, and `npm run build` before merging.
