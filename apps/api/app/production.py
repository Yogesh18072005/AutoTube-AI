from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

import httpx

API_ROOT = Path(__file__).resolve().parents[1]
MEDIA_ROOT = Path(os.getenv("AUTOTUBE_MEDIA_DIR", str(API_ROOT / "media")))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


class ProviderNotConfigured(RuntimeError):
    pass


async def generate_text(prompt: str, *, system: str = "You are a careful YouTube production assistant.") -> str:
    """Generate text through an OpenAI-compatible chat-completions endpoint."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ProviderNotConfigured("OPENAI_API_KEY is not configured on the API server.")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()


async def synthesize_voice(text: str, *, voice_id: str | None = None) -> Path:
    """Create an MP3 narration file using ElevenLabs; never fabricates a success response."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ProviderNotConfigured("ELEVENLABS_API_KEY is not configured on the API server.")
    selected_voice = voice_id or os.getenv("ELEVENLABS_VOICE_ID")
    if not selected_voice:
        raise ProviderNotConfigured("Set ELEVENLABS_VOICE_ID or provide a voice_id.")
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{selected_voice}",
            headers={"xi-api-key": api_key, "Accept": "audio/mpeg"},
            json={"text": text, "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")},
        )
        response.raise_for_status()
    target = MEDIA_ROOT / f"voice-{uuid.uuid4().hex}.mp3"
    target.write_bytes(response.content)
    return target


def render_title_card(title: str, *, duration_seconds: int = 5, audio_path: str | None = None) -> Path:
    """Render a simple branded 1080p title-card MP4; requires a local FFmpeg binary."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ProviderNotConfigured("FFmpeg was not found. Install FFmpeg and add it to PATH.")
    duration = max(3, min(duration_seconds, 30))
    safe_title = re.sub(r"[^\w .,!?-]", "", title).strip()[:100] or "AutoTube AI"
    draw_text = safe_title.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    output = MEDIA_ROOT / f"render-{uuid.uuid4().hex}.mp4"
    command = [
        ffmpeg, "-y", "-f", "lavfi", "-i",
        "color=c=#101a2b:s=1920x1080:r=30",
    ]
    if audio_path:
        source = Path(audio_path).resolve()
        if not source.is_file() or MEDIA_ROOT.resolve() not in source.parents:
            raise ValueError("Audio asset must be a file created inside the AutoTube media directory.")
        command += ["-i", str(source)]
    command += [
        "-vf",
        f"drawtext=text='{draw_text}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2",
        "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p",
    ]
    if audio_path:
        command += ["-c:a", "aac", "-shortest"]
    else:
        command += ["-an"]
    command.append(str(output))
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
    return output


def public_media_url(path: Path) -> str:
    return f"/media/{path.name}"
