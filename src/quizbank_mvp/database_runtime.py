"""Database migration and readiness checks."""

from __future__ import annotations

from pathlib import Path

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


def initialize_database(db_path: Path | None = None):
    if db_path is None and configured_database_url():
        initialize_postgresql_database()
        return "postgresql"
    path = (db_path or configured_db_path()).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        for migration_path in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
            connection.executescript(migration_path.read_text(encoding="utf-8"))
        ensure_visual_metadata_columns(connection)
    return path


def database_is_ready(db_path: Path | None = None) -> bool:
    if db_path is None and configured_database_url():
        return postgresql_is_ready()
    path = (db_path or configured_db_path()).resolve()
    return path.exists() and RUNTIME_TABLES.issubset(sqlite_table_names(path))


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
