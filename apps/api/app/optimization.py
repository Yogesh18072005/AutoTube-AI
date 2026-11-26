from __future__ import annotations

import re
from statistics import mean
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/v1/optimization", tags=["creator optimization"])

_WORD = re.compile(r"[\w']+", re.UNICODE)
_NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|x|k|m|minutes?|seconds?|hours?|days?)?\b", re.I)
_VAGUE = {"amazing", "incredible", "insane", "crazy", "ultimate", "best", "secret", "powerful", "huge"}
_FILLER = {"basically", "actually", "literally", "just", "really", "very", "today", "welcome", "guys"}
_STAKES = {"lose", "lost", "waste", "wasting", "fail", "risk", "cost", "mistake", "avoid", "stop", "before"}
_CURIOSITY = {"why", "how", "what", "which", "until", "before", "but", "reason", "nobody", "except"}


def _words(text: str) -> list[str]:
    return [word.lower() for word in _WORD.findall(text)]


def score_hook(text: str) -> dict[str, Any]:
    words = _words(text)
    if not words:
        return {"score": 0, "band": "weak", "dimensions": {}, "recommendations": ["Write an opening line before scoring it."], "disclaimer": "Heuristic feedback, not a prediction of views or retention."}
    numbers = len(_NUMBER.findall(text))
    vague = sum(word in _VAGUE for word in words)
    filler = sum(word in _FILLER for word in words)
    direct = sum(word in {"you", "your", "you're"} for word in words)
    stakes = sum(word in _STAKES for word in words)
    curiosity = sum(word in _CURIOSITY for word in words)
    count = len(words)
    dimensions = {
        "specificity": max(0, min(100, 45 + numbers * 18 - vague * 13 - filler * 5)),
        "audience_relevance": max(0, min(100, 35 + direct * 18)),
        "stakes": max(0, min(100, 30 + stakes * 18 + (10 if numbers else 0))),
        "curiosity": max(0, min(100, 30 + curiosity * 14 + (12 if text.strip().endswith("?") else 0))),
        "brevity": max(10, min(100, 100 - abs(count - 16) * 4)),
    }
    ordered = sorted(dimensions.values())
    score = round(0.65 * mean(ordered) + 0.35 * ordered[0])
    weakest = min(dimensions, key=dimensions.get)
    advice = {
        "specificity": "Replace broad adjectives with a concrete example, number, or named subject.",
        "audience_relevance": "Make the viewer's benefit or problem explicit.",
        "stakes": "Explain what the viewer risks missing or what changes after watching.",
        "curiosity": "Create a clear unanswered question without hiding the topic.",
        "brevity": "Tighten the opening so the main promise arrives sooner.",
    }
    return {
        "score": score,
        "band": "strong" if score >= 75 else "workable" if score >= 55 else "needs_revision",
        "dimensions": dimensions,
        "weakest_dimension": weakest,
        "recommendations": [advice[weakest]],
        "word_count": count,
        "disclaimer": "Heuristic editorial feedback only. It is not trained on your channel data and cannot predict views or retention.",
    }


def analyze_title(title: str, thumbnail_text: str = "") -> dict[str, Any]:
    clean = title.strip()
    words = _words(clean)
    issues: list[str] = []
    strengths: list[str] = []
    if len(clean) > 100:
        issues.append("Over YouTube's 100-character title limit.")
    elif len(clean) > 60:
        issues.append("May be truncated in desktop search; move the key subject earlier.")
    else:
        strengths.append("Within the commonly used 60-character desktop guideline.")
    if len(clean) > 40:
        issues.append("Check the first 40 characters carefully for mobile feed readability.")
    if sum(1 for part in clean.split() if len(part) > 2 and part.isupper()) > 2:
        issues.append("Too many all-caps words can look spammy.")
    vague = sorted(set(words) & _VAGUE)
    if vague:
        issues.append("Replace vague wording: " + ", ".join(vague) + ".")
    if not _NUMBER.search(clean):
        issues.append("Consider adding a meaningful number, date, or specific named subject when relevant.")
    thumb_words = set(_words(thumbnail_text)) - {"the", "a", "an", "and", "or", "to", "of", "in", "for", "your"}
    title_words = set(words) - {"the", "a", "an", "and", "or", "to", "of", "in", "for", "your"}
    overlap = sorted(title_words & thumb_words)
    if thumbnail_text.strip():
        if overlap:
            issues.append("Thumbnail repeats title wording: " + ", ".join(overlap) + ". Make the two elements complement each other.")
        if len(_words(thumbnail_text)) > 4:
            issues.append("Use fewer words on the thumbnail so it remains readable at feed size.")
        if not overlap:
            strengths.append("Title and thumbnail communicate different parts of the idea.")
    score = max(0, min(100, 100 - 14 * len(issues) + 5 * len(strengths)))
    return {"title": clean, "character_count": len(clean), "score": score, "issues": issues, "strengths": strengths, "title_thumbnail_overlap": overlap, "disclaimer": "Editorial checklist, not a click-through-rate prediction. Character guidance is approximate."}


class HookRequest(BaseModel):
    hook: str = Field(min_length=1, max_length=1000)


class TitleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    thumbnail_text: str = Field(default="", max_length=300)


class RetentionPoint(BaseModel):
    seconds: float = Field(ge=0)
    audience_percent: float = Field(ge=0, le=100)


class RetentionRequest(BaseModel):
    points: list[RetentionPoint] = Field(min_length=3, max_length=500)

    @field_validator("points")
    @classmethod
    def positions_must_increase(cls, points: list[RetentionPoint]) -> list[RetentionPoint]:
        if any(points[index].seconds <= points[index - 1].seconds for index in range(1, len(points))):
            raise ValueError("Retention positions must be strictly increasing.")
        return points


class TranscriptSegment(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("end_seconds")
    @classmethod
    def end_after_start(cls, value: float, info):
        start = info.data.get("start_seconds")
        if start is not None and value <= start:
            raise ValueError("Segment end_seconds must be greater than start_seconds.")
        return value


class ShortsRequest(BaseModel):
    segments: list[TranscriptSegment] = Field(min_length=1, max_length=1000)
    min_seconds: int = Field(default=20, ge=10, le=60)
    max_seconds: int = Field(default=60, ge=20, le=180)

    @field_validator("max_seconds")
    @classmethod
    def max_must_exceed_min(cls, value: int, info):
        minimum = info.data.get("min_seconds", 20)
        if value < minimum:
            raise ValueError("max_seconds must be greater than or equal to min_seconds.")
        return value


@router.post("/hook-score")
def hook_score(payload: HookRequest) -> dict[str, Any]:
    return score_hook(payload.hook)


@router.post("/title-check")
def title_check(payload: TitleRequest) -> dict[str, Any]:
    return analyze_title(payload.title, payload.thumbnail_text)


@router.post("/retention")
def retention_analysis(payload: RetentionRequest) -> dict[str, Any]:
    points = [point.model_dump() for point in payload.points]
    first = points[0]["audience_percent"]
    opening_cutoff = min(30.0, points[-1]["seconds"])
    opening_points = [point for point in points if point["seconds"] <= opening_cutoff]
    opening_end = opening_points[-1]["audience_percent"] if opening_points else first
    drops = []
    for previous, current in zip(points, points[1:]):
        lost = previous["audience_percent"] - current["audience_percent"]
        if lost > 0:
            drops.append({"from_seconds": previous["seconds"], "to_seconds": current["seconds"], "percentage_points_lost": round(lost, 2)})
    cliffs = sorted((drop for drop in drops if drop["percentage_points_lost"] >= 4), key=lambda item: item["percentage_points_lost"], reverse=True)[:5]
    middle = [drop["percentage_points_lost"] for drop in drops if drop["from_seconds"] > opening_cutoff]
    return {
        "data_points": len(points),
        "opening_loss_percentage_points": round(first - opening_end, 2),
        "ending_audience_percent": points[-1]["audience_percent"],
        "largest_drops": cliffs,
        "average_drop_per_interval_after_opening": round(mean(middle), 3) if middle else 0,
        "recommendations": [
            "Review the opening promise and deliver value earlier." if first - opening_end >= 20 else "The opening drop is not unusually large in this export; inspect the largest individual drops.",
            "Scrub to the listed timestamps and compare the spoken line, visual change, and pacing before deciding what to edit." if cliffs else "No sharp drop of 4 percentage points or more was detected between supplied samples.",
        ],
        "disclaimer": "Analysis describes the supplied export only. It does not identify why viewers left or establish a universal retention benchmark.",
    }


@router.post("/shorts-candidates")
def shorts_candidates(payload: ShortsRequest) -> dict[str, Any]:
    segments = sorted(payload.segments, key=lambda item: item.start_seconds)
    candidates: list[dict[str, Any]] = []
    for start_index, start in enumerate(segments):
        selected = []
        for segment in segments[start_index:]:
            selected.append(segment)
            duration = segment.end_seconds - start.start_seconds
            if duration > payload.max_seconds:
                break
            if duration < payload.min_seconds:
                continue
            text = " ".join(item.text.strip() for item in selected)
            words = _words(text)
            has_hook = bool(re.search(r"\b(why|how|what|mistake|secret|stop|never|three|3|one|1)\b", text, re.I))
            score = min(100, 35 + (20 if has_hook else 0) + min(25, len(words)) + (20 if 35 <= duration <= 55 else 10))
            candidates.append({
                "start_seconds": round(start.start_seconds, 2),
                "end_seconds": round(segment.end_seconds, 2),
                "duration_seconds": round(duration, 2),
                "score": score,
                "transcript": text,
                "suggestion": "Start with the strongest standalone sentence and add a concise on-screen title.",
            })
            break
    candidates.sort(key=lambda item: (item["score"], item["duration_seconds"]), reverse=True)
    # Remove near-duplicate windows that start within 10 seconds of a higher-ranked candidate.
    chosen = []
    for candidate in candidates:
        if all(abs(candidate["start_seconds"] - existing["start_seconds"]) >= 10 for existing in chosen):
            chosen.append(candidate)
        if len(chosen) == 10:
            break
    return {
        "candidates": chosen,
        "count": len(chosen),
        "disclaimer": "Candidates are transcript-based editing suggestions. Review context, rights, accuracy, and pacing before publishing.",
    }
