# AutoTube AI

**A bilingual AI-assisted YouTube content production workspace for Shorts and long-form videos.**

AutoTube AI combines a Next.js creator dashboard, a FastAPI production API, a Redis/Celery background worker, and a Java Spring Boot backend retained as an optional migration track. The default Docker setup runs the API and worker that contain the current provider integrations.

## What works in the current implementation

- **Ideas and content records:** persistent workspace records in the API's SQLite database volume.
- **AI research briefs and scripts:** OpenAI-compatible text generation. AI research briefs explicitly require human source verification; the app does not fabricate citations.
- **SEO metadata:** provider-generated titles, descriptions, tags and hashtags.
- **Voice generation:** ElevenLabs MP3 generation when an API key and voice ID are configured.
- **Media generation:** OpenAI image generation and local 1280×720 thumbnail generation.
- **Video rendering:** FFmpeg title-card rendering and a multi-scene text-card renderer with optional narration audio. This is a starter renderer, not a full nonlinear video editor.
- **Background production:** Redis/Celery worker creates a research brief, structured script, optional narration, multi-scene text-card video, thumbnail, SEO metadata and a video draft.
- **YouTube channel connection:** Google OAuth with encrypted token storage outside the public media directory.
- **YouTube publishing:** resumable upload and scheduled publication for an approved video that references a generated MP4 asset.
- **YouTube analytics:** Analytics API endpoint after channel authorization.
- **Approval boundary:** the API rejects publishing unless the video record has been approved.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript |
| Production API | Python 3.12, FastAPI, Pydantic |
| Background jobs | Celery, Redis |
| Media | FFmpeg, Pillow |
| Persistence | SQLite in a Docker volume for the current FastAPI runtime |
| Optional backend migration | Java 21, Spring Boot 3.5, Spring Data JPA, PostgreSQL |
| AI text and images | OpenAI-compatible Chat Completions API, OpenAI Images API |
| Voice | ElevenLabs |
| YouTube | Google OAuth 2.0, YouTube Data API v3, YouTube Analytics API |
| Tooling | Docker Compose, Maven, npm, GitHub Actions |

## Repository layout

```text
apps/
  web/       Next.js + TypeScript dashboard
  api/       FastAPI production API, OAuth, media adapters and Celery worker
  backend/   Java Spring Boot migration backend
docs/        Architecture and setup notes
docker-compose.yml
.env.example
```

## Setup (Windows PowerShell)

### Prerequisites

- Docker Desktop
- Node.js 22 or later and npm
- A modern browser

Java 21 and Maven are only required if you also want to run the optional Java migration backend.

### 1. Create your local environment file

From the repository root:

```powershell
Copy-Item .env.example .env
```

The API automatically creates strong, persistent OAuth-signing and token-encryption keys inside the `autotube_data` Docker volume on first use. You do not need to generate or paste these keys. Keep the volume when restarting or upgrading the app, and back it up with the rest of your application data. You may set `AUTOTUBE_SECRET_KEY` and `AUTOTUBE_TOKEN_ENCRYPTION_KEY` explicitly if you manage secrets yourself. Do not commit `.env`.

### 2. Add provider credentials

- **OpenAI:** set `OPENAI_API_KEY`. This enables AI research briefs, scripts, SEO metadata, and image generation. Confirm that the selected model and image endpoint are enabled for your account.
- **ElevenLabs (optional):** set `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`.
- **YouTube:** create a Google OAuth client of type Web application. Enable YouTube Data API v3 and YouTube Analytics API. Add this exact authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`. Set `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REDIRECT_URI`.
- **YouTube trend search (optional):** set `YOUTUBE_DATA_API_KEY`.

For Google OAuth, configure the consent screen and add your Google account as a test user while the app is in testing mode. The OAuth client secret and all API keys belong only in the server-side `.env` file.

### 3. Start the API and worker

```powershell
docker compose up --build
```

This starts:
- FastAPI at `http://localhost:8000`
- Interactive API documentation at `http://localhost:8000/docs`
- Redis and the Celery worker
- Persistent Docker volumes for records, generated media and encrypted OAuth tokens

Health check: `http://localhost:8000/health`.

### 4. Start the dashboard

Open a second PowerShell window:

```powershell
Set-Location apps/web
npm ci
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

Open `http://localhost:3000`.

### 5. Connect YouTube

Open **Channels** in the dashboard and select **Connect YouTube with Google**. Complete Google's consent flow. The API stores the returned tokens encrypted in the private application data volume. Do not delete that volume if you want to keep the channel connection.

### 6. Run the production pipeline

Open **Automation**, enter a topic and start the pipeline. The worker uses the configured OpenAI provider and creates a research brief, script, title-card MP4, thumbnail, SEO draft and video review record. If ElevenLabs credentials are present, it also creates narration audio.

The automation MP4 is a sequence of text-based scene cards with optional generated narration. It is not a full automatic stock-footage editor and does not add motion graphics or automatic captions. Research output is an AI brief and must be fact-checked; it is not live sourced research.

### 7. Approve and schedule

Open **Approval Queue** and review the generated record. Only approve a video after checking the script, media, metadata, rights and factual claims. Then use **Publishing** to schedule it. The backend checks approval and uploads the referenced MP4 through YouTube's resumable upload API. Scheduled videos are uploaded as private with YouTube's `publishAt` value.

**Publishing is a real external action.** Test with private or unlisted content first. The project intentionally does not auto-publish unreviewed drafts.

## API highlights

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/research/brief` | Credential-backed AI research brief (verify factual claims) |
| GET | `/api/v1/research/trends` | Recent YouTube trend candidates (optional Data API key) |
| POST | `/api/v1/scripts/generate` | AI script generation |
| POST | `/api/v1/voice/generate` | ElevenLabs narration |
| POST | `/api/v1/media/image` | OpenAI image generation |
| POST | `/api/v1/render/title-card` | FFmpeg title-card MP4 |
| POST | `/api/v1/videos/render-project` | Basic scene-card render |
| POST | `/api/v1/thumbnails/generate` | 1280×720 thumbnail |
| GET | `/api/v1/auth/google/start` | Begin YouTube OAuth |
| GET | `/api/v1/auth/google/status` | Safe connection status |
| POST | `/api/v1/automation/queue` | Queue a production job |
| GET | `/api/v1/automation/jobs/{job_id}` | Read job status/result |
| POST | `/api/v1/publishing/{video_id}/schedule` | Approval-gated YouTube upload/schedule |
| GET | `/api/v1/analytics/youtube` | Live YouTube Analytics report |
| GET | `/api/v1/research/trends` | Recent YouTube trend candidates |

## Optional Java migration backend

The Java service is not the default dashboard API yet. It can be started alongside the production API with:

```powershell
docker compose --profile java-migration up --build
```

It listens on `http://localhost:8001` and uses PostgreSQL. The FastAPI service remains the integrated runtime until the Java backend reaches feature parity. Do not point the dashboard at the Java service if you need the OAuth, media and worker features listed above.

## Tests and CI

GitHub Actions checks:
- Python API tests
- Java backend tests
- Frontend ESLint, TypeScript and production build

Run tests locally:

```powershell
Set-Location apps/api
python -m pip install -e ".[dev]"
pytest -q

Set-Location ../backend
mvn test

Set-Location ../web
npm ci
npm run lint
npm run typecheck
npm run build
```

## Security and operational notes

- Provider secrets stay server-side; never put them in `NEXT_PUBLIC_*` variables or commit `.env`.
- OAuth tokens are encrypted with Fernet and stored in the private `/app/data` volume, not in the publicly served media directory.
- Back up the Docker volumes and retain the same `AUTOTUBE_TOKEN_ENCRYPTION_KEY`; losing it makes stored OAuth tokens unreadable.
- Set strong unique application secrets before connecting accounts.
- Configure Google OAuth authorized domains/redirect URIs for any deployed host; the localhost callback is for local development only.
- Use HTTPS, authentication, per-user authorization, rate limits, monitoring, managed storage and a production database before exposing this as a public multi-user service.
- Provider usage may incur charges. Check each provider's pricing and quotas.

