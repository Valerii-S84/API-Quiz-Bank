"""Content bank version status and activation workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .database_connection import connect, new_id, utc_now


class ContentBankVersionError(ValueError):
    """Raised when a content bank version workflow invariant fails."""


def mark_bank_version_for_audit(
    db_path: Path | None,
    bank_version_id: str,
    actor: str,
    reason: str,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        version = load_bank_version(connection, bank_version_id)
        require_status(version, {"draft"})
        now = utc_now()
        connection.execute(
            "UPDATE content_bank_versions SET status = 'audit' WHERE id = ?",
            (bank_version_id,),
        )
        write_audit_log(
            connection,
            "content_bank_version_mark_audit",
            bank_version_id,
            str(version["status"]),
            "audit",
            actor,
            reason,
            now,
        )
    return {"bank_version_id": bank_version_id, "from_status": "draft", "to_status": "audit"}


def activate_bank_version(
    db_path: Path | None,
    bank_version_id: str,
    actor: str,
    reason: str,
) -> dict[str, Any]:
    return activate_target_version(
        db_path,
        bank_version_id,
        actor,
        reason,
        allowed_target_statuses={"audit"},
        audit_action="content_bank_version_activate",
    )


def rollback_bank_version(
    db_path: Path | None,
    bank_version_id: str,
    actor: str,
    reason: str,
) -> dict[str, Any]:
    return activate_target_version(
        db_path,
        bank_version_id,
        actor,
        reason,
        allowed_target_statuses={"archived"},
        audit_action="content_bank_version_rollback",
    )


def activate_target_version(
    db_path: Path | None,
    bank_version_id: str,
    actor: str,
    reason: str,
    allowed_target_statuses: set[str],
    audit_action: str,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        target = load_bank_version(connection, bank_version_id)
        require_status(target, allowed_target_statuses)
        active = load_active_version(connection, str(target["content_bank_id"]))
        if active is not None and active["id"] == bank_version_id:
            raise ContentBankVersionError("target_version_already_active")
        now = utc_now()
        from_bank_version_id = None if active is None else str(active["id"])
        archive_active_version(connection, active)
        connection.execute(
            """
            UPDATE content_bank_versions
            SET status = 'active', activated_at = ?
            WHERE id = ?
            """,
            (now, bank_version_id),
        )
        connection.execute(
            "UPDATE content_banks SET status = 'active' WHERE id = ?",
            (target["content_bank_id"],),
        )
        event_id = write_activation_event(
            connection,
            str(target["content_bank_id"]),
            from_bank_version_id,
            bank_version_id,
            actor,
            reason,
            now,
        )
        write_audit_log(
            connection,
            audit_action,
            bank_version_id,
            str(target["status"]),
            "active",
            actor,
            reason,
            now,
        )
    return {
        "activation_event_id": event_id,
        "content_bank_id": str(target["content_bank_id"]),
        "from_bank_version_id": from_bank_version_id,
        "to_bank_version_id": bank_version_id,
        "to_status": "active",
    }


def load_bank_version(connection: Any, bank_version_id: str) -> Any:
    row = connection.execute(
        """
        SELECT cbv.id, cbv.content_bank_id, cbv.version, cbv.status,
               cbv.activated_at, cbv.created_at, cb.language_code
        FROM content_bank_versions cbv
        JOIN content_banks cb ON cb.id = cbv.content_bank_id
        WHERE cbv.id = ?
        """,
        (bank_version_id,),
    ).fetchone()
    if row is None:
        raise ContentBankVersionError(f"unknown_bank_version:{bank_version_id}")
    return row


def load_active_version(connection: Any, content_bank_id: str) -> Any | None:
    return connection.execute(
        """
        SELECT id, content_bank_id, version, status, activated_at, created_at
        FROM content_bank_versions
        WHERE content_bank_id = ? AND status = 'active'
        """,
        (content_bank_id,),
    ).fetchone()


def require_status(version: Any, allowed_statuses: set[str]) -> None:
    status = str(version["status"])
    if status not in allowed_statuses:
        allowed = ",".join(sorted(allowed_statuses))
        raise ContentBankVersionError(f"invalid_bank_version_status:{status}:expected:{allowed}")


def archive_active_version(connection: Any, active: Any | None) -> None:
    if active is None:
        return
    connection.execute(
        """
        UPDATE content_bank_versions
        SET status = 'archived'
        WHERE id = ? AND status = 'active'
        """,
        (active["id"],),
    )


def write_activation_event(
    connection: Any,
    content_bank_id: str,
    from_bank_version_id: str | None,
    to_bank_version_id: str,
    actor: str,
    reason: str,
    activated_at: str,
) -> str:
    event_id = new_id("activation")
    connection.execute(
        """
        INSERT INTO content_bank_activation_events (
            activation_event_id, content_bank_id, from_bank_version_id,
            to_bank_version_id, actor, reason, activated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            content_bank_id,
            from_bank_version_id,
            to_bank_version_id,
            actor,
            reason,
            activated_at,
        ),
    )
    return event_id


def write_audit_log(
    connection: Any,
    action: str,
    entity_id: str,
    from_status: str,
    to_status: str,
    actor: str,
    reason: str,
    created_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO audit_log (
            audit_id, actor, action, entity_type, entity_id, from_status,
            to_status, reason, created_at
        ) VALUES (?, ?, ?, 'content_bank_version', ?, ?, ?, ?, ?)
        """,
        (new_id("audit"), actor, action, entity_id, from_status, to_status, reason, created_at),
    )
