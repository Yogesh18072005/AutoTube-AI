# AutoTube AI architecture

## Product scope

A single workspace for bilingual Hindi/English AI & technology YouTube production, supporting Shorts and long-form videos.

## Modules

1. Dashboard and channel setup
2. Topic ideas and research briefs
3. Script studio
4. Voice and narration workspace
5. Media library and asset provenance
6. Video editing and FFmpeg rendering workflow
7. Thumbnail studio
8. SEO metadata studio
9. Human approval queue
10. YouTube publishing
11. Analytics
12. Automation orchestration
13. Provider and workspace settings

## Content lifecycle

`IDEA -> RESEARCHED -> SCRIPT_DRAFT -> ASSETS_GENERATED -> RENDERED -> VIDEO_REVIEW -> APPROVED -> SCHEDULED -> PUBLISHED`

Rejected videos move to `CHANGES_REQUESTED`. The API requires `APPROVED` status before the scheduling boundary. The live YouTube adapter remains disabled until OAuth, upload and reconciliation are implemented.

## Current implementation in feature/full-platform-mvp

- FastAPI endpoints for ideas, research briefs, script drafts, video records, approvals/rejections, analytics summary, settings and automation status.
- SQLite local persistence for the starter workflow.
- Next.js creator workspace with navigation for all product modules.
- API-enforced approval checks.
- Provider configuration placeholders and honest fallback states for missing integrations.
- API tests for health, module configuration and publishing approval enforcement.

## External services still required

- AI/search provider for current topic research and original scripts
- TTS provider for narration
- Image/video generation provider and object storage for media assets
- FFmpeg worker for real video rendering
- Redis/Celery worker for long-running jobs and retries
- YouTube OAuth, Data API upload and Analytics API integration

## Production architecture target

- PostgreSQL with migrations for durable relational data
- Redis + Celery for background jobs
- FFmpeg render workers
- S3-compatible object storage for media
- Provider adapters for LLM, search, TTS and media generation
- YouTube OAuth token encryption, upload reconciliation and analytics ingestion
- Authentication, per-user authorization, audit logs and rate limits

## Security invariants

- Secrets stay in server environment variables; never expose them to the browser.
- A video is not publishable until a user approves the final render and metadata.
- Scheduling and publishing must verify approval on the server, not trust the UI.
- Provider outages must fail visibly; do not report generated assets or uploads that do not exist.
