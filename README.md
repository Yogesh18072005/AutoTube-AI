# AutoTube AI

A bilingual (Hindi/English) YouTube production workspace for Shorts and long-form videos. Publishing must remain behind a human approval step.

## Backend migration

The active migration branch introduces a **Java 21 + Spring Boot 3.5** backend in `apps/backend`. The Next.js frontend remains in `apps/web`. PostgreSQL is the primary database and Redis is included for the upcoming background-job implementation.

The previous FastAPI backend in `apps/api` is retained temporarily as a migration reference. Do not delete it until endpoint parity, data migration, and frontend integration have been verified.

### Java backend currently implemented

- Spring Boot application and CORS configuration
- PostgreSQL/JPA record persistence
- Compatible starter routes for health, config, ideas, research, scripts, video records, review decisions, and analytics overview
- Persistent workspace settings stored as PostgreSQL content records
- Starter SEO metadata drafts (explicitly labeled as template fallback, not live keyword research)
- OpenAI-compatible script generation through the configured server-side API key
- Approval gate: scheduling requests are rejected unless the video record is approved
- Docker image and Docker Compose PostgreSQL/Redis/API services

### Not yet migrated / not production-ready

- Google OAuth, YouTube upload, scheduling, and YouTube Analytics
- ElevenLabs voice generation, image generation, FFmpeg rendering, thumbnails, and full editor (voice/render routes return HTTP 501 until migrated; they do not create placeholder media)
- Real trend research and SEO generation
- Redis-backed end-to-end pipeline workers
- Authentication, authorization, per-user ownership, rate limits, and production security hardening
- Automated data migration from the old SQLite records into PostgreSQL

The Java scheduling endpoint intentionally returns HTTP 501 after checking approval; it does not claim to publish a video. Voice generation and FFmpeg rendering also return HTTP 501 until their real provider/renderer integrations are migrated. Keep these safeguards until the corresponding implementations are completed and tested.

## Requirements

- Java 21
- Maven 3.9+
- Docker Desktop (for PostgreSQL and Redis)
- Node.js/npm for the Next.js frontend

## Run locally (PowerShell)

At the repository root, create your local environment file:

```powershell
Copy-Item .env.example .env
```

Start PostgreSQL, Redis, and the Java API:

```powershell
docker compose up --build
```

Or run the Java API directly after starting PostgreSQL and Redis:

```powershell
cd apps/backend
mvn spring-boot:run
```

The API runs at `http://localhost:8000`; health check: `http://localhost:8000/health`.

Run backend tests:

```powershell
cd apps/backend
mvn test
```

Run the Next.js frontend in a second terminal:

```powershell
cd apps/web
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

## AI configuration

Set `OPENAI_API_KEY` in the root `.env` file. The key is read only by the backend and must never use a `NEXT_PUBLIC_` prefix or be committed to Git.

## Publishing safety

A video must be explicitly approved before scheduling can proceed. The live YouTube publishing integration is not yet migrated to Java, so no real uploads should be attempted from this branch.
