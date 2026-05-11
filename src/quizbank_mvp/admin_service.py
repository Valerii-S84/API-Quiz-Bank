"""Admin read models and audited control operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .database import (
    connect,
    new_id,
    row_to_dict,
    seed_api_credential,
    seed_consumer,
    seed_entitlement,
    transition_consumer_status,
    transition_item_status,
    utc_now,
)
from .projections import admin_quiz_projection
from .selection import QuizBankProblem


ITEM_STATUSES = (
    "draft",
    "imported",
    "normalized",
    "needs_review",
    "approved",
    "published",
    "monitored",
    "retired",
    "blocked",
)
STATUS_ACTIONS = {
    "approve": "approved",
    "publish": "published",
    "retire": "retired",
    "block": "blocked",
}
CONSUMER_KINDS = ("api_client", "telegram_channel", "telegram_bot", "teacher", "school")


def list_admin_quiz_items(
    db_path: Path | None,
    filters: dict[str, str | None],
    limit: int,
) -> dict[str, object]:
    clauses, parameters = quiz_item_filter_clauses(filters)
    query = f"{admin_item_select()} {where_sql(clauses)} ORDER BY qi.updated_at DESC LIMIT ?"
    with connect(db_path) as connection:
        rows = connection.execute(query, (*parameters, limit)).fetchall()
    return {"data": [admin_quiz_projection(row_to_dict(row)) for row in rows]}


def get_admin_quiz_item(db_path: Path | None, item_id: str) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute(
            f"{admin_item_select()} WHERE qi.item_id = ?",
            (item_id,),
        ).fetchone()
    if row is None:
        raise admin_problem(404, "ADMIN_ITEM_NOT_FOUND", "Quiz item not found")
    return admin_quiz_projection(row_to_dict(row))


def change_admin_quiz_item_status(
    db_path: Path | None,
    item_id: str,
    action: str,
    actor: str,
    reason: str,
) -> dict[str, object]:
    to_status = STATUS_ACTIONS[action]
    try:
        transition_item_status(db_path, item_id, to_status, actor, reason)
    except ValueError as error:
        raise transition_problem(str(error)) from error
    return {"item": get_admin_quiz_item(db_path, item_id), "audit": latest_item_audit(db_path, item_id)}


def admin_dashboard(db_path: Path | None) -> dict[str, object]:
    with connect(db_path) as connection:
        status_counts = count_by(connection, "quiz_items", "status")
        level_counts = count_by(connection, "quiz_items", "sublevel")
        theme_counts = count_by(connection, "quiz_items", "theme_id")
        delivery_count = scalar_count(connection, "deliveries")
        audit_count = scalar_count(connection, "audit_log")
    return {
        "corpus_status_counts": status_counts,
        "items_by_cefr_level": level_counts,
        "items_by_theme": theme_counts,
        "approved_published_count": sum(status_counts.get(status, 0) for status in ("approved", "published")),
        "delivery_log_count": delivery_count,
        "audit_log_count": audit_count,
    }


def list_audit_log(db_path: Path | None, limit: int) -> dict[str, object]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT audit_id, actor, action, entity_type, entity_id, from_status,
                   to_status, reason, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"data": [row_to_dict(row) for row in rows]}


def list_admin_consumers(db_path: Path | None, limit: int) -> dict[str, object]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT c.consumer_id, c.status, c.daily_quota_limit,
                   c.allowed_cefr_levels_json, c.allowed_theme_ids_json,
                   COALESCE(cap.display_name, '') AS display_name,
                   COALESCE(cap.consumer_kind, 'api_client') AS consumer_kind,
                   COUNT(d.delivery_id) AS delivery_count,
                   MAX(d.selected_at) AS last_delivery_at,
                   COALESCE(MAX(qu.used_count), 0) AS today_quota_used
            FROM consumers c
            LEFT JOIN consumer_admin_profiles cap ON cap.consumer_id = c.consumer_id
            LEFT JOIN deliveries d ON d.consumer_id = c.consumer_id
            LEFT JOIN quota_usage qu
              ON qu.consumer_id = c.consumer_id
             AND qu.feature = 'quiz_delivery'
             AND qu.usage_date = ?
            GROUP BY c.consumer_id, c.status, c.daily_quota_limit,
                     c.allowed_cefr_levels_json, c.allowed_theme_ids_json,
                     cap.display_name, cap.consumer_kind
            ORDER BY c.created_at DESC
            LIMIT ?
            """,
            (utc_now()[:10], limit),
        ).fetchall()
    return {"data": [consumer_projection(row_to_dict(row)) for row in rows]}


def create_admin_consumer(db_path: Path | None, payload: dict[str, Any], actor: str) -> dict[str, object]:
    consumer_id = str(payload["consumer_id"])
    seed_consumer(
        db_path,
        consumer_id,
        int(payload["daily_quota_limit"]),
        payload["allowed_cefr_levels"],
        payload["allowed_theme_ids"],
    )
    seed_api_credential(db_path, consumer_id, str(payload["api_key"]))
    seed_entitlement(
        db_path,
        consumer_id,
        payload["allowed_cefr_levels"],
        payload["allowed_theme_ids"],
        actor=actor,
        reason=str(payload["reason"]),
    )
    upsert_consumer_profile(db_path, payload, actor)
    write_consumer_create_audit(db_path, consumer_id, actor, str(payload["reason"]))
    return get_admin_consumer(db_path, consumer_id)


def change_admin_consumer_status(
    db_path: Path | None,
    consumer_id: str,
    to_status: str,
    actor: str,
    reason: str,
) -> dict[str, object]:
    try:
        transition_consumer_status(db_path, consumer_id, to_status, actor, reason)
    except ValueError as error:
        raise consumer_transition_problem(str(error)) from error
    return get_admin_consumer(db_path, consumer_id)


def get_admin_consumer(db_path: Path | None, consumer_id: str) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT c.consumer_id, c.status, c.daily_quota_limit,
                   c.allowed_cefr_levels_json, c.allowed_theme_ids_json,
                   COALESCE(cap.display_name, '') AS display_name,
                   COALESCE(cap.consumer_kind, 'api_client') AS consumer_kind,
                   COUNT(d.delivery_id) AS delivery_count,
                   MAX(d.selected_at) AS last_delivery_at,
                   COALESCE(MAX(qu.used_count), 0) AS today_quota_used
            FROM consumers c
            LEFT JOIN consumer_admin_profiles cap ON cap.consumer_id = c.consumer_id
            LEFT JOIN deliveries d ON d.consumer_id = c.consumer_id
            LEFT JOIN quota_usage qu
              ON qu.consumer_id = c.consumer_id
             AND qu.feature = 'quiz_delivery'
             AND qu.usage_date = ?
            WHERE c.consumer_id = ?
            GROUP BY c.consumer_id, c.status, c.daily_quota_limit,
                     c.allowed_cefr_levels_json, c.allowed_theme_ids_json,
                     cap.display_name, cap.consumer_kind
            """,
            (utc_now()[:10], consumer_id),
        ).fetchone()
    if row is None:
        raise admin_problem(404, "ADMIN_CONSUMER_NOT_FOUND", "Consumer not found")
    return consumer_projection(row_to_dict(row))


def latest_item_audit(db_path: Path | None, item_id: str) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT audit_id, actor, action, entity_type, entity_id, from_status,
                   to_status, reason, created_at
            FROM audit_log
            WHERE entity_type = 'quiz_item' AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (item_id,),
        ).fetchone()
    return None if row is None else row_to_dict(row)


def upsert_consumer_profile(db_path: Path | None, payload: dict[str, Any], actor: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO consumer_admin_profiles (
                consumer_id, display_name, consumer_kind, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(consumer_id) DO UPDATE SET
                display_name = excluded.display_name,
                consumer_kind = excluded.consumer_kind
            """,
            (
                payload["consumer_id"],
                payload["display_name"],
                payload["consumer_kind"],
                actor,
                utc_now(),
            ),
        )


def write_consumer_create_audit(
    db_path: Path | None,
    consumer_id: str,
    actor: str,
    reason: str,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_id, actor, action, entity_type, entity_id, from_status,
                to_status, reason, created_at
            ) VALUES (?, ?, 'consumer_create', 'consumer', ?, '', 'active', ?, ?)
            """,
            (new_id("audit"), actor, consumer_id, reason, utc_now()),
        )


def consumer_projection(row: dict[str, Any]) -> dict[str, object]:
    return {
        "consumer_id": str(row["consumer_id"]),
        "display_name": str(row["display_name"]),
        "consumer_kind": str(row["consumer_kind"]),
        "status": str(row["status"]),
        "daily_quota_limit": int(row["daily_quota_limit"]),
        "allowed_cefr_levels": decode_json_list(row["allowed_cefr_levels_json"]),
        "allowed_theme_ids": decode_json_list(row["allowed_theme_ids_json"]),
        "delivery_count": int(row["delivery_count"]),
        "today_quota_used": int(row["today_quota_used"]),
        "last_delivery_at": row["last_delivery_at"],
    }


def decode_json_list(value: Any) -> list[str]:
    return [str(item) for item in json.loads(str(value))]


def quiz_item_filter_clauses(filters: dict[str, str | None]) -> tuple[list[str], list[str]]:
    clauses: list[str] = []
    parameters: list[str] = []
    for key, column in filter_columns().items():
        value = filters.get(key)
        if value:
            clauses.append(f"{column} = ?")
            parameters.append(value)
    return clauses, parameters


def filter_columns() -> dict[str, str]:
    return {
        "status": "qi.status",
        "cefr_level": "qi.sublevel",
        "theme_id": "qi.theme_id",
        "source_id": "qi.source_id",
    }


def admin_item_select() -> str:
    return """
        SELECT qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
    """


def where_sql(clauses: list[str]) -> str:
    if not clauses:
        return ""
    return "WHERE " + " AND ".join(clauses)


def count_by(connection, table: str, column: str) -> dict[str, int]:
    rows = connection.execute(
        f"SELECT {column} AS key, COUNT(*) AS count FROM {table} GROUP BY {column}"
    ).fetchall()
    return {str(row["key"]): int(row["count"]) for row in rows}


def scalar_count(connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return int(row["count"])


def transition_problem(message: str) -> QuizBankProblem:
    if message.startswith("unknown item_id"):
        return admin_problem(404, "ADMIN_ITEM_NOT_FOUND", "Quiz item not found", message)
    return admin_problem(409, "ADMIN_INVALID_STATUS_TRANSITION", "Invalid status transition", message)


def consumer_transition_problem(message: str) -> QuizBankProblem:
    if message.startswith("unknown consumer_id"):
        return admin_problem(404, "ADMIN_CONSUMER_NOT_FOUND", "Consumer not found", message)
    return admin_problem(409, "ADMIN_INVALID_CONSUMER_TRANSITION", "Invalid consumer transition", message)


def admin_problem(
    status: int,
    reason_code: str,
    title: str,
    detail: str = "Admin operation could not be completed.",
) -> QuizBankProblem:
    return QuizBankProblem(
        status,
        reason_code,
        title,
        detail,
        "https://api.quizbank.example/problems/admin-operation",
    )
