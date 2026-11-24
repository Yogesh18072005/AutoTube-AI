from __future__ import annotations

import json
import os
import subprocess
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("AUTOTUBE_DB_PATH", str(ROOT / "autotube.db")))

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db() -> None:
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL,
            data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")

def save(kind: str, data: dict[str, Any], status: str = "draft", record_id: str | None = None) -> dict[str, Any]:
    record_id = record_id or str(uuid.uuid4())
    stamp = now()
    with connect() as db:
        db.execute(
            "INSERT INTO records(id,kind,status,data,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (record_id, kind, status, json.dumps(data), stamp, stamp),
        )
    return get_record(record_id)

def get_record(record_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Record not found")
    return {**dict(row), "data": json.loads(row["data"])}

def list_records(kind: str | None = None) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM records WHERE (? IS NULL OR kind=?) ORDER BY created_at DESC",
            (kind, kind),
        ).fetchall()
    return [{**dict(row), "data": json.loads(row["data"])} for row in rows]

def change(record_id: str, *, status: str | None = None, patch: dict[str, Any] | None = None) -> dict[str, Any]:
    item = get_record(record_id)
    data = item["data"]
    if patch:
        data.update(patch)
    with connect() as db:
        db.execute(
            "UPDATE records SET status=?, data=?, updated_at=? WHERE id=?",
            (status or item["status"], json.dumps(data), now(), record_id),
        )
    return get_record(record_id)

class IdeaInput(BaseModel):
    topic: str = Field(min_length=3, max_length=240)
    language: str = "en"
    format: str = "short"
    audience: str = "Beginners"
    notes: str = ""

class ScriptInput(BaseModel):
    idea_id: str | None = None
    topic: str = Field(min_length=3, max_length=240)
    language: str = "en"
    format: str = "short"
    tone: str = "clear and engaging"

class VideoInput(BaseModel):
    title: str
    language: str = "en"
    format: str = "short"
    script: str = ""
    description: str = ""
    tags: list[str] = []
    duration_seconds: int = 60

class DecisionInput(BaseModel):
    note: str = ""

class ScheduleInput(BaseModel):
    scheduled_at: str

class SettingsInput(BaseModel):
    channel_name: str = ""
    default_language: str = "en"
    default_format: str = "short"
    ai_provider: str = "none"
    tts_provider: str = "none"

app = FastAPI(
    title="AutoTube AI API",
    version="0.2.0",
    description="Bilingual YouTube production workflow API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    init_db()

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "autotube-api", "version": "0.2.0"}

@app.get("/api/v1/config", tags=["system"])
def public_config() -> dict[str, Any]:
    return {
        "languages": [{"value": "en", "label": "English"}, {"value": "hi", "label": "Hindi"}],
        "formats": [{"value": "short", "label": "YouTube Shorts"}, {"value": "long", "label": "Long-form"}],
        "modules": ["dashboard", "channels", "research", "scripts", "voice", "media", "editor", "thumbnails", "seo", "approval", "publishing", "analytics", "automation", "settings"],
        "publishing_requires_approval": True,
    }

@app.get("/api/v1/records")
def records(kind: str | None = None) -> list[dict[str, Any]]:
    return list_records(kind)

@app.post("/api/v1/ideas")
def create_idea(payload: IdeaInput) -> dict[str, Any]:
    return save("idea", payload.model_dump(), "idea")

@app.post("/api/v1/research")
def research(payload: IdeaInput) -> dict[str, Any]:
    # Provider-neutral starter: stores a research brief; connect a search/LLM provider for live sources.
    brief = {
        **payload.model_dump(),
        "research_status": "needs_provider",
        "angle": f"What beginners should understand about {payload.topic}",
        "suggested_hooks": [
            f"The truth about {payload.topic} in 30 seconds",
            f"Most beginners misunderstand {payload.topic}",
            f"Before you use {payload.topic}, know this",
        ],
        "source_notes": [],
        "provider_message": "Connect a research/AI provider to retrieve live sources and trend signals.",
    }
    return save("research", brief, "researched")

@app.post("/api/v1/scripts")
def create_script(payload: ScriptInput) -> dict[str, Any]:
    hook = f"Have you ever wondered how {payload.topic} actually works?"
    if payload.language == "hi":
        hook = f"Kya aap jaante hain {payload.topic} asal mein kaise kaam karta hai?"
    script = {
        **payload.model_dump(),
        "hook": hook,
        "scenes": [
            {"scene": 1, "visual": "Opening visual / title card", "narration": hook},
            {"scene": 2, "visual": f"Illustration explaining {payload.topic}", "narration": f"Let's break down {payload.topic} in simple terms."},
            {"scene": 3, "visual": "Key takeaway and closing card", "narration": "Follow for more practical AI and technology explainers."},
        ],
        "full_text": "\n\n".join([hook, f"Let's break down {payload.topic} in simple terms.", "Follow for more practical AI and technology explainers."]),
        "generation_mode": "template_fallback",
        "provider_message": "This is a starter draft. Configure an AI provider for original, researched scripts.",
    }
    return save("script", script, "script_draft")

@app.post("/api/v1/videos")
def create_video(payload: VideoInput) -> dict[str, Any]:
    data = payload.model_dump()
    data.update({"asset_url": None, "thumbnail_url": None, "seo": {"title": payload.title, "description": payload.description, "tags": payload.tags}})
    return save("video", data, "video_review")

@app.post("/api/v1/videos/{video_id}/approve")
def approve_video(video_id: str, payload: DecisionInput) -> dict[str, Any]:
    item = get_record(video_id)
    if item["kind"] != "video":
        raise HTTPException(400, "Only video records can be approved")
    return change(video_id, status="approved", patch={"approval_note": payload.note, "approved_at": now()})

@app.post("/api/v1/videos/{video_id}/reject")
def reject_video(video_id: str, payload: DecisionInput) -> dict[str, Any]:
    item = get_record(video_id)
    if item["kind"] != "video":
        raise HTTPException(400, "Only video records can be rejected")
    return change(video_id, status="changes_requested", patch={"review_note": payload.note})

@app.post("/api/v1/publishing/{video_id}/schedule")
def schedule_video(video_id: str, payload: ScheduleInput) -> dict[str, Any]:
    item = get_record(video_id)
    if item["kind"] != "video":
        raise HTTPException(400, "Only videos can be scheduled")
    if item["status"] != "approved":
        raise HTTPException(409, "Publishing blocked: approve the final video and metadata first.")
    if not os.getenv("YOUTUBE_CLIENT_ID") or not os.getenv("YOUTUBE_CLIENT_SECRET"):
        raise HTTPException(503, "YouTube OAuth is not configured. Add credentials to the server environment.")
    raise HTTPException(501, "The YouTube OAuth token flow and upload worker must be implemented before live scheduling is enabled.")

@app.get("/api/v1/analytics/overview")
def analytics() -> dict[str, Any]:
    items = list_records()
    videos = [x for x in items if x["kind"] == "video"]
    return {
        "ideas": sum(x["kind"] == "idea" for x in items),
        "scripts": sum(x["kind"] == "script" for x in items),
        "videos": len(videos),
        "awaiting_review": sum(x["status"] == "video_review" for x in videos),
        "approved": sum(x["status"] == "approved" for x in videos),
        "scheduled": sum(x["status"] == "scheduled" for x in videos),
        "published": sum(x["status"] == "published" for x in videos),
        "views": 0,
        "watch_time_hours": 0,
        "note": "Connect YouTube Analytics OAuth to load real channel performance.",
    }

@app.get("/api/v1/settings")
def get_settings() -> dict[str, Any]:
    items = list_records("settings")
    return items[0]["data"] if items else SettingsInput().model_dump()

@app.put("/api/v1/settings")
def put_settings(payload: SettingsInput) -> dict[str, Any]:
    items = list_records("settings")
    if items:
        return change(items[0]["id"], patch=payload.model_dump())["data"]
    return save("settings", payload.model_dump(), "configured")["data"]

@app.get("/api/v1/automation/status")
def automation_status() -> dict[str, Any]:
    return {
        "worker": "not_configured",
        "queue": "redis",
        "steps": ["research", "script", "voice", "visuals", "render", "thumbnail", "seo", "human_review", "publish"],
        "approval_gate": "enforced_by_api",
        "message": "Background worker and external providers must be configured before unattended production.",
    }


# Optional real production adapters. Missing credentials fail explicitly instead of
# returning mock assets or claiming that a video was generated.
from fastapi.staticfiles import StaticFiles
from app.production import (
    MEDIA_ROOT,
    ProviderNotConfigured,
    generate_text,
    public_media_url,
    render_title_card,
    synthesize_voice,
)

app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")


class GenerateScriptInput(BaseModel):
    topic: str = Field(min_length=3, max_length=240)
    language: str = "en"
    format: str = "short"
    tone: str = "clear and engaging"
    audience: str = "Beginners"


class VoiceInput(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str | None = None


class RenderInput(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    duration_seconds: int = Field(default=5, ge=3, le=30)
    audio_url: str | None = None


@app.post("/api/v1/scripts/generate", tags=["production"])
async def generate_script(payload: GenerateScriptInput) -> dict[str, Any]:
    language_name = "Hindi" if payload.language == "hi" else "English"
    length = "a concise YouTube Short script (45-60 seconds)" if payload.format == "short" else "a detailed YouTube long-form script (6-10 minutes)"
    prompt = (
        f"Create {length} in {language_name} about: {payload.topic}. "
        f"Audience: {payload.audience}. Tone: {payload.tone}. "
        "Return a strong opening hook, scene-by-scene narration, visual direction, "
        "and a concise call to action. Avoid unsupported factual claims. "
        "Clearly mark facts that need source verification."
    )
    try:
        text = await generate_text(prompt, system="You are an expert bilingual YouTube scriptwriter. Write original, audience-friendly scripts.")
    except ProviderNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"AI provider request failed: {exc}") from exc
    return save("script", {**payload.model_dump(), "full_text": text, "generation_mode": "provider", "provider": "openai-compatible"}, "script_draft")


@app.post("/api/v1/voice/generate", tags=["production"])
async def generate_voice(payload: VoiceInput) -> dict[str, Any]:
    try:
        path = await synthesize_voice(payload.text, voice_id=payload.voice_id)
    except ProviderNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Voice provider request failed: {exc}") from exc
    return save("asset", {"asset_type": "voice", "file_name": path.name, "url": public_media_url(path), "mime_type": "audio/mpeg", "provider": "elevenlabs"}, "ready")


@app.post("/api/v1/render/title-card", tags=["production"])
def render_video_title_card(payload: RenderInput) -> dict[str, Any]:
    audio_path = None
    if payload.audio_url:
        if not payload.audio_url.startswith("/media/"):
            raise HTTPException(400, "audio_url must refer to an asset under /media/")
        audio_path = str(MEDIA_ROOT / Path(payload.audio_url).name)
    try:
        path = render_title_card(payload.title, duration_seconds=payload.duration_seconds, audio_path=audio_path)
    except ProviderNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except (ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(422, f"FFmpeg rendering failed: {exc}") from exc
    return save("asset", {"asset_type": "video", "file_name": path.name, "url": public_media_url(path), "mime_type": "video/mp4", "render_type": "title_card"}, "rendered")


@app.post("/api/v1/seo/generate", tags=["production"])
async def generate_seo(payload: GenerateScriptInput) -> dict[str, Any]:
    prompt = (
        f"Create YouTube metadata for a {payload.format} about {payload.topic} in "
        f"{'Hindi' if payload.language == 'hi' else 'English'}. Return JSON with "
        "title_options (3), description, tags (10), and hashtags (5). "
        "Do not promise rankings or invent facts."
    )
    try:
        text = await generate_text(prompt, system="You are a YouTube metadata editor. Return valid JSON only.")
    except ProviderNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"SEO provider request failed: {exc}") from exc
    try:
        metadata = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(502, "AI provider returned invalid JSON for SEO metadata.") from exc
    return save("seo", {**payload.model_dump(), "metadata": metadata}, "draft")
