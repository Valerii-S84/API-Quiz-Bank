"""Weighted candidate ranking for selection."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


FRESHNESS_WINDOW_DAYS = 30
NEUTRAL_SCORE = 0.5
JITTER_WEIGHT = 0.001


@dataclass(frozen=True)
class CandidateScore:
    total: float
    coverage: float
    freshness: float
    quality: float
    delivery_penalty: float
    target_mix: float
    jitter: float

    def to_context(self) -> dict[str, float]:
        return {
            "total": round(self.total, 6),
            "coverage": round(self.coverage, 6),
            "freshness": round(self.freshness, 6),
            "quality": round(self.quality, 6),
            "delivery_penalty": round(self.delivery_penalty, 6),
            "target_mix": round(self.target_mix, 6),
            "jitter": round(self.jitter, 6),
        }


def select_ranked_candidate(candidates: list[dict[str, Any]], request: Any) -> dict[str, Any] | None:
    if not candidates:
        return None
    if request.selection_strategy == "first_eligible":
        return sorted(candidates, key=lambda item: str(item["item_id"]))[0]
    scored = [(candidate_score(candidate, request), candidate) for candidate in candidates]
    score, candidate = max(scored, key=lambda scored_item: (scored_item[0].total, str(scored_item[1]["item_id"])))
    ranked = dict(candidate)
    ranked["_selection_score"] = score.to_context()
    return ranked


def candidate_score(candidate: dict[str, Any], request: Any) -> CandidateScore:
    coverage = inverse_count_score(candidate.get("cell_delivery_count"))
    freshness = freshness_score(candidate.get("last_delivered_at"))
    quality = quality_score(candidate)
    delivery_penalty = inverse_count_score(candidate.get("delivery_count"))
    target = target_mix_score(candidate, request.target_mix)
    jitter = deterministic_jitter(str(request.consumer_id), str(candidate["item_id"]))
    total = (
        coverage * 0.35
        + freshness * 0.20
        + quality * 0.20
        + delivery_penalty * 0.15
        + target * 0.10
        + jitter
    )
    return CandidateScore(total, coverage, freshness, quality, delivery_penalty, target, jitter)


def inverse_count_score(value: Any) -> float:
    try:
        count = max(0, int(value or 0))
    except (TypeError, ValueError):
        return NEUTRAL_SCORE
    return 1.0 / (1.0 + count)


def freshness_score(value: Any) -> float:
    delivered_at = parse_timestamp(str(value or ""))
    if delivered_at is None:
        return 1.0
    age_days = max(0.0, (datetime.now(UTC) - delivered_at).total_seconds() / 86400)
    return min(1.0, age_days / FRESHNESS_WINDOW_DAYS)


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def quality_score(candidate: dict[str, Any]) -> float:
    raw_score = candidate.get("quality_score", NEUTRAL_SCORE)
    try:
        return min(1.0, max(0.0, float(raw_score)))
    except (TypeError, ValueError):
        return NEUTRAL_SCORE


def target_mix_score(candidate: dict[str, Any], target_mix: Any) -> float:
    scores = [
        axis_score(target_mix.level_weights, candidate.get("sublevel")),
        axis_score(target_mix.theme_weights, candidate.get("theme_id")),
        axis_score(target_mix.objective_weights, candidate.get("objective_id")),
        axis_score(target_mix.pattern_weights, candidate.get("pattern_id")),
    ]
    active_scores = [score for score in scores if score is not None]
    if not active_scores:
        return NEUTRAL_SCORE
    return sum(active_scores) / len(active_scores)


def axis_score(weights: dict[str, float], value: Any) -> float | None:
    if not weights:
        return None
    try:
        return min(1.0, max(0.0, float(weights.get(str(value), 0.0))))
    except (TypeError, ValueError):
        return 0.0


def deterministic_jitter(consumer_id: str, item_id: str) -> float:
    digest = hashlib.sha256(f"{consumer_id}:{item_id}".encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) / 0xFFFFFFFF) * JITTER_WEIGHT
