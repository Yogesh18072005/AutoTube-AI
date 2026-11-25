# AutoTube AI — Architecture

## Product scope

AutoTube AI is a bilingual (English/Hindi) workspace for planning and managing YouTube Shorts and long-form video content. The current repository contains a Next.js dashboard, a Java Spring Boot API, PostgreSQL persistence, an optional OpenAI-compatible script-generation adapter, and a legacy FastAPI service retained during migration.

The application is a development-stage MVP, not a production YouTube automation service.

## System overview

```text
Browser
  |
  v
Next.js 15 / React 19 dashboard (apps/web)
  |
  | HTTP / JSON, NEXT_PUBLIC_API_URL
  v
Spring Boot 3.5 / Java 21 API (apps/backend)
  |                         |
  | Spring Data JPA         | OpenAI-compatible Chat Completions
  v                         v
PostgreSQL              Configured AI provider
  |
  +-- content_records (ideas, research, scripts, videos, settings)

Redis service: provisioned in Docker Compose; application-level job orchestration is not yet implemented.
FastAPI service (apps/api): legacy implementation retained during migration; it is not the primary API in the current Java-backed dashboard.
```

## Current modules and implementation status

| Module | Current implementation |
|---|---|
| Dashboard | Next.js workspace navigation, pipeline metrics, forms and record lists |
| Ideas | Topic records persisted through the Java API |
| Research | Structured starter brief and hook suggestions; no live source discovery |
| Script Studio | Template draft endpoint plus optional server-side AI generation |
| Video records | Create, list, approve and request-changes workflow |
| SEO Studio | Starter title, description, tags and hashtags; no live keyword data |
| Analytics | Workspace record counts; YouTube channel metrics are not connected |
| Settings | Workspace defaults persisted as records |
| Publishing | Server checks approval, then returns an explicit not-implemented response |
| Voice, rendering, thumbnails | UI guidance/placeholders; provider and rendering integrations are pending |
| Automation | Workflow outline only; durable background workers and retries are pending |

## API surface

The Java service listens on port 8000 by default.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/api/v1/config` | Supported languages, formats and modules |
| GET | `/api/v1/records` | List workspace records; optional `kind` filter |
| GET / PUT | `/api/v1/settings` | Read or save workspace defaults |
| POST | `/api/v1/ideas` | Save an idea |
| POST | `/api/v1/research` | Create a starter research brief |
| POST | `/api/v1/scripts` | Create a template script |
| POST | `/api/v1/scripts/generate` | Generate a script through configured AI provider |
| POST | `/api/v1/seo/generate` | Create starter SEO metadata |
| POST | `/api/v1/videos` | Create a video draft |
| POST | `/api/v1/videos/{id}/approve` | Approve a video record |
| POST | `/api/v1/videos/{id}/reject` | Request changes |
| POST | `/api/v1/publishing/{id}/schedule` | Approval-gated; live publishing is not implemented |
| GET | `/api/v1/analytics/overview` | Workspace pipeline totals |

Voice generation and title-card rendering endpoints intentionally return HTTP 501 until their integrations are migrated.

## Content lifecycle and approval boundary

```text
IDEA -> RESEARCH BRIEF -> SCRIPT DRAFT -> VIDEO REVIEW
                                      |          |
                                      |          +-> CHANGES REQUESTED
                                      |          |
                                      +----------+-> APPROVED
                                                     |
                                                     v
                                       PUBLISHING ADAPTER (pending)
```

The Java API checks the persisted video status before accepting a scheduling request. An unapproved video receives HTTP 409. An approved video currently receives HTTP 501 because YouTube OAuth upload and scheduling have not been implemented. The UI is not treated as the security boundary.

## Local development

From the repository root:

1. Copy `.env.example` to `.env` and set local values if needed.
2. Start PostgreSQL, Redis and the Java API with `docker compose up --build`.
3. In another terminal, run `cd apps/web`, `npm ci`, then `npm run dev`.
4. Open `http://localhost:3000`. The dashboard calls the API at `http://localhost:8000` by default.

To run Java tests locally: `cd apps/backend; mvn test`.

## Continuous integration

GitHub Actions runs Java tests and frontend lint, type-check and production-build checks for pushes and pull requests targeting `main`.

## Planned production work

- Authentication, per-user authorization, audit logs and rate limits
- Database migrations and tenant-aware data ownership
- Redis-backed job queue, retries and worker monitoring
- Provider adapters for live research, narration, image generation and video rendering
- Durable media storage and asset provenance
- YouTube OAuth, secure token storage, upload reconciliation and Analytics API ingestion
- Deployment configuration, observability, backup and operational documentation

## Security and reliability principles

- Keep provider credentials in server-side environment variables; never expose secrets through `NEXT_PUBLIC_*` variables.
- Do not claim an asset, upload, or analytics result exists unless the integration actually produced it.
- Keep human approval as a server-enforced prerequisite for publishing.
- Surface provider and service failures instead of silently reporting success.
