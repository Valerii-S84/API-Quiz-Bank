"""Schema helpers for visual mode metadata columns."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Callable


VISUAL_METADATA_COLUMNS = {
    "visual_mode",
    "visual_target",
    "visual_context_hint",
    "visual_prompt_policy_version",
}
VISUAL_METADATA_TABLES = ("visual_assets", "visual_prompt_audit")
VISUAL_MODE_COLUMN_SQL = (
    "TEXT NOT NULL DEFAULT 'target_object' CHECK ("
    "visual_mode IN ('target_action', 'target_object', 'context_only', 'document_form', 'symbolic_abstract'))"
)


def sqlite_visual_metadata_is_ready(connect_fn: Callable[[Path], Any], path: Path) -> bool:
    return all(
        VISUAL_METADATA_COLUMNS.issubset(sqlite_table_columns(connect_fn, path, table_name))
        for table_name in VISUAL_METADATA_TABLES
    )


def sqlite_table_columns(connect_fn: Callable[[Path], Any], path: Path, table_name: str) -> set[str]:
    with connect_fn(path) as connection:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def ensure_visual_metadata_columns(connection: sqlite3.Connection) -> None:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    table_names = {row["name"] for row in rows}
    for table_name in VISUAL_METADATA_TABLES:
        if table_name in table_names:
            ensure_visual_metadata_table_columns(connection, table_name)


def ensure_visual_metadata_table_columns(connection: sqlite3.Connection, table_name: str) -> None:
    existing_columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}
    column_sql = {
        "visual_mode": VISUAL_MODE_COLUMN_SQL,
        "visual_target": "TEXT NOT NULL DEFAULT 'unknown' CHECK (visual_target <> '')",
        "visual_context_hint": "TEXT NOT NULL DEFAULT ''",
        "visual_prompt_policy_version": "TEXT NOT NULL DEFAULT 'unknown' CHECK (visual_prompt_policy_version <> '')",
    }
    for column_name, definition in column_sql.items():
        if column_name not in existing_columns:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def postgresql_visual_metadata_is_ready(connect_fn: Callable[[None], Any]) -> bool:
    with connect_fn(None) as connection:
        rows = connection.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name IN (?, ?)
            """,
            VISUAL_METADATA_TABLES,
        ).fetchall()
    columns_by_table: dict[str, set[str]] = {table_name: set() for table_name in VISUAL_METADATA_TABLES}
    for row in rows:
        columns_by_table[str(row["table_name"])].add(str(row["column_name"]))
    return all(VISUAL_METADATA_COLUMNS.issubset(columns) for columns in columns_by_table.values())
