from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, HTTPException, Query

from app.advanced import _token_encryption_key

router = APIRouter(prefix="/api/v1/intelligence", tags=["creator-intelligence"])
DATA_ROOT = Path(os.getenv("AUTOTUBE_DATA_DIR", "/app/data"))
TOKEN_PATH = DATA_ROOT / ".youtube-token.enc"


def _metrics_totals(report: dict[str, Any]) -> dict[str, float]:
    headers = [item.get("name", "") for item in report.get("columnHeaders", [])]
    rows = report.get("rows", [])
    values = rows[0] if rows else []
    result: dict[str, float] = {}
    for name, value in zip(headers, values):
        try:
            result[name] = float(value)
        except (TypeError, ValueError):
            continue
    return result


def build_recommendations(current: dict[str, float], previous: dict[str, float], videos: list[dict[str, Any]]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    views = current.get("views", 0)
    prior_views = previous.get("views", 0)
    if prior_views > 0:
        change = (views - prior_views) / prior_views * 100
        if change <= -15:
            recommendations.append({"priority": "high", "title": "Views declined versus the previous period", "detail": f"Views changed by {change:.1f}%. Compare recent topics, upload cadence and packaging before making changes."})
        elif change >= 15:
            recommendations.append({"priority": "positive", "title": "Views increased versus the previous period", "detail": f"Views changed by {change:.1f}%. Review which recent videos contributed most and test related ideas."})
    watch = current.get("estimatedMinutesWatched", 0)
    if views > 0 and watch > 0:
        average = watch * 60 / views
        if average < 30:
            recommendations.append({"priority": "medium", "title": "Review early viewer value", "detail": f"Channel average view duration is {average:.0f} seconds for this period. Compare retention curves by video; this aggregate alone does not explain exits."})
    if videos:
        top = videos[0]
        title = str(top.get("title", "Top video"))[:100]
        recommendations.append({"priority": "positive", "title": "Study your strongest recent video", "detail": f'"{title}" leads the returned video report by views. Review its topic, opening and packaging; do not assume one result guarantees repeat performance.'})
    if not recommendations:
        recommendations.append({"priority": "info", "title": "Collect a longer baseline", "detail": "Connect your channel and compare complete reporting periods. Recommendations appear only when the available data supports them."})
    return recommendations


async def _authorized_reports(start_date: str, end_date: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not TOKEN_PATH.exists():
        raise HTTPException(401, "Connect a YouTube channel from Channels before using Creator Intelligence.")
    try:
        fernet = Fernet(_token_encryption_key().encode())
        tokens = json.loads(fernet.decrypt(TOKEN_PATH.read_bytes()))
    except (InvalidToken, ValueError, OSError) as exc:
        raise HTTPException(500, "Stored YouTube credentials could not be decrypted. Check the persistent token encryption key.") from exc
    async with httpx.AsyncClient(timeout=45) as client:
        if time.time() > tokens.get("expiry_date", 0) / 1000 - 60:
            if not tokens.get("refresh_token"):
                raise HTTPException(401, "YouTube authorization expired. Reconnect your channel.")
            refresh = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
                "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
                "refresh_token": tokens["refresh_token"],
                "grant_type": "refresh_token",
            })
            if refresh.is_error:
                raise HTTPException(401, "YouTube token refresh failed. Reconnect your channel.")
            refreshed = refresh.json()
            refreshed["expiry_date"] = int((time.time() + refreshed.get("expires_in", 3600)) * 1000)
            tokens.update(refreshed)
            TOKEN_PATH.write_bytes(fernet.encrypt(json.dumps(tokens).encode()))

        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        base = {"ids": "channel==MINE", "startDate": start_date, "endDate": end_date}
        summary_response = await client.get("https://youtubeanalytics.googleapis.com/v2/reports", params={
            **base, "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,comments,shares"
        }, headers=headers)
        if summary_response.is_error:
            raise HTTPException(summary_response.status_code, "YouTube Analytics could not return channel totals. Check OAuth consent and Analytics API access.")
        video_response = await client.get("https://youtubeanalytics.googleapis.com/v2/reports", params={
            **base, "dimensions": "video",
            "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments,shares",
            "sort": "-views", "maxResults": 50,
        }, headers=headers)
        if video_response.is_error:
            raise HTTPException(video_response.status_code, "YouTube Analytics returned channel totals but could not load the video breakdown.")
        return summary_response.json(), video_response.json()


@router.get("/channel")
async def channel_intelligence(
    start_date: str = Query(default_factory=lambda: (date.today() - timedelta(days=28)).isoformat()),
    end_date: str = Query(default_factory=lambda: (date.today() - timedelta(days=1)).isoformat()),
) -> dict[str, Any]:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        raise HTTPException(422, "Dates must use YYYY-MM-DD format.") from exc
    if start > end or (end - start).days > 365 or end >= date.today():
        raise HTTPException(422, "Choose a past date range of at most 366 days.")
    span = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=span - 1)
    current_report, video_report = await _authorized_reports(start.isoformat(), end.isoformat())
    previous_report, _ = await _authorized_reports(previous_start.isoformat(), previous_end.isoformat())
    current = _metrics_totals(current_report)
    previous = _metrics_totals(previous_report)
    headers = [item.get("name", "") for item in video_report.get("columnHeaders", [])]
    videos = []
    for row in video_report.get("rows", []):
        values = dict(zip(headers, row))
        videos.append({
            "video_id": values.get("video"),
            "views": values.get("views", 0),
            "watch_minutes": values.get("estimatedMinutesWatched", 0),
            "average_view_duration_seconds": values.get("averageViewDuration", 0),
            "subscribers_gained": values.get("subscribersGained", 0),
            "likes": values.get("likes", 0),
            "comments": values.get("comments", 0),
            "shares": values.get("shares", 0),
            "url": f"https://www.youtube.com/watch?v={values.get('video')}" if values.get("video") else None,
        })
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat(), "days": span},
        "previous_period": {"start_date": previous_start.isoformat(), "end_date": previous_end.isoformat()},
        "current": current,
        "previous": previous,
        "videos": videos,
        "recommendations": build_recommendations(current, previous, videos),
        "data_source": "YouTube Analytics API",
        "disclaimer": "Recommendations are evidence-led prompts, not causal explanations or predictions. Video rows contain only metrics returned for the connected channel.",
    }
