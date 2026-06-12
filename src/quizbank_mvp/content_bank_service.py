"""Content bank version status and activation workflow."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .database_connection import connect, new_id, row_to_dict, utc_now


DEFAULT_LANGUAGE_CODE = "de"


class ContentBankVersionError(ValueError):
    """Raised when a content bank version workflow invariant fails."""


def list_languages(db_path: Path | None) -> dict[str, Any]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT code, name, is_active, created_at
            FROM languages
            ORDER BY CASE code
                WHEN 'de' THEN 1
                WHEN 'en' THEN 2
                WHEN 'fr' THEN 3
                WHEN 'es' THEN 4
                WHEN 'nl' THEN 5
                ELSE 99
            END
            """
        ).fetchall()
    return {"data": [language_projection(row_to_dict(row)) for row in rows]}


def list_content_banks(
    db_path: Path | None,
    language_code: str = DEFAULT_LANGUAGE_CODE,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT cb.id, cb.slug, cb.language_code, lang.name AS language_name,
                   cb.name, cb.status, cb.created_at,
                   active.id AS active_bank_version_id,
                   active.version AS active_bank_version,
                   COUNT(cbv.id) AS version_count
            FROM content_banks cb
            JOIN languages lang ON lang.code = cb.language_code
            LEFT JOIN content_bank_versions active
              ON active.content_bank_id = cb.id
             AND active.status = 'active'
            LEFT JOIN content_bank_versions cbv
              ON cbv.content_bank_id = cb.id
            WHERE cb.language_code = ?
            GROUP BY cb.id, cb.slug, cb.language_code, lang.name, cb.name,
                     cb.status, cb.created_at, active.id, active.version
            ORDER BY cb.slug
            """,
            (language_code,),
        ).fetchall()
    return {"data": [content_bank_projection(row_to_dict(row)) for row in rows]}


def list_content_bank_versions(db_path: Path | None, content_bank_id: str) -> dict[str, Any]:
    with connect(db_path) as connection:
        ensure_content_bank_exists(connection, content_bank_id)
        rows = connection.execute(
            """
            SELECT cbv.id, cbv.content_bank_id, cb.slug AS content_bank_slug,
                   cb.language_code, cbv.version, cbv.status, cbv.activated_at,
                   cbv.created_at
            FROM content_bank_versions cbv
            JOIN content_banks cb ON cb.id = cbv.content_bank_id
            WHERE cbv.content_bank_id = ?
            ORDER BY CASE cbv.status
                WHEN 'active' THEN 1
                WHEN 'audit' THEN 2
                WHEN 'draft' THEN 3
                WHEN 'archived' THEN 4
                ELSE 99
            END,
            cbv.created_at DESC,
            cbv.id
            """,
            (content_bank_id,),
        ).fetchall()
    return {"data": [content_bank_version_projection(row_to_dict(row)) for row in rows]}


def list_import_batches(
    db_path: Path | None,
    filters: dict[str, str | None],
    limit: int,
) -> dict[str, Any]:
    clauses, parameters = import_batch_filter_clauses(filters)
    query = f"{import_batch_select()} {where_sql(clauses)} {import_batch_order_sql()} LIMIT ?"
    try:
        with connect(db_path) as connection:
            rows = connection.execute(query, (*parameters, limit)).fetchall()
    except sqlite3.OperationalError as error:
        if import_batches_table_is_missing(error):
            return {"data": []}
        raise
    return {"data": [import_batch_projection(row_to_dict(row)) for row in rows]}


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


def ensure_content_bank_exists(connection: Any, content_bank_id: str) -> None:
    row = connection.execute(
        "SELECT id FROM content_banks WHERE id = ?",
        (content_bank_id,),
    ).fetchone()
    if row is None:
        raise ContentBankVersionError(f"unknown_content_bank:{content_bank_id}")


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


def import_batch_filter_clauses(filters: dict[str, str | None]) -> tuple[list[str], list[str]]:
    clauses: list[str] = []
    parameters: list[str] = []
    for key, column in import_batch_filter_columns().items():
        value = filters.get(key)
        if value:
            clauses.append(f"{column} = ?")
            parameters.append(value)
    return clauses, parameters


def import_batch_filter_columns() -> dict[str, str]:
    return {
        "language_code": "ib.language_code",
        "content_bank_id": "ib.content_bank_id",
        "bank_version_id": "ib.bank_version_id",
        "import_status": "ib.import_status",
    }


def import_batch_select() -> str:
    return """
        SELECT ib.import_batch_id, ib.source_id, ib.parser_profile_id,
               ib.import_mode, ib.import_status, ib.language_code,
               ib.content_bank_id, ib.bank_version_id,
               cbv.status AS bank_version_status,
               ib.default_item_status, ib.row_count_detected,
               ib.accepted_candidate_count, ib.rejected_candidate_count,
               ib.report_uri, ib.started_at, ib.completed_at, ib.created_by
        FROM import_batches ib
        LEFT JOIN content_bank_versions cbv ON cbv.id = ib.bank_version_id
    """


def import_batch_order_sql() -> str:
    return "ORDER BY COALESCE(ib.completed_at, ib.started_at) DESC, ib.import_batch_id DESC"


def where_sql(clauses: list[str]) -> str:
    if not clauses:
        return ""
    return "WHERE " + " AND ".join(clauses)


def import_batches_table_is_missing(error: sqlite3.OperationalError) -> bool:
    return "no such table: import_batches" in str(error)


def language_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": str(row["code"]),
        "name": str(row["name"]),
        "is_active": bool(row["is_active"]),
        "created_at": str(row["created_at"]),
    }


def content_bank_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "content_bank_id": str(row["id"]),
        "slug": str(row["slug"]),
        "language_code": str(row["language_code"]),
        "language_name": str(row["language_name"]),
        "name": str(row["name"]),
        "status": str(row["status"]),
        "active_bank_version_id": optional_str(row["active_bank_version_id"]),
        "active_bank_version": optional_str(row["active_bank_version"]),
        "version_count": int(row["version_count"]),
        "created_at": str(row["created_at"]),
    }


def content_bank_version_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "bank_version_id": str(row["id"]),
        "content_bank_id": str(row["content_bank_id"]),
        "content_bank_slug": str(row["content_bank_slug"]),
        "language_code": str(row["language_code"]),
        "version": str(row["version"]),
        "status": str(row["status"]),
        "activated_at": optional_str(row["activated_at"]),
        "created_at": str(row["created_at"]),
    }


def import_batch_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "import_batch_id": str(row["import_batch_id"]),
        "source_id": str(row["source_id"]),
        "parser_profile_id": str(row["parser_profile_id"]),
        "import_mode": str(row["import_mode"]),
        "import_status": str(row["import_status"]),
        "language_code": str(row["language_code"]),
        "content_bank_id": str(row["content_bank_id"]),
        "bank_version_id": str(row["bank_version_id"]),
        "bank_version_status": optional_str(row["bank_version_status"]),
        "default_item_status": str(row["default_item_status"]),
        "row_count_detected": int(row["row_count_detected"]),
        "accepted_candidate_count": int(row["accepted_candidate_count"]),
        "rejected_candidate_count": int(row["rejected_candidate_count"]),
        "report_uri": str(row["report_uri"]),
        "started_at": str(row["started_at"]),
        "completed_at": optional_str(row["completed_at"]),
        "created_by": str(row["created_by"]),
    }


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
