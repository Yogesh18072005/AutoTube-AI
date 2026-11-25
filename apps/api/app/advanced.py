from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.production import MEDIA_ROOT, ProviderNotConfigured

router = APIRouter(prefix="/api/v1", tags=["advanced"])
DATA_ROOT = Path(os.getenv("AUTOTUBE_DATA_DIR", str(MEDIA_ROOT.parent / "data")))
DATA_ROOT.mkdir(parents=True, exist_ok=True)
TOKEN_PATH = DATA_ROOT / ".youtube-token.enc"


def _secret() -> str:
    value = os.getenv("AUTOTUBE_SECRET_KEY")
    if not value:
        raise ProviderNotConfigured("Set AUTOTUBE_SECRET_KEY on the API server.")
    return value


def _sign(value: str) -> str:
    return hmac.new(_secret().encode(), value.encode(), hashlib.sha256).hexdigest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _escape_drawtext(value: str) -> str:
    escaped = value.replace("\\\\", "\\\\\\\\")
    for character in [":", "'", ",", ";", "[", "]", "%"]:
        escaped = escaped.replace(character, "\\\\" + character)
    return escaped


def _jwt(payload: dict) -> str:
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(_secret().encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{signature}"


class Scene(BaseModel):
    narration: str = Field(min_length=1, max_length=3000)
    visual: str = Field(default="Technology background", max_length=240)
    seconds: int = Field(default=5, ge=2, le=30)


class RenderProject(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    scenes: list[Scene] = Field(min_length=1, max_length=30)
    captions: bool = True
    audio_url: str | None = None


class ThumbnailRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    subtitle: str = Field(default="", max_length=120)


class RegisterInput(BaseModel):
    email: str
    password: str = Field(min_length=12, max_length=128)


class LoginInput(BaseModel):
    email: str
    password: str


def _font(size: int):
    try:
        from PIL import ImageFont
        for candidate in ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, size)
        return ImageFont.load_default()
    except Exception:
        return None


@router.get("/research/trends")
async def youtube_trends(q: str = "artificial intelligence", region: str = "IN", language: str = "en"):
    key = os.getenv("YOUTUBE_DATA_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise HTTPException(503, "Set YOUTUBE_DATA_API_KEY or GOOGLE_API_KEY to retrieve live YouTube trend signals.")
    params = {"part": "snippet,statistics", "q": q, "type": "video", "order": "viewCount", "publishedAfter": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()-7*86400)), "regionCode": region, "relevanceLanguage": language, "maxResults": 20, "key": key}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://www.googleapis.com/youtube/v3/search", params=params)
        response.raise_for_status()
        payload = response.json()
        ids = [x["id"]["videoId"] for x in payload.get("items", []) if x.get("id", {}).get("videoId")]
        stats = {}
        if ids:
            detail = await client.get("https://www.googleapis.com/youtube/v3/videos", params={"part":"statistics,contentDetails","id":",".join(ids),"key":key})
            detail.raise_for_status()
            stats = {x["id"]: x.get("statistics", {}) for x in detail.json().get("items", [])}
    return {"query": q, "region": region, "window_days": 7, "items": [{"video_id": x["id"]["videoId"], "title": x["snippet"]["title"], "channel": x["snippet"]["channelTitle"], "published_at": x["snippet"]["publishedAt"], "url": "https://youtube.com/watch?v="+x["id"]["videoId"], "statistics": stats.get(x["id"]["videoId"], {})} for x in payload.get("items", []) if x.get("id", {}).get("videoId")]}


@router.post("/media/image")
async def generate_image(request: Request):
    body = await request.json()
    prompt = str(body.get("prompt", "")).strip()[:2000]
    if len(prompt) < 5:
        raise HTTPException(422, "Provide an image prompt of at least five characters.")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(503, "OPENAI_API_KEY is required for image generation.")
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post("https://api.openai.com/v1/images/generations", headers={"Authorization": f"Bearer {key}"}, json={"model": os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"), "prompt": prompt, "size": "1536x1024"})
        response.raise_for_status()
        result = response.json()
        item = result["data"][0]
        if item.get("b64_json"):
            raw = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            download = await client.get(item["url"])
            download.raise_for_status()
            raw = download.content
        else:
            raise HTTPException(502, "Image provider returned no image data.")
    path = MEDIA_ROOT / f"image-{uuid.uuid4().hex}.png"
    path.write_bytes(raw)
    return {"url": f"/media/{path.name}", "file_name": path.name, "provider": "openai"}


@router.post("/videos/render-project")
def render_project(payload: RenderProject):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise HTTPException(503, "Install FFmpeg and add it to PATH on the API server.")
    work = MEDIA_ROOT / f"job-{uuid.uuid4().hex}"
    work.mkdir()
    clips = []
    try:
        for index, scene in enumerate(payload.scenes):
            output = work / f"scene-{index:03}.mp4"
            title = _escape_drawtext(scene.visual[:180])
            command = [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=0x101a2b:s=1080x1920:r=30", "-vf", f"drawtext=text='{title}':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=0x00000099:boxborderw=24", "-t", str(scene.seconds), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)]
            subprocess.run(command, check=True, capture_output=True, timeout=180)
            clips.append(output)
        concat = work / "concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\\n" for p in clips), encoding="utf-8")
        silent_video = work / "silent.mp4"
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent_video)], check=True, capture_output=True, timeout=300)
        target = MEDIA_ROOT / f"video-{uuid.uuid4().hex}.mp4"
        if payload.audio_url:
            if not payload.audio_url.startswith("/media/"):
                raise HTTPException(400, "audio_url must refer to an asset under /media/.")
            audio_path = (MEDIA_ROOT / Path(payload.audio_url).name).resolve()
            if MEDIA_ROOT.resolve() not in audio_path.parents or not audio_path.is_file():
                raise HTTPException(404, "Narration audio asset was not found in the media directory.")
            subprocess.run(
                [ffmpeg, "-y", "-i", str(silent_video), "-i", str(audio_path),
                 "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                 "-shortest", "-movflags", "+faststart", str(target)],
                check=True, capture_output=True, timeout=300,
            )
        else:
            shutil.copy2(silent_video, target)
        return {"url": f"/media/{target.name}", "file_name": target.name, "scenes": len(clips), "status": "rendered", "audio_included": bool(payload.audio_url), "captions": "not_generated"}
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode(errors="replace")[-1200:]
        raise HTTPException(422, f"FFmpeg render failed: {detail}") from exc
    finally:
        shutil.rmtree(work, ignore_errors=True)


@router.post("/thumbnails/generate")
def generate_thumbnail(payload: ThumbnailRequest):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise HTTPException(503, "Install Pillow in the API environment to generate thumbnails.") from exc
    image = Image.new("RGB", (1280, 720), "#101a2b")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((48, 48, 1232, 672), radius=34, fill="#172b49", outline="#5d83c7", width=4)
    title_font, sub_font = _font(76), _font(38)
    words = payload.title.split()
    lines, current = [], ""
    for word in words:
        test = (current+" "+word).strip()
        if draw.textbbox((0,0), test, font=title_font)[2] > 1080 and current:
            lines.append(current); current=word
        else: current=test
    if current: lines.append(current)
    y = 260 - len(lines)*48
    for line in lines[:3]:
        box=draw.textbbox((0,0),line,font=title_font)
        draw.text(((1280-(box[2]-box[0]))/2,y),line,font=title_font,fill="white")
        y += 100
    if payload.subtitle:
        box=draw.textbbox((0,0),payload.subtitle,font=sub_font)
        draw.text(((1280-(box[2]-box[0]))/2,570),payload.subtitle,font=sub_font,fill="#a9c8ff")
    target=MEDIA_ROOT/f"thumbnail-{uuid.uuid4().hex}.png"
    image.save(target)
    return {"url":f"/media/{target.name}","file_name":target.name,"width":1280,"height":720}


@router.get("/auth/google/start")
def youtube_oauth_start():
    client_id=os.getenv("YOUTUBE_CLIENT_ID")
    redirect=os.getenv("YOUTUBE_REDIRECT_URI","http://localhost:8000/api/v1/auth/google/callback")
    if not client_id or not os.getenv("YOUTUBE_CLIENT_SECRET"):
        raise HTTPException(503,"Configure YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET.")
    try:
        state=f"{int(time.time())}.{secrets.token_urlsafe(24)}"
        signed=f"{state}.{_sign(state)}"
    except ProviderNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    params={"client_id":client_id,"redirect_uri":redirect,"response_type":"code","scope":"https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly","access_type":"offline","prompt":"consent","state":signed}
    return {"authorization_url":"https://accounts.google.com/o/oauth2/v2/auth?"+urlencode(params),"state":signed}


@router.get("/auth/google/callback")
async def youtube_oauth_callback(code: str, state: str):
    try:
        raw,signature=state.rsplit(".",1)
        timestamp,nonce=raw.split(".",1)
        if not hmac.compare_digest(signature,_sign(raw)): raise ValueError("bad signature")
        if abs(time.time()-int(timestamp)) > 600 or not nonce: raise ValueError("expired state")
    except Exception as exc:
        raise HTTPException(400,"Invalid OAuth state.") from exc
    async with httpx.AsyncClient(timeout=30) as client:
        response=await client.post("https://oauth2.googleapis.com/token",data={"code":code,"client_id":os.getenv("YOUTUBE_CLIENT_ID"),"client_secret":os.getenv("YOUTUBE_CLIENT_SECRET"),"redirect_uri":os.getenv("YOUTUBE_REDIRECT_URI","http://localhost:8000/api/v1/auth/google/callback"),"grant_type":"authorization_code"})
        response.raise_for_status()
        tokens=response.json()
        tokens["expiry_date"] = int((time.time() + tokens.get("expires_in", 3600)) * 1000)
    token_key=os.getenv("AUTOTUBE_TOKEN_ENCRYPTION_KEY")
    if not token_key:
        raise HTTPException(503,"OAuth completed but token storage is disabled. Configure AUTOTUBE_TOKEN_ENCRYPTION_KEY and retry authorization.")
    from cryptography.fernet import Fernet
    try:
        encryption_key=Fernet(token_key.encode())
        TOKEN_PATH.write_bytes(encryption_key.encrypt(json.dumps(tokens).encode()))
    except Exception as exc:
        raise HTTPException(500,"AUTOTUBE_TOKEN_ENCRYPTION_KEY must be a valid Fernet key.") from exc
    return {"connected":True,"message":"YouTube OAuth tokens stored encrypted on this API host. You may close this page."}


@router.get("/auth/google/status")
def youtube_oauth_status():
    if not TOKEN_PATH.exists():
        return {"connected": False, "provider": "youtube"}
    token_key = os.getenv("AUTOTUBE_TOKEN_ENCRYPTION_KEY")
    if not token_key:
        return {"connected": False, "provider": "youtube", "reason": "token_encryption_not_configured"}
    from cryptography.fernet import Fernet, InvalidToken
    try:
        tokens = json.loads(Fernet(token_key.encode()).decrypt(TOKEN_PATH.read_bytes()))
    except (InvalidToken, ValueError):
        return {"connected": False, "provider": "youtube", "reason": "stored_token_unreadable"}
    return {
        "connected": bool(tokens.get("refresh_token") or tokens.get("access_token")),
        "provider": "youtube",
        "expires_at": tokens.get("expiry_date"),
    }


@router.get("/analytics/youtube")
async def youtube_analytics(start_date: str, end_date: str):
    if not TOKEN_PATH.exists():
        raise HTTPException(401,"Connect a YouTube channel using /api/v1/auth/google/start.")
    token_key=os.getenv("AUTOTUBE_TOKEN_ENCRYPTION_KEY")
    if not token_key: raise HTTPException(503,"Token encryption key is not configured.")
    from cryptography.fernet import Fernet, InvalidToken
    try:
        fernet=Fernet(token_key.encode())
        tokens=json.loads(fernet.decrypt(TOKEN_PATH.read_bytes()))
    except (InvalidToken, ValueError) as exc:
        raise HTTPException(500,"Stored OAuth token could not be decrypted. Check AUTOTUBE_TOKEN_ENCRYPTION_KEY.") from exc
    async with httpx.AsyncClient(timeout=40) as client:
        if time.time()>tokens.get("expiry_date",0)/1000-60:
            refresh=await client.post("https://oauth2.googleapis.com/token",data={"client_id":os.getenv("YOUTUBE_CLIENT_ID"),"client_secret":os.getenv("YOUTUBE_CLIENT_SECRET"),"refresh_token":tokens.get("refresh_token"),"grant_type":"refresh_token"})
            refresh.raise_for_status(); refreshed=refresh.json(); refreshed["expiry_date"]=int((time.time()+refreshed.get("expires_in",3600))*1000); tokens.update(refreshed); TOKEN_PATH.write_bytes(fernet.encrypt(json.dumps(tokens).encode()))
        response=await client.get("https://youtubeanalytics.googleapis.com/v2/reports",params={"ids":"channel==MINE","startDate":start_date,"endDate":end_date,"metrics":"views,estimatedMinutesWatched,averageViewDuration,subscribersGained","dimensions":"day"},headers={"Authorization":f"Bearer {tokens['access_token']}"})
        response.raise_for_status()
        return response.json()


@router.post("/auth/register")
def register_user(payload: RegisterInput):
    # Password hashing is deliberately delegated to bcrypt; no plaintext credentials are persisted.
    try:
        from pwdlib import PasswordHash
    except ImportError as exc:
        raise HTTPException(503,"Install pwdlib[argon2] to enable local account authentication.") from exc
    from app.main import save
    existing=[x for x in __import__("app.main",fromlist=["list_records"]).list_records("user") if x["data"].get("email","").lower()==payload.email.lower()]
    if existing: raise HTTPException(409,"An account with this email already exists.")
    record=save("user",{"email":payload.email.lower(),"password_hash":PasswordHash.recommended().hash(payload.password)},"active")
    return {"user_id":record["id"],"email":payload.email.lower(),"access_token":_jwt({"sub":record["id"],"exp":int(time.time())+3600}),"token_type":"bearer"}


@router.post("/auth/login")
def login_user(payload: LoginInput):
    try:
        from pwdlib import PasswordHash
    except ImportError as exc:
        raise HTTPException(503,"Install pwdlib[argon2] to enable local account authentication.") from exc
    from app.main import list_records
    users=[x for x in list_records("user") if x["data"].get("email","").lower()==payload.email.lower()]
    if not users or not PasswordHash.recommended().verify(payload.password,users[0]["data"]["password_hash"]):
        raise HTTPException(401,"Invalid email or password.")
    user=users[0]
    return {"user_id":user["id"],"email":payload.email.lower(),"access_token":_jwt({"sub":user["id"],"exp":int(time.time())+3600}),"token_type":"bearer"}


class YouTubeUploadInput(BaseModel):
    video_id: str
    privacy_status: str = Field(default="private", pattern="^(private|unlisted|public)$")
    publish_at: str | None = None


@router.post("/publishing/youtube/upload")
async def upload_approved_video(payload: YouTubeUploadInput):
    from app.main import get_record, change
    video=get_record(payload.video_id)
    if video["kind"]!="video" or video["status"]!="approved":
        raise HTTPException(409,"Publishing blocked: approve this exact final video before upload.")
    data=video["data"]
    asset_url=data.get("asset_url")
    if not asset_url or not asset_url.startswith("/media/"):
        raise HTTPException(422,"The approved video record must reference a rendered /media/ asset.")
    asset=(MEDIA_ROOT/Path(asset_url).name).resolve()
    if MEDIA_ROOT.resolve() not in asset.parents or not asset.is_file():
        raise HTTPException(404,"Rendered video asset was not found on this API host.")
    if not TOKEN_PATH.exists():
        raise HTTPException(401,"Connect a YouTube channel before uploading.")
    token_key=os.getenv("AUTOTUBE_TOKEN_ENCRYPTION_KEY")
    if not token_key: raise HTTPException(503,"Token encryption key is not configured.")
    from cryptography.fernet import Fernet
    try: tokens=json.loads(Fernet(token_key.encode()).decrypt(TOKEN_PATH.read_bytes()))
    except Exception as exc: raise HTTPException(500,"Stored YouTube credentials could not be decrypted.") from exc
    async with httpx.AsyncClient(timeout=180) as client:
        if time.time()>tokens.get("expiry_date",0)/1000-60:
            refresh=await client.post("https://oauth2.googleapis.com/token",data={"client_id":os.getenv("YOUTUBE_CLIENT_ID"),"client_secret":os.getenv("YOUTUBE_CLIENT_SECRET"),"refresh_token":tokens.get("refresh_token"),"grant_type":"refresh_token"})
            refresh.raise_for_status(); refreshed=refresh.json(); refreshed["expiry_date"]=int((time.time()+refreshed.get("expires_in",3600))*1000); tokens.update(refreshed)
            TOKEN_PATH.write_bytes(Fernet(token_key.encode()).encrypt(json.dumps(tokens).encode()))
        metadata={"snippet":{"title":str(data.get("title","AutoTube AI video"))[:100],"description":str(data.get("description",""))[:5000],"tags":data.get("tags",[])[:500],"categoryId":"28"},"status":{"privacyStatus":payload.privacy_status}}
        if payload.publish_at:
            if payload.privacy_status!="private": raise HTTPException(422,"Scheduled publication must remain private until YouTube publishAt is applied.")
            metadata["status"]["publishAt"]=payload.publish_at
        init=await client.post("https://www.googleapis.com/upload/youtube/v3/videos",params={"uploadType":"resumable","part":"snippet,status"},headers={"Authorization":f"Bearer {tokens['access_token']}","Content-Type":"application/json; charset=UTF-8","X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(asset.stat().st_size)},json=metadata)
        init.raise_for_status()
        upload_url=init.headers.get("location")
        if not upload_url: raise HTTPException(502,"YouTube did not return a resumable upload URL.")
        with asset.open("rb") as stream:
            uploaded=await client.put(upload_url,content=stream.read(),headers={"Authorization":f"Bearer {tokens['access_token']}","Content-Type":"video/mp4","Content-Length":str(asset.stat().st_size)})
        uploaded.raise_for_status()
        result=uploaded.json()
    scheduled = bool(payload.publish_at)
    status = "scheduled" if scheduled else "published"
    change(payload.video_id,status=status,patch={"youtube_video_id":result.get("id"),"youtube_url":f"https://youtube.com/watch?v={result.get('id')}","scheduled_for":payload.publish_at,"published_at":None if scheduled else now()})
    return {"status":status,"youtube_video_id":result.get("id"),"url":f"https://youtube.com/watch?v={result.get('id')}"}
