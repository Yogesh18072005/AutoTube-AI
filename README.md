# AutoTube AI

**An AI-assisted, bilingual YouTube content production workspace for Shorts and long-form videos.**

AutoTube AI brings content ideas, research briefs, script drafting, video records, human review, and production analytics into one dashboard. It is designed for English and Hindi creator workflows, with an explicit human-approval gate before any publishing action.

## Project highlights

- **Bilingual workflow:** English and Hindi content settings for YouTube Shorts and long-form videos.
- **Creator dashboard:** Next.js and TypeScript interface with research, script studio, approval queue, publishing, analytics, and workspace settings.
- **Modular backend:** Java 21 and Spring Boot 3.5 REST API, with a Python FastAPI service retained during the backend migration.
- **Persistence and infrastructure:** PostgreSQL with Spring Data JPA, Redis service configuration, and Docker Compose.
- **AI-assisted scripts:** Server-side OpenAI-compatible script generation when an API key is configured.
- **Human-in-the-loop workflow:** Video drafts move through review; scheduling is blocked unless a video has been approved.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Primary backend | Java 21, Spring Boot 3.5, Spring Web, Spring Data JPA |
| Supporting API | Python, FastAPI |
| Database | PostgreSQL |
| Cache / queue infrastructure | Redis (service configured; end-to-end worker pipeline is pending) |
| Dev environment | Docker, Docker Compose, Maven, npm |
| AI integration | OpenAI-compatible Chat Completions API (server-side configuration) |

## Current implementation status

| Area | Current state |
|---|---|
| Dashboard and workspace navigation | Implemented |
| Ideas and content records | REST endpoints and database persistence implemented |
| Research briefs | Structured starter briefs; live web research provider is not connected |
| Script drafting | Template fallback and optional AI-provider generation |
| Video records and review | Create, approve, and reject workflow implemented |
| SEO metadata | Starter template generation; live keyword research is not connected |
| Analytics | Workspace pipeline counts; YouTube channel metrics are not connected |
| Scheduling and YouTube publishing | Approval check is implemented; OAuth upload and scheduling integration remain pending |
| Voice generation and video rendering | Provider/FFmpeg integration remains pending |
| Background automation | Redis infrastructure is configured; complete queue workers are pending |
| Authentication and production hardening | Not yet production-ready |

**Important:** The application does not claim to upload or publish videos, synthesize voice, or render final videos until those provider integrations are implemented. The publishing endpoint checks approval and then returns a not-implemented response. Do not treat this repository as a production deployment.

## Repository structure

```text
apps/
  web/       Next.js + TypeScript creator dashboard
  backend/   Java Spring Boot REST API
  api/       Python FastAPI service retained during migration
docs/        Architecture notes
docker-compose.yml
.env.example
```

## Run locally (Windows PowerShell)

### Prerequisites

- Java 21
- Maven 3.9+
- Node.js and npm
- Docker Desktop

### 1. Configure environment

From the repository root:

```powershell
Copy-Item .env.example .env
```

Add your provider credentials to the local `.env` file only when needed. Never commit `.env` or expose provider keys through `NEXT_PUBLIC_*` variables.

### 2. Start PostgreSQL, Redis, and the Java API

From the repository root:

```powershell
docker compose up --build
```

The API is available at `http://localhost:8000`; health endpoint: `http://localhost:8000/health`.

To run the Java API directly instead, start PostgreSQL and Redis first, then:

```powershell
cd apps/backend
mvn spring-boot:run
```

### 3. Start the frontend

Open a second terminal:

```powershell
cd apps/web
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000`.

### 4. Run Java backend tests

```powershell
cd apps/backend
mvn test
```

## AI script generation

Set `OPENAI_API_KEY` in the root `.env` file to enable the Java backend's AI script-generation integration. Optional model and base URL settings are documented in `.env.example`. Without credentials, provider-backed generation reports that configuration is required; the app does not silently claim a live AI response.

## Safety and publishing workflow

Generated content remains a draft until a person reviews and approves it. The API rejects scheduling requests for unapproved videos. Live YouTube OAuth upload is not yet implemented, so no real video is published by this project at its current stage.

## Development note

The Java Spring Boot service is the primary backend target. The Python FastAPI code remains in the repository as migration/reference code until endpoint parity and the migration are complete.
