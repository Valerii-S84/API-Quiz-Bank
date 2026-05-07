"""Selection, entitlement and delivery rules for the MVP runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database import (
    DELIVERABLE_STATUSES,
    connect,
    new_id,
    row_to_dict,
    today_usage_date,
    utc_now,
)


class QuizBankProblem(Exception):
    def __init__(
        self,
        status: int,
        reason_code: str,
        title: str,
        detail: str,
        problem_type: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.reason_code = reason_code
        self.title = title
        self.detail = detail
        self.problem_type = problem_type
        self.extra = extra or {}

    def to_problem_details(self) -> dict[str, Any]:
        return {
            "type": self.problem_type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "reason_code": self.reason_code,
            **self.extra,
        }


@dataclass(frozen=True)
class SelectionRequest:
    consumer_id: str
    cefr_level: str | None = None
    theme_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()


def select_next_item(db_path: Path | None, request: SelectionRequest) -> dict[str, Any]:
    with connect(db_path) as connection:
        consumer = load_active_consumer(connection, request.consumer_id)
        entitlement = load_active_entitlement(connection, request)
        enforce_consumer_scope(consumer, request)
        enforce_entitlement_scope(entitlement, request)
        quota_usage = reserve_quota(connection, consumer)
        item = find_eligible_item(connection, request)
        if item is None:
            raise no_eligible_problem(request)
        delivery = create_delivery(connection, request.consumer_id, item, entitlement, quota_usage)
    return {"delivery": delivery, "quiz_item": public_projection(item)}


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


def load_active_consumer(connection, consumer_id: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT * FROM consumers WHERE consumer_id = ? AND status = 'active'",
        (consumer_id,),
    ).fetchone()
    if row is None:
        raise QuizBankProblem(
            403,
            "CONSUMER_NOT_ACTIVE",
            "Consumer is not active",
            "The consumer is missing or inactive.",
            "https://api.quizbank.example/problems/consumer-not-active",
        )
    return row_to_dict(row)


def load_active_entitlement(connection, request: SelectionRequest) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT * FROM entitlements
        WHERE consumer_id = ?
          AND feature = 'quiz_delivery'
          AND status = 'active'
          AND (valid_until IS NULL OR valid_until >= ?)
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (request.consumer_id, utc_now()),
    ).fetchone()
    if row is None:
        raise QuizBankProblem(
            403,
            "ENTITLEMENT_MISSING_FEATURE",
            "Entitlement missing",
            "This consumer is not entitled to quiz delivery.",
            "https://api.quizbank.example/problems/entitlement-missing",
        )
    return row_to_dict(row)


def enforce_consumer_scope(consumer: dict[str, Any], request: SelectionRequest) -> None:
    enforce_scope_list(
        json.loads(consumer["allowed_cefr_levels_json"]),
        [request.cefr_level] if request.cefr_level else [],
        "CONSUMER_LEVEL_NOT_ALLOWED",
    )
    enforce_scope_list(
        json.loads(consumer["allowed_theme_ids_json"]),
        list(request.theme_ids),
        "CONSUMER_THEME_NOT_ALLOWED",
    )


def enforce_entitlement_scope(entitlement: dict[str, Any], request: SelectionRequest) -> None:
    enforce_scope_list(
        json.loads(entitlement["allowed_cefr_levels_json"]),
        [request.cefr_level] if request.cefr_level else [],
        "ENTITLEMENT_LEVEL_NOT_ALLOWED",
    )
    enforce_scope_list(
        json.loads(entitlement["allowed_theme_ids_json"]),
        list(request.theme_ids),
        "ENTITLEMENT_THEME_NOT_ALLOWED",
    )


def enforce_scope_list(allowed: list[str], requested: list[str], reason_code: str) -> None:
    if not requested or not allowed:
        return
    denied = [value for value in requested if value not in allowed]
    if denied:
        raise QuizBankProblem(
            403,
            reason_code,
            "Request is outside allowed scope",
            "The requested quiz scope is not allowed for this consumer.",
            "https://api.quizbank.example/problems/entitlement-scope-denied",
            {"denied_values": denied},
        )


def reserve_quota(connection, consumer: dict[str, Any]) -> dict[str, Any]:
    usage_date = today_usage_date()
    row = load_quota_usage(connection, consumer["consumer_id"], usage_date)
    used_count = 0 if row is None else int(row["used_count"])
    quota_limit = int(consumer["daily_quota_limit"])
    if used_count >= quota_limit:
        raise quota_exceeded_problem(used_count, quota_limit)
    quota_usage_id = row["quota_usage_id"] if row else new_id("quota")
    upsert_quota_usage(connection, consumer, usage_date, quota_usage_id, used_count + 1)
    return {"quota_usage_id": quota_usage_id}


def load_quota_usage(connection, consumer_id: str, usage_date: str):
    row = connection.execute(
        """
        SELECT * FROM quota_usage
        WHERE consumer_id = ? AND feature = 'quiz_delivery' AND usage_date = ?
        """,
        (consumer_id, usage_date),
    ).fetchone()
    return row


def quota_exceeded_problem(used_count: int, quota_limit: int) -> QuizBankProblem:
    return QuizBankProblem(
        429,
        "QUOTA_EXCEEDED",
        "Quota exceeded",
        "This consumer has reached the configured delivery quota.",
        "https://api.quizbank.example/problems/quota-exceeded",
        {"quota": {"used": used_count, "limit": quota_limit, "window": "day"}},
    )


def upsert_quota_usage(
    connection,
    consumer: dict[str, Any],
    usage_date: str,
    quota_usage_id: str,
    next_used_count: int,
) -> None:
    connection.execute(
        """
        INSERT INTO quota_usage (
            quota_usage_id, consumer_id, feature, usage_date, used_count,
            quota_limit, updated_at
        ) VALUES (?, ?, 'quiz_delivery', ?, ?, ?, ?)
        ON CONFLICT(consumer_id, feature, usage_date) DO UPDATE SET
            used_count = excluded.used_count,
            quota_limit = excluded.quota_limit,
            updated_at = excluded.updated_at
        """,
        (
            quota_usage_id,
            consumer["consumer_id"],
            usage_date,
            next_used_count,
            int(consumer["daily_quota_limit"]),
            utc_now(),
        ),
    )


def find_eligible_item(connection, request: SelectionRequest) -> dict[str, Any] | None:
    query = [
        """
        SELECT qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        WHERE qi.status IN (?, ?)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
          AND NOT EXISTS (
              SELECT 1 FROM deliveries d
              WHERE d.consumer_id = ?
                AND d.quiz_item_id = qi.item_id
                AND d.delivery_status IN ('created', 'delivered', 'reserved')
          )
        """
    ]
    parameters: list[Any] = [*DELIVERABLE_STATUSES, request.consumer_id]
    append_filter(query, parameters, "qi.sublevel = ?", request.cefr_level)
    append_in_filter(query, parameters, "qi.theme_id", request.theme_ids)
    append_in_filter(query, parameters, "qi.objective_id", request.objective_ids)
    append_in_filter(query, parameters, "qi.pattern_id", request.pattern_ids)
    query.append("ORDER BY qi.item_id ASC LIMIT 1")
    row = connection.execute(" ".join(query), parameters).fetchone()
    return None if row is None else row_to_dict(row)


def append_filter(query: list[str], parameters: list[Any], clause: str, value: Any) -> None:
    if value is None:
        return
    query.append(f"AND {clause}")
    parameters.append(value)


def append_in_filter(
    query: list[str],
    parameters: list[Any],
    column: str,
    values: tuple[str, ...],
) -> None:
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    query.append(f"AND {column} IN ({placeholders})")
    parameters.extend(values)


def create_delivery(
    connection,
    consumer_id: str,
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
            consumer_id,
            item["item_id"],
            item["status"],
            item["source_id"],
            item["resolved_source_type"],
            item["resolved_provenance_note"],
            "eligible_by_status_level_theme_traceability_entitlement_quota",
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


def public_projection(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": item["item_id"],
        "language": item["language"],
        "cefr_level": item["sublevel"],
        "theme_id": item["theme_id"],
        "objective_id": item["objective_id"],
        "pattern_id": item["pattern_id"],
        "prompt": item["prompt"],
        "stem_text": item["stem_text"],
        "options": json.loads(item["options_json"]),
        "source_traceability": {
            "source_id": item["source_id"],
            "source_type": item["resolved_source_type"],
            "provenance_note": item["resolved_provenance_note"],
        },
    }


def delivery_projection(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "delivery_id": delivery["delivery_id"],
        "consumer_id": delivery["consumer_id"],
        "quiz_item_id": delivery["quiz_item_id"],
        "item_status": delivery["item_status"],
        "status": delivery["delivery_status"],
        "selected_at": delivery["selected_at"],
        "source_traceability": {
            "source_id": delivery["source_id"],
            "source_type": delivery["source_type"],
            "provenance_note": delivery["provenance_note"],
        },
        "reason": delivery["selection_reason_summary"],
    }


def no_eligible_problem(request: SelectionRequest) -> QuizBankProblem:
    return QuizBankProblem(
        404,
        "SELECTION_NO_ELIGIBLE_ITEM",
        "No eligible quiz item",
        "No item satisfies the selection constraints.",
        "https://api.quizbank.example/problems/no-eligible-item",
        {
            "selection_context": {
                "consumer_id": request.consumer_id,
                "cefr_level": request.cefr_level,
                "theme_ids": list(request.theme_ids),
                "objective_ids": list(request.objective_ids),
                "pattern_ids": list(request.pattern_ids),
                "filters_applied": [
                    "status",
                    "cefr_level",
                    "theme_id",
                    "source_traceability",
                    "repeat_policy",
                    "entitlement",
                    "quota",
                ],
            }
        },
    )
