"""Queue-first selection orchestration for precomputed selection queues."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .database_connection import connect, decode_json_field, row_to_dict
from .database_status import DELIVERABLE_STATUSES
from .problems import QuizBankProblem
from .projections import build_learner_quiz_projection
from .selection_decision_log import insert_selection_decision, success_decision
from .selection_delivery import answer_feedback, create_delivery
from .selection_models import SelectionRequest
from .selection_queue_filler import queue_scopes_for_request
from .selection_queue_models import selection_queue_id
from .selection_quota import reserve_quota
from .selection_scope import effective_scope_replacement, resolve_content_scope_request
from .selection_scope_enforcement import (
    enforce_consumer_scope,
    enforce_entitlement_scope,
    load_active_consumer,
    load_active_entitlement,
)
from .time_ids import new_id, utc_now


@dataclass(frozen=True)
class QueueSelectionContext:
    consumer: dict[str, Any]
    entitlement: dict[str, Any]
    request: SelectionRequest


@dataclass(frozen=True)
class QueueClaim:
    queue_item_id: str
    queue_id: str
    item_id: str
    score_snapshot: dict[str, Any]


def select_next_item_from_queue(db_path: Path | None, request: SelectionRequest) -> dict[str, Any]:
    selection_request_id = new_id("selreq")
    with connect(db_path) as connection:
        context = prepare_queue_selection_context(connection, request)
        claim = claim_next_queue_item(connection, context.request)
        quota_usage = reserve_quota(connection, context.consumer, context.request)
        item = load_claimed_item(connection, claim, context.request)
        delivery = create_delivery(
            connection,
            context.request,
            item,
            context.entitlement,
            quota_usage,
        )
        mark_queue_item_delivered(connection, claim, str(delivery["delivery_id"]))
        decision = success_decision(
            selection_request_id,
            context.request,
            delivery,
            item,
            1,
            1,
            {},
        )
        insert_selection_decision(connection, decision)
    return {
        "delivery": delivery,
        "quiz_item": build_learner_quiz_projection(item),
        "answer_feedback": answer_feedback(item),
        "selection_decision": decision.to_context(),
    }


def prepare_queue_selection_context(connection: Any, request: SelectionRequest) -> QueueSelectionContext:
    consumer = load_active_consumer(connection, request.consumer_id)
    entitlement = load_active_entitlement(connection, request)
    request = replace(request, **effective_scope_replacement(request, consumer, entitlement))
    request = resolve_content_scope_request(connection, request, consumer)
    enforce_consumer_scope(consumer, request)
    enforce_entitlement_scope(entitlement, request)
    return QueueSelectionContext(consumer, entitlement, request)


def claim_next_queue_item(connection: Any, request: SelectionRequest) -> QueueClaim:
    queue_ids = tuple(selection_queue_id(scope) for scope in queue_scopes_for_request(request))
    row = claim_next_queue_item_row(connection, request, queue_ids)
    if row is None:
        raise queue_not_ready_problem(request, queue_ids)
    claim = row_to_dict(row)
    return QueueClaim(
        str(claim["queue_item_id"]),
        str(claim["queue_id"]),
        str(claim["item_id"]),
        decoded_score_snapshot(claim["score_snapshot_json"]),
    )


def claim_next_queue_item_row(
    connection: Any,
    request: SelectionRequest,
    queue_ids: tuple[str, ...],
):
    now = utc_now()
    query = [claim_next_queue_item_sql(queue_ids, request.excluded_item_ids)]
    parameters: list[Any] = [
        new_id("selclaim"),
        now,
        now,
        *queue_ids,
        *DELIVERABLE_STATUSES,
    ]
    parameters.extend(request.excluded_item_ids)
    return connection.execute(" ".join(query), tuple(parameters)).fetchone()


def claim_next_queue_item_sql(
    queue_ids: tuple[str, ...],
    excluded_item_ids: tuple[str, ...],
) -> str:
    queue_placeholders = ", ".join("?" for _ in queue_ids)
    status_placeholders = ", ".join("?" for _ in DELIVERABLE_STATUSES)
    excluded_clause = ""
    if excluded_item_ids:
        excluded_placeholders = ", ".join("?" for _ in excluded_item_ids)
        excluded_clause = f"AND sqi.item_id NOT IN ({excluded_placeholders})"
    return f"""
        UPDATE selection_queue_items
        SET claim_status = 'claimed',
            claim_token = ?,
            claimed_at = ?,
            claim_expires_at = NULL,
            updated_at = ?
        WHERE queue_item_id = (
            SELECT sqi.queue_item_id
            FROM selection_queue_items sqi
            JOIN selection_queues sq ON sq.queue_id = sqi.queue_id
            JOIN quiz_items qi ON qi.item_id = sqi.item_id
            WHERE sqi.queue_id IN ({queue_placeholders})
              AND sq.queue_status IN ('ready', 'draining')
              AND sqi.claim_status = 'available'
              AND qi.status IN ({status_placeholders})
              AND qi.language_code = sq.language_code
              AND qi.content_bank_id = sq.content_bank_id
              AND qi.bank_version_id = sq.bank_version_id
              AND (sq.cefr_level = '' OR qi.sublevel = sq.cefr_level)
              AND (sq.theme_id = '' OR qi.theme_id = sq.theme_id)
              AND (sq.objective_id = '' OR qi.objective_id = sq.objective_id)
              AND (sq.pattern_id = '' OR qi.pattern_id = sq.pattern_id)
              {excluded_clause}
            ORDER BY sqi.position ASC, sqi.queue_item_id ASC
            LIMIT 1
        )
        RETURNING queue_item_id, queue_id, item_id, score_snapshot_json
    """


def load_claimed_item(
    connection: Any,
    claim: QueueClaim,
    request: SelectionRequest,
) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note,
               iq.theme_group, iq.image_quality_recommended,
               iq.image_quality_source, iq.image_quality_policy_share,
               iq.image_quality_override
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
        WHERE qi.item_id = ?
          AND qi.status IN (?, ?)
          AND qi.language_code = ?
          AND qi.content_bank_id = ?
          AND qi.bank_version_id = ?
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """,
        (
            claim.item_id,
            *DELIVERABLE_STATUSES,
            request.language_code,
            request.content_bank_id,
            request.bank_version_id,
        ),
    ).fetchone()
    if row is None:
        raise queue_not_ready_problem(request, (claim.queue_id,))
    return item_with_queue_score(row_to_dict(row), claim)


def item_with_queue_score(item: dict[str, Any], claim: QueueClaim) -> dict[str, Any]:
    score = claim.score_snapshot.get("selection_score", {})
    if not isinstance(score, dict):
        score = {}
    return {**item, "_selection_score": score}


def decoded_score_snapshot(value: Any) -> dict[str, Any]:
    snapshot = decode_json_field(value)
    if isinstance(snapshot, dict):
        return snapshot
    return {}


def mark_queue_item_delivered(connection: Any, claim: QueueClaim, delivery_id: str) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE selection_queue_items
        SET claim_status = 'delivered',
            delivery_id = ?,
            updated_at = ?
        WHERE queue_item_id = ? AND claim_status = 'claimed'
        """,
        (delivery_id, now, claim.queue_item_id),
    )
    connection.execute(
        """
        UPDATE selection_queues
        SET available_count = CASE
                WHEN available_count > 0 THEN available_count - 1
                ELSE 0
            END,
            queue_status = CASE
                WHEN available_count > 1 THEN queue_status
                ELSE 'warming'
            END,
            refill_after_at = CASE
                WHEN available_count > 1 THEN refill_after_at
                ELSE ?
            END,
            updated_at = ?
        WHERE queue_id = ?
        """,
        (now, now, claim.queue_id),
    )


def queue_not_ready_problem(
    request: SelectionRequest,
    queue_ids: tuple[str, ...],
) -> QuizBankProblem:
    return QuizBankProblem(
        503,
        "SELECTION_QUEUE_NOT_READY",
        "Selection queue is not ready",
        "No precomputed queue item is currently available for this request scope.",
        "https://api.quizbank.example/problems/selection-queue-not-ready",
        {
            "selection_context": {
                "consumer_id": request.consumer_id,
                "delivery_mode": request.delivery_mode,
                "consumer_profile": request.consumer_profile.to_context(),
                "filters": request.filter_context(),
                "content_scope": request.content_scope.to_context(),
                "queue_ids": list(queue_ids),
            }
        },
    )
