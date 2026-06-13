"""Database migration and readiness checks."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .content_scope_defaults import DEFAULT_BANK_VERSION, DEFAULT_BANK_VERSION_ID
from .content_scope_defaults import DEFAULT_CONTENT_BANK_ID, DEFAULT_LANGUAGE_CODE
from .database_channel_tariff_scope import ensure_sqlite_channel_tariff_scope
from .database_channel_tariff_scope import sqlite_channel_tariff_scope_is_ready
from .database_connection import (
    ROOT,
    configured_database_url,
    configured_db_path,
    connect,
    utc_now,
)
from .visual_database_metadata import (
    ensure_visual_metadata_columns,
    postgresql_visual_metadata_is_ready,
    sqlite_visual_metadata_is_ready,
)


MIGRATIONS_DIRECTORY = ROOT / "database" / "migrations"
POSTGRESQL_MIGRATIONS_DIRECTORY = ROOT / "database" / "postgresql"
RUNTIME_TABLES = {
    "languages",
    "content_banks",
    "content_bank_versions",
    "content_bank_activation_events",
    "quiz_items",
    "consumers",
    "api_credentials",
    "admin_credentials",
    "consumer_admin_profiles",
    "deliveries",
    "selection_decisions",
    "quiz_item_image_quality_policy",
}
VISUAL_RUNTIME_TABLES = {
    "consumer_visual_settings",
    "visual_assets",
    "visual_prompt_audit",
    "visual_delivery_results",
    "visual_usage_events",
}
CONTENT_SCOPE_COLUMNS = {
    "language_code",
    "content_bank_id",
    "bank_version_id",
}
SIMPLE_CONTENT_SCOPE_TABLES = (
    "sources",
    "deliveries",
    "selection_decisions",
    "visual_assets",
    "visual_prompt_audit",
    "visual_usage_events",
)
SCOPED_COLUMN_SQL = {
    "language_code": f"TEXT NOT NULL DEFAULT '{DEFAULT_LANGUAGE_CODE}' CHECK (language_code <> '')",
    "content_bank_id": f"TEXT NOT NULL DEFAULT '{DEFAULT_CONTENT_BANK_ID}' CHECK (content_bank_id <> '')",
    "bank_version_id": f"TEXT NOT NULL DEFAULT '{DEFAULT_BANK_VERSION_ID}' CHECK (bank_version_id <> '')",
}


def initialize_database(db_path: Path | None = None):
    if db_path is None and configured_database_url():
        initialize_postgresql_database()
        return "postgresql"
    path = (db_path or configured_db_path()).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        for migration_path in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
            connection.executescript(migration_path.read_text(encoding="utf-8"))
        ensure_sqlite_content_bank_foundation(connection)
        ensure_visual_metadata_columns(connection)
    return path


def database_is_ready(db_path: Path | None = None) -> bool:
    if db_path is None and configured_database_url():
        return postgresql_is_ready()
    path = (db_path or configured_db_path()).resolve()
    return (
        path.exists()
        and RUNTIME_TABLES.issubset(sqlite_table_names(path))
        and sqlite_content_bank_foundation_is_ready(path)
    )


def visual_database_is_ready(db_path: Path | None = None) -> bool:
    if db_path is None and configured_database_url():
        try:
            return VISUAL_RUNTIME_TABLES.issubset(
                postgresql_table_names()
            ) and postgresql_visual_metadata_is_ready(connect)
        except Exception:
            return False
    path = (db_path or configured_db_path()).resolve()
    return (
        path.exists()
        and VISUAL_RUNTIME_TABLES.issubset(sqlite_table_names(path))
        and sqlite_visual_metadata_is_ready(connect, path)
    )


def sqlite_table_names(path: Path) -> set[str]:
    with connect(path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return {row["name"] for row in rows}


def sqlite_content_bank_foundation_is_ready(path: Path) -> bool:
    with connect(path) as connection:
        return (
            sqlite_table_has_columns(connection, "quiz_items", CONTENT_SCOPE_COLUMNS)
            and sqlite_table_has_columns(connection, "sources", CONTENT_SCOPE_COLUMNS)
            and sqlite_table_has_columns(connection, "deliveries", CONTENT_SCOPE_COLUMNS)
            and sqlite_channel_tariff_scope_is_ready(connection)
            and sqlite_quiz_items_has_bank_version_fk(connection)
            and sqlite_active_german_bank_version_exists(connection)
        )


def ensure_sqlite_content_bank_foundation(connection: sqlite3.Connection) -> None:
    ensure_sqlite_content_reference_rows(connection)
    for table_name in SIMPLE_CONTENT_SCOPE_TABLES:
        ensure_sqlite_scope_columns(connection, table_name)
    ensure_sqlite_scheduled_slot_scope(connection)
    ensure_sqlite_quiz_item_scope(connection)
    ensure_sqlite_channel_tariff_scope(connection)
    ensure_sqlite_scope_indexes(connection)


def ensure_sqlite_content_reference_rows(connection: sqlite3.Connection) -> None:
    ensure_sqlite_content_reference_tables(connection)
    seed_sqlite_languages(connection)
    seed_sqlite_default_content_bank(connection)
    seed_sqlite_default_bank_version(connection)
    seed_sqlite_default_activation_event(connection)


def ensure_sqlite_content_reference_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS languages (
            code TEXT PRIMARY KEY CHECK (code IN ('de', 'en', 'fr', 'es', 'nl')),
            name TEXT NOT NULL CHECK (name <> ''),
            is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS content_banks (
            id TEXT PRIMARY KEY,
            slug TEXT NOT NULL CHECK (slug <> ''),
            language_code TEXT NOT NULL REFERENCES languages(code),
            name TEXT NOT NULL CHECK (name <> ''),
            status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
            created_at TEXT NOT NULL,
            UNIQUE (language_code, slug)
        );

        CREATE TABLE IF NOT EXISTS content_bank_versions (
            id TEXT PRIMARY KEY,
            content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
            version TEXT NOT NULL CHECK (version <> ''),
            status TEXT NOT NULL CHECK (status IN ('draft', 'audit', 'active', 'archived')),
            activated_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE (content_bank_id, version)
        );

        CREATE TABLE IF NOT EXISTS content_bank_activation_events (
            activation_event_id TEXT PRIMARY KEY,
            content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
            from_bank_version_id TEXT REFERENCES content_bank_versions(id),
            to_bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
            actor TEXT NOT NULL CHECK (actor <> ''),
            reason TEXT NOT NULL CHECK (reason <> ''),
            activated_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS uq_content_bank_versions_one_active
            ON content_bank_versions(content_bank_id)
            WHERE status = 'active';

        CREATE INDEX IF NOT EXISTS idx_content_bank_versions_status
            ON content_bank_versions(content_bank_id, status, activated_at);
        """
    )


def seed_sqlite_languages(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO languages (code, name, is_active, created_at)
        VALUES (?, ?, ?, '2026-06-12T00:00:00Z')
        """,
        (
            ("de", "German", 1),
            ("en", "English", 0),
            ("fr", "French", 0),
            ("es", "Spanish", 0),
            ("nl", "Dutch", 0),
        ),
    )


def seed_sqlite_default_content_bank(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO content_banks (
            id, slug, language_code, name, status, created_at
        ) VALUES (?, ?, ?, ?, ?, '2026-06-12T00:00:00Z')
        """,
        (
            DEFAULT_CONTENT_BANK_ID,
            DEFAULT_CONTENT_BANK_ID,
            DEFAULT_LANGUAGE_CODE,
            "German Core",
            "active",
        ),
    )


def seed_sqlite_default_bank_version(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO content_bank_versions (
            id, content_bank_id, version, status, activated_at, created_at
        ) VALUES (?, ?, ?, 'active', '2026-06-12T00:00:00Z', '2026-06-12T00:00:00Z')
        """,
        (DEFAULT_BANK_VERSION_ID, DEFAULT_CONTENT_BANK_ID, DEFAULT_BANK_VERSION),
    )


def seed_sqlite_default_activation_event(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO content_bank_activation_events (
            activation_event_id, content_bank_id, from_bank_version_id,
            to_bank_version_id, actor, reason, activated_at
        ) VALUES (?, ?, NULL, ?, 'system_migration', ?, '2026-06-12T00:00:00Z')
        """,
        (
            "activation:german-core:2026-06-12-baseline",
            DEFAULT_CONTENT_BANK_ID,
            DEFAULT_BANK_VERSION_ID,
            "Baseline German content bank activation",
        ),
    )


def ensure_sqlite_scope_columns(connection: sqlite3.Connection, table_name: str) -> None:
    if not sqlite_table_exists(connection, table_name):
        return
    existing_columns = sqlite_table_columns(connection, table_name)
    for column_name, column_sql in SCOPED_COLUMN_SQL.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
            )


def ensure_sqlite_quiz_item_scope(connection: sqlite3.Connection) -> None:
    if not sqlite_table_exists(connection, "quiz_items"):
        return
    if sqlite_quiz_items_scope_is_ready(connection):
        return
    rebuild_sqlite_quiz_items(connection)


def rebuild_sqlite_quiz_items(connection: sqlite3.Connection) -> None:
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS quiz_items_content_scope_migration")
    connection.executescript(
        f"""
        CREATE TABLE quiz_items_content_scope_migration (
            item_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL REFERENCES sources(source_id),
            language TEXT NOT NULL,
            language_code TEXT NOT NULL DEFAULT '{DEFAULT_LANGUAGE_CODE}' REFERENCES languages(code),
            content_bank_id TEXT NOT NULL DEFAULT '{DEFAULT_CONTENT_BANK_ID}'
                REFERENCES content_banks(id),
            bank_version_id TEXT NOT NULL DEFAULT '{DEFAULT_BANK_VERSION_ID}'
                REFERENCES content_bank_versions(id),
            level_band TEXT NOT NULL,
            sublevel TEXT NOT NULL,
            theme_id TEXT NOT NULL,
            subtheme_id TEXT NOT NULL,
            objective_id TEXT NOT NULL,
            pattern_id TEXT NOT NULL,
            difficulty_band TEXT NOT NULL,
            register TEXT NOT NULL,
            prompt TEXT NOT NULL,
            stem_text TEXT NOT NULL,
            options_json TEXT NOT NULL,
            answer_key TEXT NOT NULL,
            explanation TEXT NOT NULL,
            tags TEXT NOT NULL,
            coverage_cell_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN (
                    'draft',
                    'imported',
                    'normalized',
                    'needs_review',
                    'approved',
                    'published',
                    'monitored',
                    'retired',
                    'blocked'
                )
            ),
            version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            reviewed_at TEXT NOT NULL,
            level_locked TEXT NOT NULL,
            locked_at TEXT NOT NULL
        );
        """
    )
    connection.execute(sqlite_quiz_items_backfill_sql())
    connection.execute("DROP TABLE quiz_items")
    connection.execute("ALTER TABLE quiz_items_content_scope_migration RENAME TO quiz_items")
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")


def sqlite_quiz_items_backfill_sql() -> str:
    return f"""
        INSERT INTO quiz_items_content_scope_migration (
            item_id, source_id, language, language_code, content_bank_id,
            bank_version_id, level_band, sublevel, theme_id, subtheme_id,
            objective_id, pattern_id, difficulty_band, register, prompt,
            stem_text, options_json, answer_key, explanation, tags,
            coverage_cell_id, status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        )
        SELECT
            item_id, source_id, language, '{DEFAULT_LANGUAGE_CODE}',
            '{DEFAULT_CONTENT_BANK_ID}', '{DEFAULT_BANK_VERSION_ID}',
            level_band, sublevel, theme_id, subtheme_id, objective_id,
            pattern_id, difficulty_band, register, prompt, stem_text,
            options_json, answer_key, explanation, tags, coverage_cell_id,
            status, version, created_at, updated_at, reviewed_at,
            level_locked, locked_at
        FROM quiz_items
    """


def ensure_sqlite_scheduled_slot_scope(connection: sqlite3.Connection) -> None:
    if not sqlite_table_exists(connection, "scheduled_delivery_slots"):
        return
    if sqlite_scheduled_slot_scope_is_ready(connection):
        return
    rebuild_sqlite_scheduled_delivery_slots(connection)


def rebuild_sqlite_scheduled_delivery_slots(connection: sqlite3.Connection) -> None:
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS scheduled_delivery_slots_content_scope_migration")
    connection.executescript(
        f"""
        CREATE TABLE scheduled_delivery_slots_content_scope_migration (
            slot_run_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
            channel_id TEXT NOT NULL,
            delivery_date TEXT NOT NULL,
            slot_id TEXT NOT NULL,
            language_code TEXT NOT NULL DEFAULT '{DEFAULT_LANGUAGE_CODE}' CHECK (language_code <> ''),
            content_bank_id TEXT NOT NULL DEFAULT '{DEFAULT_CONTENT_BANK_ID}' CHECK (content_bank_id <> ''),
            bank_version_id TEXT NOT NULL DEFAULT '{DEFAULT_BANK_VERSION_ID}' CHECK (bank_version_id <> ''),
            cefr_level TEXT NOT NULL,
            theme_id TEXT NOT NULL,
            delivery_id TEXT REFERENCES deliveries(delivery_id),
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'created', 'sent', 'failed', 'skipped', 'no_item')
            ),
            failure_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (
                consumer_id,
                channel_id,
                delivery_date,
                slot_id,
                language_code,
                content_bank_id,
                bank_version_id,
                theme_id,
                cefr_level
            )
        );
        """
    )
    connection.execute(sqlite_scheduled_slots_backfill_sql())
    connection.execute("DROP TABLE scheduled_delivery_slots")
    connection.execute(
        """
        ALTER TABLE scheduled_delivery_slots_content_scope_migration
        RENAME TO scheduled_delivery_slots
        """
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")


def sqlite_scheduled_slots_backfill_sql() -> str:
    return f"""
        INSERT INTO scheduled_delivery_slots_content_scope_migration (
            slot_run_id, idempotency_key, consumer_id, channel_id,
            delivery_date, slot_id, language_code, content_bank_id,
            bank_version_id, cefr_level, theme_id, delivery_id, status,
            failure_reason, created_at, updated_at
        )
        SELECT
            slot_run_id, idempotency_key, consumer_id, channel_id,
            delivery_date, slot_id, '{DEFAULT_LANGUAGE_CODE}',
            '{DEFAULT_CONTENT_BANK_ID}', '{DEFAULT_BANK_VERSION_ID}',
            cefr_level, theme_id, delivery_id, status, failure_reason,
            created_at, updated_at
        FROM scheduled_delivery_slots
    """


def ensure_sqlite_scope_indexes(connection: sqlite3.Connection) -> None:
    connection.execute("DROP INDEX IF EXISTS idx_quiz_items_selection_pool")
    connection.execute("DROP INDEX IF EXISTS idx_quiz_items_cell_lookup")
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_quiz_items_delivery_filter
            ON quiz_items(status, sublevel, theme_id, objective_id, pattern_id);

        CREATE INDEX IF NOT EXISTS idx_quiz_items_selection_pool
            ON quiz_items(
                language_code,
                bank_version_id,
                status,
                sublevel,
                theme_id,
                objective_id,
                pattern_id,
                item_id
            );

        CREATE INDEX IF NOT EXISTS idx_quiz_items_cell_lookup
            ON quiz_items(language_code, bank_version_id, theme_id, pattern_id, item_id);

        CREATE INDEX IF NOT EXISTS idx_deliveries_scope_item
            ON deliveries(
                consumer_id,
                language_code,
                bank_version_id,
                delivery_status,
                quiz_item_id
            );

        CREATE INDEX IF NOT EXISTS idx_selection_decisions_scope_created
            ON selection_decisions(consumer_id, language_code, bank_version_id, created_at);

        CREATE INDEX IF NOT EXISTS idx_scheduled_delivery_slots_consumer_date
            ON scheduled_delivery_slots(consumer_id, delivery_date, status);

        CREATE INDEX IF NOT EXISTS idx_quota_usage_content_scope
            ON quota_usage(
                consumer_id,
                feature,
                usage_date,
                language_code,
                content_bank_id,
                bank_version_id
            );
        """
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


def sqlite_quiz_items_scope_is_ready(connection: sqlite3.Connection) -> bool:
    return (
        sqlite_table_has_columns(connection, "quiz_items", CONTENT_SCOPE_COLUMNS)
        and sqlite_quiz_items_has_bank_version_fk(connection)
    )


def sqlite_quiz_items_has_bank_version_fk(connection: sqlite3.Connection) -> bool:
    rows = connection.execute("PRAGMA foreign_key_list(quiz_items)").fetchall()
    return any(
        row["from"] == "bank_version_id"
        and row["table"] == "content_bank_versions"
        and row["to"] == "id"
        for row in rows
    )


def sqlite_scheduled_slot_scope_is_ready(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'scheduled_delivery_slots'
        """
    ).fetchone()
    if row is None or not sqlite_table_has_columns(
        connection,
        "scheduled_delivery_slots",
        CONTENT_SCOPE_COLUMNS,
    ):
        return False
    table_sql = str(row["sql"])
    return all(column_name in table_sql for column_name in CONTENT_SCOPE_COLUMNS)


def sqlite_active_german_bank_version_exists(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT cbv.id
        FROM content_bank_versions cbv
        JOIN content_banks cb ON cb.id = cbv.content_bank_id
        WHERE cb.language_code = ?
          AND cb.slug = ?
          AND cbv.id = ?
          AND cbv.status = 'active'
        """,
        (DEFAULT_LANGUAGE_CODE, DEFAULT_CONTENT_BANK_ID, DEFAULT_BANK_VERSION_ID),
    ).fetchone()
    return row is not None


def initialize_postgresql_database() -> None:
    with connect(None) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        for migration_path in sorted(POSTGRESQL_MIGRATIONS_DIRECTORY.glob("*.sql")):
            migration_id = migration_path.name
            row = connection.execute(
                "SELECT migration_id FROM schema_migrations WHERE migration_id = ?",
                (migration_id,),
            ).fetchone()
            if row is not None:
                continue
            connection.executescript(migration_path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO schema_migrations (migration_id, applied_at) VALUES (?, ?)",
                (migration_id, utc_now()),
            )


def postgresql_is_ready() -> bool:
    try:
        return RUNTIME_TABLES.issubset(postgresql_table_names())
    except Exception:
        return False


def postgresql_table_names() -> set[str]:
    with connect(None) as connection:
        rows = connection.execute(
            """
            SELECT table_name AS name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        ).fetchall()
    return {row["name"] for row in rows}
