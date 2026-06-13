"""SQLite compatibility helpers for channel and tariff content scope."""

from __future__ import annotations

import sqlite3

from .content_scope_defaults import (
    DEFAULT_ALLOWED_BANK_VERSION_IDS_JSON,
    DEFAULT_ALLOWED_CONTENT_BANK_IDS_JSON,
    DEFAULT_ALLOWED_CONTENT_TYPES_JSON,
    DEFAULT_ALLOWED_LANGUAGE_CODES_JSON,
    DEFAULT_BANK_VERSION_ID,
    DEFAULT_CONTENT_BANK_ID,
    DEFAULT_LANGUAGE_CODE,
)


CONTENT_SCOPE_COLUMNS = {"language_code", "content_bank_id", "bank_version_id"}


def ensure_sqlite_channel_tariff_scope(connection: sqlite3.Connection) -> None:
    ensure_sqlite_consumer_scope_columns(connection)
    ensure_sqlite_entitlement_scope_columns(connection)
    ensure_sqlite_quota_usage_scope(connection)


def ensure_sqlite_consumer_scope_columns(connection: sqlite3.Connection) -> None:
    if not sqlite_table_exists(connection, "consumers"):
        return
    ensure_sqlite_columns(
        connection,
        "consumers",
        {
            "default_language_code": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_LANGUAGE_CODE}' CHECK (default_language_code <> '')"
            ),
            "default_content_bank_id": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_CONTENT_BANK_ID}' CHECK (default_content_bank_id <> '')"
            ),
            "default_bank_version_id": "TEXT NOT NULL DEFAULT ''",
            "allowed_language_codes_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_LANGUAGE_CODES_JSON}'"
            ),
            "allowed_content_bank_ids_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_CONTENT_BANK_IDS_JSON}'"
            ),
            "allowed_bank_version_ids_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_BANK_VERSION_IDS_JSON}'"
            ),
        },
    )


def ensure_sqlite_entitlement_scope_columns(connection: sqlite3.Connection) -> None:
    if not sqlite_table_exists(connection, "entitlements"):
        return
    ensure_sqlite_columns(
        connection,
        "entitlements",
        {
            "allowed_language_codes_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_LANGUAGE_CODES_JSON}'"
            ),
            "allowed_content_bank_ids_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_CONTENT_BANK_IDS_JSON}'"
            ),
            "allowed_bank_version_ids_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_BANK_VERSION_IDS_JSON}'"
            ),
            "allowed_content_types_json": (
                f"TEXT NOT NULL DEFAULT '{DEFAULT_ALLOWED_CONTENT_TYPES_JSON}'"
            ),
        },
    )


def ensure_sqlite_columns(
    connection: sqlite3.Connection,
    table_name: str,
    column_sql: dict[str, str],
) -> None:
    existing_columns = sqlite_table_columns(connection, table_name)
    for column_name, definition in column_sql.items():
        if column_name not in existing_columns:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def ensure_sqlite_quota_usage_scope(connection: sqlite3.Connection) -> None:
    if not sqlite_table_exists(connection, "quota_usage"):
        return
    if sqlite_quota_usage_scope_is_ready(connection):
        return
    rebuild_sqlite_quota_usage(connection)


def rebuild_sqlite_quota_usage(connection: sqlite3.Connection) -> None:
    existing_columns = sqlite_table_columns(connection, "quota_usage")
    language_expr = scoped_backfill_expr(existing_columns, "language_code", DEFAULT_LANGUAGE_CODE)
    bank_expr = scoped_backfill_expr(existing_columns, "content_bank_id", DEFAULT_CONTENT_BANK_ID)
    version_expr = scoped_backfill_expr(existing_columns, "bank_version_id", DEFAULT_BANK_VERSION_ID)
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS quota_usage_content_scope_migration")
    connection.executescript(scoped_quota_usage_table_sql())
    connection.execute(scoped_quota_usage_backfill_sql(language_expr, bank_expr, version_expr))
    connection.execute("DROP TABLE quota_usage")
    connection.execute("ALTER TABLE quota_usage_content_scope_migration RENAME TO quota_usage")
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")


def scoped_quota_usage_table_sql() -> str:
    return f"""
        CREATE TABLE quota_usage_content_scope_migration (
            quota_usage_id TEXT PRIMARY KEY,
            consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
            feature TEXT NOT NULL,
            usage_date TEXT NOT NULL,
            language_code TEXT NOT NULL DEFAULT '{DEFAULT_LANGUAGE_CODE}' CHECK (language_code <> ''),
            content_bank_id TEXT NOT NULL DEFAULT '{DEFAULT_CONTENT_BANK_ID}' CHECK (content_bank_id <> ''),
            bank_version_id TEXT NOT NULL DEFAULT '{DEFAULT_BANK_VERSION_ID}' CHECK (bank_version_id <> ''),
            used_count INTEGER NOT NULL,
            quota_limit INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (
                consumer_id,
                feature,
                usage_date,
                language_code,
                content_bank_id,
                bank_version_id
            )
        );
    """


def scoped_quota_usage_backfill_sql(language_expr: str, bank_expr: str, version_expr: str) -> str:
    return f"""
        INSERT INTO quota_usage_content_scope_migration (
            quota_usage_id, consumer_id, feature, usage_date,
            language_code, content_bank_id, bank_version_id,
            used_count, quota_limit, updated_at
        )
        SELECT
            quota_usage_id, consumer_id, feature, usage_date,
            {language_expr}, {bank_expr}, {version_expr},
            used_count, quota_limit, updated_at
        FROM quota_usage
    """


def scoped_backfill_expr(existing_columns: set[str], column_name: str, default_value: str) -> str:
    if column_name in existing_columns:
        return f"COALESCE(NULLIF({column_name}, ''), '{default_value}')"
    return f"'{default_value}'"


def sqlite_channel_tariff_scope_is_ready(connection: sqlite3.Connection) -> bool:
    return (
        sqlite_table_has_columns(
            connection,
            "consumers",
            {
                "default_language_code",
                "default_content_bank_id",
                "default_bank_version_id",
                "allowed_language_codes_json",
                "allowed_content_bank_ids_json",
                "allowed_bank_version_ids_json",
            },
        )
        and sqlite_table_has_columns(
            connection,
            "entitlements",
            {
                "allowed_language_codes_json",
                "allowed_content_bank_ids_json",
                "allowed_bank_version_ids_json",
                "allowed_content_types_json",
            },
        )
        and sqlite_quota_usage_scope_is_ready(connection)
    )


def sqlite_quota_usage_scope_is_ready(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'quota_usage'
        """
    ).fetchone()
    if row is None:
        return False
    return (
        sqlite_table_has_columns(connection, "quota_usage", CONTENT_SCOPE_COLUMNS)
        and "language_code" in str(row["sql"])
        and "content_bank_id" in str(row["sql"])
        and "bank_version_id" in str(row["sql"])
    )


def sqlite_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def sqlite_table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def sqlite_table_has_columns(
    connection: sqlite3.Connection,
    table_name: str,
    column_names: set[str],
) -> bool:
    return column_names.issubset(sqlite_table_columns(connection, table_name))
