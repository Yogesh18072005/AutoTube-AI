# AutoTube AI architecture

## Content lifecycle

`IDEA -> RESEARCHED -> SCRIPT_DRAFT -> SCRIPT_APPROVED -> ASSETS_GENERATED -> RENDERED -> VIDEO_REVIEW -> APPROVED -> SCHEDULED -> PUBLISHED`

A rejected item returns to editing. Publishing endpoints must enforce `APPROVED` status server-side.

## Services

1. Research: topic discovery, source capture, duplicate checks, trend scoring.
2. Script: Hindi/English scripts with hooks, scene plan, citations/source notes.
3. Media: provider adapters for TTS and image/video assets.
4. Renderer: FFmpeg-based vertical (9:16) and horizontal (16:9) outputs.
5. Review: preview, metadata editing, quality checklist, approve/reject.
6. Publishing: OAuth connection, upload, schedule, status reconciliation.
7. Analytics: views, watch time, retention and content performance.

## Key design decisions

- Provider adapters keep AI, TTS and media vendors replaceable.
- Celery/Redis handles long-running jobs; API requests do not render videos inline.
- PostgreSQL stores workflow state and metadata; object storage stores media.
- Every generated asset records provider, prompt, language and provenance.
- Human approval is mandatory before upload/scheduling.
- Secrets are environment-managed; never committed.

## Initial API boundaries

- `GET /health`
- `GET /api/v1/projects`
- `POST /api/v1/ideas`
- `POST /api/v1/scripts`
- `POST /api/v1/videos`
- `POST /api/v1/videos/{id}/approve`
- `POST /api/v1/videos/{id}/reject`
- `POST /api/v1/publishing/{id}/schedule`

Only `/health` is implemented in the initial scaffold. Other endpoints are planned milestones.
