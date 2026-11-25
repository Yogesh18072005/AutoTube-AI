from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_real_script_generation_requires_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/v1/scripts/generate",
        json={"topic": "AI agents", "language": "en", "format": "short"},
    )
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_voice_generation_requires_provider(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    response = client.post(
        "/api/v1/voice/generate",
        json={"text": "Hello from AutoTube AI"},
    )
    assert response.status_code == 503
    assert "ELEVENLABS_API_KEY" in response.json()["detail"]


def test_render_requires_ffmpeg_when_unavailable(monkeypatch):
    from app import production

    monkeypatch.setattr(production.shutil, "which", lambda _: None)
    response = client.post(
        "/api/v1/render/title-card",
        json={"title": "AutoTube AI", "duration_seconds": 5},
    )
    assert response.status_code == 503
    assert "FFmpeg" in response.json()["detail"]

def test_automation_worker_fails_clearly_without_ai_credentials(monkeypatch):
    import pytest
    from app.worker import execute_pipeline

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        execute_pipeline.run({"topic": "AI agents", "language": "en", "format": "short"})


def test_youtube_oauth_status_never_exposes_tokens():
    response = client.get("/api/v1/auth/google/status")
    assert response.status_code == 200
    payload = response.json()
    assert "connected" in payload
    assert "access_token" not in payload
    assert "refresh_token" not in payload
