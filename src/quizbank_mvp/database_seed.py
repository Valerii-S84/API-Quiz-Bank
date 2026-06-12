"""Seed and demo persistence helpers for the MVP runtime."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .credential_hashing import admin_key_prefix, api_key_prefix, hash_api_key
from .database_connection import connect
from .database_runtime import (
    DEFAULT_BANK_VERSION_ID,
    DEFAULT_CONTENT_BANK_ID,
    DEFAULT_LANGUAGE_CODE,
)
from .image_quality_repository import upsert_quiz_item_image_quality_policy
from .time_ids import new_id, utc_now
from .visual_asset_repository import insert_visual_asset_record


DEFAULT_VISUAL_SETTINGS = {
    "delivery_mode": "text_only",
    "visual_style": "standard_illustration",
    "branding_preset": "none",
    "fallback_policy": "text_only",
    "daily_visual_delivery_limit": 0,
    "daily_generation_limit": 0,
    "monthly_generation_limit": 0,
    "is_active": 1,
}


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
    source_scope = content_scope_values(rows[0] if rows else {})
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO sources (
                source_id, source_type, provenance_note, checksum_sha256, status,
                created_at, language_code, content_bank_id, bank_version_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type = excluded.source_type,
                provenance_note = excluded.provenance_note,
                checksum_sha256 = excluded.checksum_sha256,
                status = excluded.status,
                language_code = excluded.language_code,
                content_bank_id = excluded.content_bank_id,
                bank_version_id = excluded.bank_version_id
            """,
            (
                source_id,
                source_type,
                provenance_note,
                checksum,
                "active",
                now,
                *source_scope,
            ),
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
            item_id, source_id, language, language_code, content_bank_id,
            bank_version_id, level_band, sublevel, theme_id, subtheme_id,
            objective_id, pattern_id, difficulty_band, register, prompt,
            stem_text, options_json, answer_key, explanation, tags,
            coverage_cell_id, status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        ) VALUES (
            :item_id, :source_id, :language, :language_code, :content_bank_id,
            :bank_version_id, :level_band, :sublevel, :theme_id, :subtheme_id,
            :objective_id, :pattern_id, :difficulty_band, :register, :prompt,
            :stem_text, :options_json, :answer_key, :explanation, :tags,
            :coverage_cell_id, :status, :version, :created_at, :updated_at,
            :reviewed_at, :level_locked, :locked_at
        )
        ON CONFLICT(item_id) DO UPDATE SET
            source_id = excluded.source_id,
            language_code = excluded.language_code,
            content_bank_id = excluded.content_bank_id,
            bank_version_id = excluded.bank_version_id,
            status = excluded.status,
            updated_at = excluded.updated_at
        """,
        {
            **item,
            "source_id": source_id,
            "options_json": item["options"],
            "status": item_status,
            "language_code": item.get("language_code") or item.get("language") or DEFAULT_LANGUAGE_CODE,
            "content_bank_id": item.get("content_bank_id") or DEFAULT_CONTENT_BANK_ID,
            "bank_version_id": item.get("bank_version_id") or DEFAULT_BANK_VERSION_ID,
        },
    )
    upsert_quiz_item_image_quality_policy(connection, item)


def content_scope_values(item: dict[str, str]) -> tuple[str, str, str]:
    return (
        item.get("language_code") or item.get("language") or DEFAULT_LANGUAGE_CODE,
        item.get("content_bank_id") or DEFAULT_CONTENT_BANK_ID,
        item.get("bank_version_id") or DEFAULT_BANK_VERSION_ID,
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


def seed_admin_credential(
    db_path: Path | None,
    actor: str,
    role: str,
    raw_admin_key: str,
    credential_id: str | None = None,
    status: str = "active",
) -> str:
    resolved_credential_id = credential_id or f"admin_cred_{actor}"
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO admin_credentials (
                credential_id, actor, role, key_prefix, key_hash, status,
                created_at, revoked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(credential_id) DO UPDATE SET
                role = excluded.role,
                key_prefix = excluded.key_prefix,
                key_hash = excluded.key_hash,
                status = excluded.status,
                revoked_at = NULL
            """,
            (
                resolved_credential_id,
                actor,
                role,
                admin_key_prefix(raw_admin_key),
                hash_api_key(raw_admin_key),
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


def upsert_consumer_visual_settings(
    db_path: Path | None,
    consumer_id: str,
    settings: dict[str, Any] | None = None,
) -> None:
    values = {**DEFAULT_VISUAL_SETTINGS, **(settings or {})}
    now = utc_now()
    created_at = str(values.get("created_at", now))
    updated_at = str(values.get("updated_at", now))
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO consumer_visual_settings (
                consumer_id, delivery_mode, visual_style, branding_preset,
                fallback_policy, daily_visual_delivery_limit,
                daily_generation_limit, monthly_generation_limit, is_active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(consumer_id) DO UPDATE SET
                delivery_mode = excluded.delivery_mode,
                visual_style = excluded.visual_style,
                branding_preset = excluded.branding_preset,
                fallback_policy = excluded.fallback_policy,
                daily_visual_delivery_limit = excluded.daily_visual_delivery_limit,
                daily_generation_limit = excluded.daily_generation_limit,
                monthly_generation_limit = excluded.monthly_generation_limit,
                is_active = excluded.is_active,
                updated_at = excluded.updated_at
            """,
            (
                consumer_id,
                values["delivery_mode"],
                values["visual_style"],
                values["branding_preset"],
                values["fallback_policy"],
                values["daily_visual_delivery_limit"],
                values["daily_generation_limit"],
                values["monthly_generation_limit"],
                values["is_active"],
                created_at,
                updated_at,
            ),
        )


def insert_visual_asset(db_path: Path | None, asset: dict[str, Any]) -> str:
    return insert_visual_asset_record(db_path, asset, connect, new_id, utc_now)


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
