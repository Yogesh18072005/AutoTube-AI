from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from celery import Celery

celery_app = Celery(
    "autotube",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


async def _generate_content(project: dict[str, Any]) -> dict[str, Any]:
    from app.main import now, save
    from app.production import generate_text, synthesize_voice, ProviderNotConfigured

    topic = str(project["topic"]).strip()
    language = str(project.get("language", "en"))
    video_format = str(project.get("format", "short"))
    audience = str(project.get("audience", "Beginners"))
    language_name = "Hindi" if language == "hi" else "English"

    research_prompt = (
        f"Prepare a creator research brief about {topic} for {audience} in {language_name}. "
        "Separate established background knowledge from claims that need source verification. "
        "Do not invent citations, URLs, statistics, or current trends. Return concise sections: "
        "overview, key points, audience questions, possible angles, and verification checklist."
    )
    research_text = await generate_text(
        research_prompt,
        system="You are a careful research assistant. Never fabricate sources or current facts.",
    )
    research = save(
        "research",
        {
            **project,
            "brief": research_text,
            "research_status": "ai_brief_needs_source_verification",
            "source_notes": [],
            "created_at": now(),
        },
        "researched",
    )

    length = "45-60 seconds" if video_format == "short" else "6-10 minutes"
    script_prompt = (
        f"Write an original YouTube script about {topic} in {language_name}, for {audience}. "
        f"Target length: {length}. Use the following research brief as background, not as proof: "
        f"{research_text}. Include a strong hook, spoken narration, scene-by-scene visual directions, "
        "a clear ending, and mark factual claims that need verification."
    )
    script_text = await generate_text(
        script_prompt,
        system="You are an experienced bilingual YouTube scriptwriter. Produce a useful, natural script.",
    )
    script = save(
        "script",
        {
            **project,
            "full_text": script_text,
            "research_id": research["id"],
            "generation_mode": "openai",
            "provider": "openai-compatible",
        },
        "script_draft",
    )

    voice_asset = None
    voice_note = "Voice generation skipped: configure ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID to enable narration."
    if os.getenv("ELEVENLABS_API_KEY") and os.getenv("ELEVENLABS_VOICE_ID"):
        voice_path = await synthesize_voice(script_text[:5000])
        voice_asset = save(
            "asset",
            {
                "asset_type": "voice",
                "file_name": voice_path.name,
                "url": f"/media/{voice_path.name}",
                "mime_type": "audio/mpeg",
                "provider": "elevenlabs",
            },
            "ready",
        )
        voice_note = "Narration generated with ElevenLabs."

    from app.production import render_title_card, public_media_url
    audio_path = None
    if voice_asset:
        from app.production import MEDIA_ROOT
        audio_path = str(MEDIA_ROOT / voice_asset["data"]["file_name"])
    video_path = render_title_card(topic, duration_seconds=8, audio_path=audio_path)
    video_asset = save(
        "asset",
        {
            "asset_type": "video",
            "file_name": video_path.name,
            "url": public_media_url(video_path),
            "mime_type": "video/mp4",
            "render_type": "branded_title_card",
        },
        "rendered",
    )

    from app.advanced import ThumbnailRequest, generate_thumbnail
    thumbnail = generate_thumbnail(ThumbnailRequest(title=topic, subtitle="Created with AutoTube AI"))

    seo_prompt = (
        f"Return valid JSON only with title_options (3), description, tags (10), and hashtags (5) "
        f"for a {video_format} YouTube video about {topic} in {language_name}. "
        "Do not claim guaranteed rankings or invent factual details."
    )
    seo_text = await generate_text(
        seo_prompt,
        system="You create accurate YouTube metadata. Return only valid JSON.",
    )
    try:
        seo_metadata = json.loads(seo_text)
    except json.JSONDecodeError:
        seo_metadata = {
            "title_options": [topic[:100]],
            "description": f"A video about {topic}. Please verify all factual claims before publishing.",
            "tags": [],
            "hashtags": [],
            "provider_warning": "The AI response was not valid JSON; review and edit this fallback metadata.",
        }
    seo = save("seo", {**project, "metadata": seo_metadata}, "draft")

    video = save(
        "video",
        {
            "title": topic[:100],
            "description": str(seo_metadata.get("description", "")),
            "language": language,
            "format": video_format,
            "script": script_text,
            "script_id": script["id"],
            "research_id": research["id"],
            "seo_id": seo["id"],
            "asset_url": video_asset["data"]["url"],
            "thumbnail_url": thumbnail["url"],
            "voice_asset_url": voice_asset["data"]["url"] if voice_asset else None,
            "tags": seo_metadata.get("tags", []),
            "production_notes": [
                "The generated MP4 is a branded title-card render, not a full scene-based edit.",
                "Review the script, metadata, visual assets, and factual claims before approval.",
                voice_note,
            ],
        },
        "video_review",
    )
    return {
        "status": "review_required",
        "approval_required": True,
        "research_id": research["id"],
        "script_id": script["id"],
        "video_id": video["id"],
        "video_asset": video_asset["data"]["url"],
        "thumbnail": thumbnail["url"],
        "voice_generated": bool(voice_asset),
        "message": "Draft assets created. Human review is required before YouTube publishing.",
    }


@celery_app.task(bind=True, name="autotube.execute_pipeline")
def execute_pipeline(self, project: dict[str, Any]) -> dict[str, Any]:
    required = ["topic", "language", "format"]
    missing = [key for key in required if not project.get(key)]
    if missing:
        raise ValueError("Missing pipeline fields: " + ", ".join(missing))
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to run the content automation pipeline.")
    return asyncio.run(_generate_content(project))
