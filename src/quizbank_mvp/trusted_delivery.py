"""Trusted consumer delivery helpers for answer-enabled quiz access."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .database_connection import connect, new_id, row_to_dict, utc_now
from .database_status import DELIVERABLE_STATUSES
from .problems import QuizBankProblem
from .projections import build_learner_quiz_projection
from .selection import (
    SelectionFilters,
    SelectionRequest,
    answer_feedback,
    delivery_projection,
    enforce_consumer_scope,
    enforce_entitlement_scope,
    load_active_consumer,
    load_active_entitlement,
)


SHORTS_FACTORY_BACKEND_CONSUMER_ID = "shorts_factory_backend"
DEUTSCH_TRAINER_BOT_CONSUMER_ID = "deutsch_trainer_bot"
ANSWER_ENABLED_CONSUMERS = {
    "website_quiz_teaser",
    DEUTSCH_TRAINER_BOT_CONSUMER_ID,
    SHORTS_FACTORY_BACKEND_CONSUMER_ID,
}
TRUSTED_ROUTE_CONSUMERS = {
    "website_quiz_teaser",
    SHORTS_FACTORY_BACKEND_CONSUMER_ID,
}
DELIVERY_OUTCOME_STATUSES = {"sent", "failed", "cancelled"}


def is_answer_enabled_consumer(consumer_id: str) -> bool:
    return consumer_id in ANSWER_ENABLED_CONSUMERS


def is_trusted_route_consumer(consumer_id: str) -> bool:
    return consumer_id in TRUSTED_ROUTE_CONSUMERS


def lookup_trusted_quiz_item(
    db_path: Path | None,
    item_id: str,
    consumer_id: str,
) -> dict[str, object]:
    ensure_trusted_route_consumer(consumer_id)
    with connect(db_path) as connection:
        consumer = load_active_consumer(connection, consumer_id)
        item = load_deliverable_item(connection, item_id)
        request = item_scope_request(consumer_id, item)
        entitlement = load_active_entitlement(connection, request)
        enforce_consumer_scope(consumer, request)
        enforce_entitlement_scope(entitlement, request)
    return {
        "quiz_item": build_learner_quiz_projection(item),
        "answer_feedback": answer_feedback(item),
    }


def record_delivery_outcome(
    db_path: Path | None,
    delivery_id: str,
    consumer_id: str,
    status: str,
    reason: str | None = None,
) -> dict[str, object]:
    ensure_trusted_route_consumer(consumer_id)
    ensure_delivery_outcome_status(status)
    with connect(db_path) as connection:
        delivery = load_consumer_delivery(connection, delivery_id, consumer_id)
        connection.execute(
            """
            UPDATE deliveries
            SET delivery_status = ?
            WHERE delivery_id = ? AND consumer_id = ?
            """,
            (status, delivery_id, consumer_id),
        )
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_id, actor, action, entity_type, entity_id, from_status,
                to_status, reason, created_at
            ) VALUES (?, ?, 'delivery_outcome', 'delivery', ?, ?, ?, ?, ?)
            """,
            (
                new_id("audit"),
                consumer_id,
                delivery_id,
                delivery["delivery_status"],
                status,
                reason or status,
                utc_now(),
            ),
        )
        updated = load_consumer_delivery(connection, delivery_id, consumer_id)
    return delivery_projection(updated)


def load_deliverable_item(connection, item_id: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note,
               iq.theme_group,
               iq.image_quality_recommended,
               iq.image_quality_source,
               iq.image_quality_policy_share,
               iq.image_quality_override
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
        WHERE qi.item_id = ?
          AND qi.status IN (?, ?)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """,
        (item_id, *DELIVERABLE_STATUSES),
    ).fetchone()
    if row is None:
        raise trusted_problem(
            404,
            "QUIZ_ITEM_NOT_FOUND",
            "Quiz item not found",
            "No approved or published quiz item is visible for this trusted lookup.",
        )
    return row_to_dict(row)


def item_scope_request(consumer_id: str, item: dict[str, Any]) -> SelectionRequest:
    return SelectionRequest(
        consumer_id=consumer_id,
        filters=SelectionFilters(
            cefr_level=str(item["sublevel"]),
            theme_ids=(str(item["theme_id"]),),
        ),
        delivery_mode="trusted_item_lookup",
    )


def load_consumer_delivery(connection, delivery_id: str, consumer_id: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT * FROM deliveries
        WHERE delivery_id = ? AND consumer_id = ?
        """,
        (delivery_id, consumer_id),
    ).fetchone()
    if row is None:
        raise trusted_problem(
            404,
            "DELIVERY_NOT_FOUND",
            "Delivery not found",
            "No delivery is visible for this consumer.",
        )
    return row_to_dict(row)


def ensure_trusted_route_consumer(consumer_id: str) -> None:
    if is_trusted_route_consumer(consumer_id):
        return
    raise trusted_problem(
        403,
        "TRUSTED_CONSUMER_REQUIRED",
        "Trusted consumer required",
        "This endpoint is available only to trusted route consumers.",
    )


def ensure_delivery_outcome_status(status: str) -> None:
    if status in DELIVERY_OUTCOME_STATUSES:
        return
    raise trusted_problem(
        400,
        "DELIVERY_OUTCOME_INVALID",
        "Delivery outcome invalid",
        "Delivery outcome must be sent, failed or cancelled.",
    )


def trusted_problem(status: int, reason_code: str, title: str, detail: str) -> QuizBankProblem:
    return QuizBankProblem(
        status,
        reason_code,
        title,
        detail,
        "https://api.quizbank.example/problems/trusted-delivery",
    )
