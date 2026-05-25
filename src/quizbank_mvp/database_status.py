"""Status transition persistence helpers."""

from __future__ import annotations

from pathlib import Path

from .database_connection import connect, new_id, utc_now


ALLOWED_TRANSITIONS = {
    "draft": {"approved", "blocked", "retired"},
    "approved": {"published", "blocked", "retired"},
    "published": {"blocked", "retired"},
}
ALLOWED_CONSUMER_TRANSITIONS = {
    "active": {"suspended", "blocked"},
    "suspended": {"active", "blocked"},
    "blocked": {"active"},
}
DELIVERABLE_STATUSES = ("approved", "published")


def transition_item_status(
    db_path: Path | None,
    item_id: str,
    to_status: str,
    actor: str,
    reason: str,
) -> None:
    with connect(db_path) as connection:
        item = connection.execute(
            "SELECT status FROM quiz_items WHERE item_id = ?",
            (item_id,),
        ).fetchone()
        if item is None:
            raise ValueError(f"unknown item_id: {item_id}")
        from_status = item["status"]
        if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
            raise ValueError(f"invalid status transition: {from_status} -> {to_status}")
        connection.execute(
            "UPDATE quiz_items SET status = ?, updated_at = ? WHERE item_id = ?",
            (to_status, utc_now(), item_id),
        )
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_id, actor, action, entity_type, entity_id, from_status,
                to_status, reason, created_at
            ) VALUES (?, ?, 'status_transition', 'quiz_item', ?, ?, ?, ?, ?)
            """,
            (new_id("audit"), actor, item_id, from_status, to_status, reason, utc_now()),
        )


def transition_consumer_status(
    db_path: Path | None,
    consumer_id: str,
    to_status: str,
    actor: str,
    reason: str,
) -> None:
    with connect(db_path) as connection:
        consumer = connection.execute(
            "SELECT status FROM consumers WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        if consumer is None:
            raise ValueError(f"unknown consumer_id: {consumer_id}")
        from_status = consumer["status"]
        if to_status not in ALLOWED_CONSUMER_TRANSITIONS.get(from_status, set()):
            raise ValueError(f"invalid consumer transition: {from_status} -> {to_status}")
        connection.execute(
            "UPDATE consumers SET status = ? WHERE consumer_id = ?",
            (to_status, consumer_id),
        )
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_id, actor, action, entity_type, entity_id, from_status,
                to_status, reason, created_at
            ) VALUES (?, ?, 'consumer_status_transition', 'consumer', ?, ?, ?, ?, ?)
            """,
            (new_id("audit"), actor, consumer_id, from_status, to_status, reason, utc_now()),
        )
