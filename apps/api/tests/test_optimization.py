from fastapi.testclient import TestClient

from app.main import app
from app.optimization import analyze_title, score_hook

client = TestClient(app)


def test_hook_score_is_bounded_and_explains_limits():
    result = score_hook("You can save 30 minutes with this simple Python shortcut.")
    assert 0 <= result["score"] <= 100
    assert set(result["dimensions"]) == {"specificity", "audience_relevance", "stakes", "curiosity", "brevity"}
    assert "cannot predict views" in result["disclaimer"]


def test_title_checker_detects_thumbnail_overlap():
    result = analyze_title("Python automation in 5 minutes", "Python automation")
    assert result["title_thumbnail_overlap"] == ["automation", "python"]
    assert result["issues"]


def test_hook_endpoint():
    response = client.post("/api/v1/optimization/hook-score", json={"hook": "Why do most beginners struggle with Python?"})
    assert response.status_code == 200
    assert response.json()["band"] in {"strong", "workable", "needs_revision"}


def test_title_endpoint_validates_and_returns_feedback():
    response = client.post("/api/v1/optimization/title-check", json={"title": "Learn Python in 7 days", "thumbnail_text": "START HERE"})
    assert response.status_code == 200
    assert response.json()["character_count"] == len("Learn Python in 7 days")


def test_retention_endpoint_finds_large_drop():
    response = client.post("/api/v1/optimization/retention", json={"points": [
        {"seconds": 0, "audience_percent": 100},
        {"seconds": 15, "audience_percent": 92},
        {"seconds": 30, "audience_percent": 70},
        {"seconds": 45, "audience_percent": 66},
    ]})
    assert response.status_code == 200
    assert response.json()["opening_loss_percentage_points"] == 30
    assert response.json()["largest_drops"][0]["percentage_points_lost"] == 22


def test_retention_rejects_non_increasing_positions():
    response = client.post("/api/v1/optimization/retention", json={"points": [
        {"seconds": 0, "audience_percent": 100},
        {"seconds": 10, "audience_percent": 90},
        {"seconds": 10, "audience_percent": 80},
    ]})
    assert response.status_code == 422


def test_shorts_candidates_builds_clips_from_timestamped_transcript():
    response = client.post("/api/v1/optimization/shorts-candidates", json={"min_seconds": 10, "max_seconds": 30, "segments": [
        {"start_seconds": 0, "end_seconds": 6, "text": "Why does this Python trick work?"},
        {"start_seconds": 6, "end_seconds": 14, "text": "It removes repetitive steps from your workflow."},
        {"start_seconds": 14, "end_seconds": 24, "text": "Here is a quick example you can try."},
    ]})
    assert response.status_code == 200
    assert response.json()["count"] >= 1
    assert response.json()["candidates"][0]["duration_seconds"] >= 10
