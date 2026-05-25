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
    connection.execute(
        """
        INSERT INTO deliveries (
            delivery_id, consumer_id, quiz_item_id, item_status, delivery_status,
            source_id, source_type, provenance_note, selection_reason_summary,
            selected_at, entitlement_id, quota_usage_id
        ) VALUES (?, ?, ?, ?, 'created', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            delivery_id,
            request.consumer_id,
            item["item_id"],
            item["status"],
            item["source_id"],
            item["resolved_source_type"],
            item["resolved_provenance_note"],
            request.policy.selection_reason_summary(),
            utc_now(),
            entitlement["entitlement_id"],
            quota_usage["quota_usage_id"],
        ),
    )
    row = connection.execute(
        "SELECT * FROM deliveries WHERE delivery_id = ?",
        (delivery_id,),
    ).fetchone()
    return delivery_projection(row_to_dict(row))


def delivery_projection(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "delivery_id": delivery["delivery_id"],
        "consumer_id": delivery["consumer_id"],
        "quiz_item_id": delivery["quiz_item_id"],
        "item_status": delivery["item_status"],
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
