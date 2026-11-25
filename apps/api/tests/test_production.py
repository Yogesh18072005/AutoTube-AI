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
