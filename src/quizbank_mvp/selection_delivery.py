"""Delivery persistence and projection for selected quiz items."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .database_connection import connect, row_to_dict
from .problems import QuizBankProblem
from .time_ids import new_id, utc_now

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


def get_delivery(db_path: Path | None, delivery_id: str, consumer_id: str) -> dict[str, Any]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM deliveries
            WHERE delivery_id = ? AND consumer_id = ?
            """,
            (delivery_id, consumer_id),
        ).fetchone()
    if row is None:
        raise QuizBankProblem(
            404,
            "DELIVERY_NOT_FOUND",
            "Delivery not found",
            "No delivery is visible for this consumer.",
            "https://api.quizbank.example/problems/delivery-not-found",
        )
    return delivery_projection(row_to_dict(row))


def create_delivery(
    connection,
    request: "SelectionRequest",
    item: dict[str, Any],
    entitlement: dict[str, Any],
    quota_usage: dict[str, Any],
) -> dict[str, Any]:
    delivery_id = new_id("deliv")
    selected_at = utc_now()
    selection_reason = request.policy.selection_reason_summary()
    connection.execute(
        """
        INSERT INTO deliveries (
            delivery_id, consumer_id, quiz_item_id, item_status, delivery_status,
            language_code, content_bank_id, bank_version_id,
            source_id, source_type, provenance_note, selection_reason_summary,
            selected_at, entitlement_id, quota_usage_id
        ) VALUES (?, ?, ?, ?, 'created', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            delivery_id,
            request.consumer_id,
            item["item_id"],
            item["status"],
            request.language_code,
            request.content_bank_id,
            request.bank_version_id,
            item["source_id"],
            item["resolved_source_type"],
            item["resolved_provenance_note"],
            selection_reason,
            selected_at,
            entitlement["entitlement_id"],
            quota_usage["quota_usage_id"],
        ),
    )
    delivery = {
        "delivery_id": delivery_id,
        "consumer_id": request.consumer_id,
        "quiz_item_id": item["item_id"],
        "item_status": item["status"],
        "delivery_status": "created",
        "language_code": request.language_code,
        "content_bank_id": request.content_bank_id,
        "bank_version_id": request.bank_version_id,
        "selected_at": selected_at,
        "selection_reason_summary": selection_reason,
    }
    upsert_consumer_delivery_state(connection, request, delivery)
    return delivery_projection(delivery)


def upsert_consumer_delivery_state(
    connection,
    request: "SelectionRequest",
    delivery: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO consumer_delivery_state (
            consumer_id, channel_id, language_code, content_bank_id,
            bank_version_id, quiz_item_id, delivery_count, last_delivery_id,
            last_delivery_status, last_delivered_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        ON CONFLICT(
            consumer_id, channel_id, language_code, content_bank_id,
            bank_version_id, quiz_item_id
        ) DO UPDATE SET
            delivery_count = consumer_delivery_state.delivery_count + 1,
            last_delivery_id = excluded.last_delivery_id,
            last_delivery_status = excluded.last_delivery_status,
            last_delivered_at = excluded.last_delivered_at,
            updated_at = excluded.updated_at
        """,
        (
            delivery["consumer_id"],
            request.consumer_profile.delivery_channel,
            delivery["language_code"],
            delivery["content_bank_id"],
            delivery["bank_version_id"],
            delivery["quiz_item_id"],
            delivery["delivery_id"],
            delivery["delivery_status"],
            delivery["selected_at"],
            utc_now(),
        ),
    )


def update_consumer_delivery_state_status(
    connection,
    consumer_id: str,
    delivery_id: str,
    delivery_status: str,
) -> None:
    connection.execute(
        """
        UPDATE consumer_delivery_state
        SET last_delivery_status = ?, updated_at = ?
        WHERE consumer_id = ? AND last_delivery_id = ?
        """,
        (delivery_status, utc_now(), consumer_id, delivery_id),
    )


def delivery_projection(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "delivery_id": delivery["delivery_id"],
        "consumer_id": delivery["consumer_id"],
        "quiz_item_id": delivery["quiz_item_id"],
        "item_status": delivery["item_status"],
        "language_code": delivery["language_code"],
        "content_bank_id": delivery["content_bank_id"],
        "bank_version_id": delivery["bank_version_id"],
        "status": delivery["delivery_status"],
        "selected_at": delivery["selected_at"],
        "reason": delivery["selection_reason_summary"],
    }


def answer_feedback(item: dict[str, Any]) -> dict[str, str]:
    option_index = int(item["answer_key"]) + 1
    return {
        "correctAnswerId": f"option_{option_index}",
        "explanation": str(item["explanation"]).strip(),
    }
