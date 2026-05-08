"""SQLite persistence for the MVP runtime."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIRECTORY = ROOT / "database" / "migrations"
DEFAULT_DB_PATH = ROOT / "var" / "quizbank_mvp.sqlite3"
DELIVERABLE_STATUSES = ("approved", "published")
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


def configured_db_path() -> Path:
    return Path(os.environ.get("QUIZBANK_DB_PATH", DEFAULT_DB_PATH)).resolve()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = (db_path or configured_db_path()).resolve()
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: Path | None = None) -> Path:
    path = (db_path or configured_db_path()).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        for migration_path in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
            connection.executescript(migration_path.read_text(encoding="utf-8"))
    return path


def database_is_ready(db_path: Path | None = None) -> bool:
    path = (db_path or configured_db_path()).resolve()
    if not path.exists():
        return False
    with connect(path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    table_names = {row["name"] for row in rows}
    return {"quiz_items", "consumers", "api_credentials", "deliveries"}.issubset(table_names)


def read_jsonl(path: Path) -> list[dict[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def seed_control_fixture(
    db_path: Path | None,
    fixture_path: Path,
    item_status: str,
    source_id: str = "src_control_mvp",
) -> int:
    rows = read_jsonl(fixture_path)
    checksum = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    now = utc_now()
    source_type = rows[0].get("source_type", "fixture") if rows else "fixture"
    provenance_note = rows[0].get("provenance_note", str(fixture_path)) if rows else str(fixture_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO sources (
                source_id, source_type, provenance_note, checksum_sha256, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type = excluded.source_type,
                provenance_note = excluded.provenance_note,
                checksum_sha256 = excluded.checksum_sha256,
                status = excluded.status
            """,
            (source_id, source_type, provenance_note, checksum, "active", now),
        )
        for item in rows:
            upsert_quiz_item(connection, item, item_status, source_id)
    return len(rows)


def upsert_quiz_item(
    connection: sqlite3.Connection,
    item: dict[str, str],
    item_status: str,
    source_id: str,
) -> None:
    connection.execute(
        """
        INSERT INTO quiz_items (
            item_id, source_id, language, level_band, sublevel, theme_id, subtheme_id,
            objective_id, pattern_id, difficulty_band, register, prompt, stem_text,
            options_json, answer_key, explanation, tags, coverage_cell_id, status,
            version, created_at, updated_at, reviewed_at, level_locked, locked_at
        ) VALUES (
            :item_id, :source_id, :language, :level_band, :sublevel, :theme_id,
            :subtheme_id, :objective_id, :pattern_id, :difficulty_band, :register,
            :prompt, :stem_text, :options_json, :answer_key, :explanation, :tags,
            :coverage_cell_id, :status, :version, :created_at, :updated_at,
            :reviewed_at, :level_locked, :locked_at
        )
        ON CONFLICT(item_id) DO UPDATE SET
            source_id = excluded.source_id,
            status = excluded.status,
            updated_at = excluded.updated_at
        """,
        {
            **item,
            "source_id": source_id,
            "options_json": item["options"],
            "status": item_status,
        },
    )


def seed_consumer(
    db_path: Path | None,
    consumer_id: str,
    daily_quota_limit: int,
    allowed_cefr_levels: Iterable[str],
    allowed_theme_ids: Iterable[str],
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO consumers (
                consumer_id, status, allowed_cefr_levels_json, allowed_theme_ids_json,
                daily_quota_limit, created_at
            ) VALUES (?, 'active', ?, ?, ?, ?)
            ON CONFLICT(consumer_id) DO UPDATE SET
                status = excluded.status,
                allowed_cefr_levels_json = excluded.allowed_cefr_levels_json,
                allowed_theme_ids_json = excluded.allowed_theme_ids_json,
                daily_quota_limit = excluded.daily_quota_limit
            """,
            (
                consumer_id,
                json.dumps(list(allowed_cefr_levels)),
                json.dumps(list(allowed_theme_ids)),
                daily_quota_limit,
                utc_now(),
            ),
        )


def seed_api_credential(
    db_path: Path | None,
    consumer_id: str,
    raw_api_key: str,
    credential_id: str | None = None,
    status: str = "active",
) -> str:
    from .auth import api_key_prefix, hash_api_key

    resolved_credential_id = credential_id or f"cred_{consumer_id}"
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO api_credentials (
                credential_id, consumer_id, key_prefix, key_hash, status,
                created_at, revoked_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(credential_id) DO UPDATE SET
                key_prefix = excluded.key_prefix,
                key_hash = excluded.key_hash,
                status = excluded.status,
                revoked_at = NULL
            """,
            (
                resolved_credential_id,
                consumer_id,
                api_key_prefix(raw_api_key),
                hash_api_key(raw_api_key),
                status,
                utc_now(),
            ),
        )
    return resolved_credential_id


def seed_entitlement(
    db_path: Path | None,
    consumer_id: str,
    allowed_cefr_levels: Iterable[str],
    allowed_theme_ids: Iterable[str],
    valid_until: str | None = None,
    actor: str = "local_seed",
    reason: str = "MVP entitlement grant",
) -> str:
    entitlement_id = f"ent_{consumer_id}"
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status, allowed_cefr_levels_json,
                allowed_theme_ids_json, valid_until, created_at
            ) VALUES (?, ?, 'quiz_delivery', 'active', ?, ?, ?, ?)
            ON CONFLICT(entitlement_id) DO UPDATE SET
                status = excluded.status,
                allowed_cefr_levels_json = excluded.allowed_cefr_levels_json,
                allowed_theme_ids_json = excluded.allowed_theme_ids_json,
                valid_until = excluded.valid_until
            """,
            (
                entitlement_id,
                consumer_id,
                json.dumps(list(allowed_cefr_levels)),
                json.dumps(list(allowed_theme_ids)),
                valid_until,
                utc_now(),
            ),
        )
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_id, actor, action, entity_type, entity_id, from_status,
                to_status, reason, created_at
            ) VALUES (?, ?, 'entitlement_grant', 'entitlement', ?, '', 'active', ?, ?)
            """,
            (new_id("audit"), actor, entitlement_id, reason, utc_now()),
        )
    return entitlement_id


def seed_demo_state(db_path: Path | None, fixture_path: Path) -> None:
    reset_demo_delivery_state(db_path)
    seed_control_fixture(db_path, fixture_path, "approved")
    seed_consumer(db_path, "consumer_demo", 2, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_demo", "demo_consumer_api_key")
    seed_entitlement(db_path, "consumer_demo", ["A2"], ["T10"])
    seed_consumer(db_path, "consumer_quota_blocked", 0, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_quota_blocked", "quota_blocked_api_key")
    seed_entitlement(db_path, "consumer_quota_blocked", ["A2"], ["T10"])
    seed_consumer(db_path, "consumer_no_entitlement", 2, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_no_entitlement", "no_entitlement_api_key")


def reset_demo_delivery_state(db_path: Path | None) -> None:
    demo_consumers = (
        "consumer_demo",
        "consumer_quota_blocked",
        "consumer_no_entitlement",
    )
    with connect(db_path) as connection:
        connection.execute(
            "DELETE FROM deliveries WHERE consumer_id IN (?, ?, ?)",
            demo_consumers,
        )
        connection.execute(
            "DELETE FROM quota_usage WHERE consumer_id IN (?, ?, ?)",
            demo_consumers,
        )


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


def today_usage_date() -> str:
    return date.today().isoformat()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}
