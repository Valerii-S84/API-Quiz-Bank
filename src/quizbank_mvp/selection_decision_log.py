"""Persistence for selection decision evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .database_connection import utc_now


@dataclass(frozen=True)
class SelectionDecisionLog:
    selection_request_id: str
    delivery_id: str | None
    consumer_id: str
    delivery_mode: str
    selection_strategy: str
    filters: dict[str, object]
    filters_applied: list[str]
    candidate_count: int
    eligible_count: int
    selected_item_id: str | None
    selected_score: dict[str, float]
    selected_reason: str
    blocked_reason_counts: dict[str, int]
    fallback_reason_code: str | None

    def to_row(self) -> dict[str, object]:
        return {
            "selection_request_id": self.selection_request_id,
            "delivery_id": self.delivery_id,
            "consumer_id": self.consumer_id,
            "delivery_mode": self.delivery_mode,
            "selection_strategy": self.selection_strategy,
            "filters_json": stable_json(self.filters),
            "filters_applied_json": stable_json(self.filters_applied),
            "candidate_count": self.candidate_count,
            "eligible_count": self.eligible_count,
            "selected_item_id": self.selected_item_id,
            "selected_score_json": stable_json(self.selected_score),
            "selected_reason": self.selected_reason,
            "blocked_reason_counts_json": stable_json(self.blocked_reason_counts),
            "fallback_reason_code": self.fallback_reason_code,
            "created_at": utc_now(),
        }

    def to_context(self) -> dict[str, object]:
        return {
            "selection_request_id": self.selection_request_id,
            "candidate_count": self.candidate_count,
            "eligible_count": self.eligible_count,
            "selected_item_id": self.selected_item_id,
            "selected_score": self.selected_score,
            "selected_reason": self.selected_reason,
            "blocked_reason_counts": self.blocked_reason_counts,
            "fallback_reason_code": self.fallback_reason_code,
        }


def success_decision(
    selection_request_id: str,
    request: Any,
    delivery: dict[str, Any],
    item: dict[str, Any],
    candidate_count: int,
    eligible_count: int,
    blocked_reason_counts: dict[str, int],
) -> SelectionDecisionLog:
    return SelectionDecisionLog(
        selection_request_id=selection_request_id,
        delivery_id=str(delivery["delivery_id"]),
        consumer_id=request.consumer_id,
        delivery_mode=request.delivery_mode,
        selection_strategy=request.selection_strategy,
        filters=request.filters.to_context(),
        filters_applied=list(request.policy.hard_filters),
        candidate_count=candidate_count,
        eligible_count=eligible_count,
        selected_item_id=str(item["item_id"]),
        selected_score=dict(item.get("_selection_score", {})),
        selected_reason="selected_top_score",
        blocked_reason_counts=blocked_reason_counts,
        fallback_reason_code=None,
    )


def no_candidate_decision(
    selection_request_id: str,
    request: Any,
    candidate_count: int,
    blocked_reason_counts: dict[str, int],
) -> SelectionDecisionLog:
    return SelectionDecisionLog(
        selection_request_id=selection_request_id,
        delivery_id=None,
        consumer_id=request.consumer_id,
        delivery_mode=request.delivery_mode,
        selection_strategy=request.selection_strategy,
        filters=request.filters.to_context(),
        filters_applied=list(request.policy.hard_filters),
        candidate_count=candidate_count,
        eligible_count=0,
        selected_item_id=None,
        selected_score={},
        selected_reason="no_eligible_candidate",
        blocked_reason_counts=blocked_reason_counts,
        fallback_reason_code=request.policy.no_candidate_reason_code,
    )


def insert_selection_decision(connection, decision: SelectionDecisionLog) -> None:
    row = decision.to_row()
    connection.execute(
        """
        INSERT INTO selection_decisions (
            selection_request_id, delivery_id, consumer_id, delivery_mode,
            selection_strategy, filters_json, filters_applied_json, candidate_count,
            eligible_count, selected_item_id, selected_score_json, selected_reason,
            blocked_reason_counts_json, fallback_reason_code, created_at
        ) VALUES (
            :selection_request_id, :delivery_id, :consumer_id, :delivery_mode,
            :selection_strategy, :filters_json, :filters_applied_json, :candidate_count,
            :eligible_count, :selected_item_id, :selected_score_json, :selected_reason,
            :blocked_reason_counts_json, :fallback_reason_code, :created_at
        )
        """,
        row,
    )


def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
