# AutoTube AI — Architecture and implementation map

## Runtime topology

The default local stack is a Python production API plus a Redis-backed Celery worker. The Java Spring Boot service is retained as an optional migration backend and is not yet feature-parity with the production API.

```text
Browser
  |
  v
Next.js 15 / React 19 dashboard (apps/web)
  | HTTP / JSON, NEXT_PUBLIC_API_URL
  v
FastAPI production API :8000 (apps/api)
  |-- SQLite records database (/app/data volume)
  |-- encrypted Google OAuth tokens (/app/data volume)
  |-- generated assets (/app/media volume; served as /media)
  |-- OpenAI-compatible text + image adapters
  |-- ElevenLabs speech adapter
  |-- YouTube OAuth, Data API, upload and Analytics adapters
  |
  +---- Redis broker / result backend
             |
             v
        Celery worker
        - AI research brief (requires source verification)
        - AI script
        - optional ElevenLabs narration
        - FFmpeg title-card MP4
        - Pillow thumbnail
        - AI SEO metadata
        - video draft -> human review

Optional migration profile:
Browser / developer -> Java Spring Boot :8001 -> PostgreSQL
```

## Runtime services

| Service | Default | Responsibility |
|---|---:|---|
| `api` | 8000 | FastAPI REST API and provider adapters |
| `worker` | internal | Celery content-production tasks |
| `redis` | 6379 | Celery broker and result backend |
| `java-api` | 8001 (profile only) | Spring Boot migration service |
| `postgres` | 5432 (profile only) | Java migration database |

The default FastAPI implementation currently uses SQLite records stored in a Docker volume. PostgreSQL is used by the optional Java service; the two backends do not share records.

## Provider integrations and required configuration

| Feature | Provider / dependency | Environment |
|---|---|---|
| AI research brief, script and SEO | OpenAI-compatible Chat Completions | `OPENAI_API_KEY`, optional base URL/model |
| Image generation | OpenAI Images API | `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL` |
| Voice generation | ElevenLabs | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` |
| Thumbnail generation | Pillow (local) | no external credential |
| MP4 title-card rendering | FFmpeg (installed in API image) | no external credential |
| YouTube OAuth and upload | Google OAuth + YouTube Data API v3 | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REDIRECT_URI` |
| YouTube Analytics | YouTube Analytics API | same OAuth connection |
| YouTube trend candidates | YouTube Data API key | `YOUTUBE_DATA_API_KEY` |
| OAuth state signing | HMAC | `AUTOTUBE_SECRET_KEY` |
| OAuth token encryption | Fernet | `AUTOTUBE_TOKEN_ENCRYPTION_KEY` |
| Background jobs | Redis/Celery | `REDIS_URL` |

## Content lifecycle and approval boundary

```text
TOPIC -> AI RESEARCH BRIEF -> SCRIPT -> OPTIONAL VOICE
                                      |
                                      v
                              TITLE-CARD MP4
                                      |
                         THUMBNAIL + SEO METADATA
                                      |
                                      v
                                VIDEO REVIEW
                                 /        \
                         CHANGES         APPROVED
                                             |
                                             v
                                 YOUTUBE UPLOAD / SCHEDULE
```

The API verifies that the exact video record is approved before upload. The upload route requires a rendered asset under `/media/` and an authorized YouTube connection. Scheduled uploads remain private and include YouTube's `publishAt` value. The worker never approves or publishes its own draft.

## Implemented API groups

- Workspace records, ideas, research and script drafts
- OpenAI-compatible script and SEO generation
- ElevenLabs speech generation
- OpenAI image generation
- FFmpeg title-card and basic scene-card rendering
- Pillow thumbnail generation
- Google OAuth start/callback/status and encrypted token refresh
- Approval-gated resumable YouTube upload and scheduled publishing
- YouTube Analytics report endpoint
- YouTube trend discovery endpoint
- Celery pipeline queue and job result endpoint

## Important scope boundaries

- The worker's research output is an AI-generated brief, not a source-cited live web-research report. Verify facts before publishing.
- The generated video in the default worker is a branded title-card MP4. It is not a complete scene-based edit with stock footage, motion graphics or automatic captions.
- The basic scene-card renderer creates visual scene cards; it does not yet provide a complete editing timeline.
- The dashboard's media and production tools expose the existing provider endpoints, but full media-library management and asset editing remain future work.
- The Java migration backend currently implements core workspace records and AI script generation. OAuth, publishing, media and queue parity are not complete there.

## Local setup

1. Copy `.env.example` to `.env`.
2. Generate `AUTOTUBE_SECRET_KEY` with Python's `secrets.token_urlsafe(48)`.
3. Generate `AUTOTUBE_TOKEN_ENCRYPTION_KEY` with `Fernet.generate_key()`.
4. Add the provider credentials required for the features you intend to use.
5. Configure Google OAuth's authorized redirect URI as `http://localhost:8000/api/v1/auth/google/callback`.
6. Run `docker compose up --build`.
7. Run the dashboard from `apps/web` with `npm ci`, `NEXT_PUBLIC_API_URL=http://localhost:8000`, and `npm run dev`.

## CI

GitHub Actions runs:
- Python API tests (Python 3.12)
- Java backend tests (Java 21)
- Frontend ESLint, TypeScript and production build (Node 22)

## Security / production checklist

- Keep API keys and OAuth client secrets out of source control and browser bundles.
- Keep OAuth tokens encrypted outside the static media directory.
- Back up `/app/data` and `/app/media`; keep the same Fernet key when restoring.
- Use HTTPS and a production OAuth redirect URI for deployment.
- Add authentication and per-user authorization before multi-user hosting.
- Add tenant isolation, CSRF protection for browser sessions, rate limiting, audit logs and operational monitoring.
- Move SQLite and local media to managed production storage before scaling.
- Monitor provider quotas, costs, upload failures and Celery retries.
