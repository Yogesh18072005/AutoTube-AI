from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_config_exposes_all_workspace_modules():
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    assert "approval" in response.json()["modules"]
    assert response.json()["publishing_requires_approval"] is True


def test_unapproved_video_cannot_be_scheduled(monkeypatch):
    monkeypatch.delenv("YOUTUBE_CLIENT_ID", raising=False)
    monkeypatch.delenv("YOUTUBE_CLIENT_SECRET", raising=False)
    video = client.post(
        "/api/v1/videos",
        json={"title": "Approval gate test", "language": "en", "format": "short"},
    )
    assert video.status_code == 200
    video_id = video.json()["id"]

    response = client.post(
        f"/api/v1/publishing/{video_id}/schedule",
        json={"scheduled_at": "2030-01-01T12:00:00Z"},
    )
    assert response.status_code == 409
    assert "approve" in response.json()["detail"].lower()


def test_approved_video_still_requires_youtube_credentials(monkeypatch):
    monkeypatch.delenv("YOUTUBE_CLIENT_ID", raising=False)
    monkeypatch.delenv("YOUTUBE_CLIENT_SECRET", raising=False)
    video = client.post("/api/v1/videos", json={"title": "OAuth test"})
    video_id = video.json()["id"]
    approved = client.post(f"/api/v1/videos/{video_id}/approve", json={"note": "Reviewed"})
    assert approved.status_code == 200
    response = client.post(
        f"/api/v1/publishing/{video_id}/schedule",
        json={"scheduled_at": "2030-01-01T12:00:00Z"},
    )
    assert response.status_code == 503
    assert "OAuth" in response.json()["detail"]
