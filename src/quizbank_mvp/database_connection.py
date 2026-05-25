"""Database connection and shared persistence primitives."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from .time_ids import new_id, today_usage_date, utc_now


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "var" / "quizbank_mvp.sqlite3"
POSTGRESQL_UNSUPPORTED_SQL_PATTERNS = (
    (re.compile(r"\bPRAGMA\b", re.IGNORECASE), "SQLite PRAGMA statements"),
    (re.compile(r"\bsqlite_master\b", re.IGNORECASE), "SQLite sqlite_master metadata"),
    (re.compile(r"\bINSERT\s+OR\s+REPLACE\b", re.IGNORECASE), "SQLite INSERT OR REPLACE"),
    (re.compile(r"\blast_insert_rowid\s*\(", re.IGNORECASE), "SQLite last_insert_rowid()"),
)


class PostgreSQLUnsupportedSQLError(RuntimeError):
    """Raised when PostgreSQL runtime receives SQLite-specific SQL."""


def configured_db_path() -> Path:
    return Path(os.environ.get("QUIZBANK_DB_PATH", DEFAULT_DB_PATH)).resolve()


def configured_database_url() -> str | None:
    return os.environ.get("QUIZBANK_DATABASE_URL") or os.environ.get("DATABASE_URL")


def connect(db_path: Path | None = None):
    if db_path is None and configured_database_url():
        return connect_postgresql(configured_database_url() or "")
    path = (db_path or configured_db_path()).resolve()
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def connect_postgresql(database_url: str):
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as error:  # pragma: no cover - exercised in deployment image
        raise RuntimeError("PostgreSQL runtime requires psycopg") from error
    connection = psycopg.connect(database_url, row_factory=dict_row)
    return PostgreSQLConnection(connection)


class PostgreSQLConnection:
    def __init__(self, connection) -> None:
        self.connection = connection

    def __enter__(self) -> "PostgreSQLConnection":
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.connection.__exit__(exc_type, exc_value, traceback)
        self.connection.close()

    def execute(self, sql: str, parameters: Any = None):
        ensure_postgresql_supported_sql(sql)
        translated_sql = translate_sqlite_placeholders(sql, parameters)
        return self.connection.execute(translated_sql, parameters)

    def executescript(self, script: str) -> None:
        ensure_postgresql_supported_sql(script)
        self.connection.execute(script)

    def rollback(self) -> None:
        self.connection.rollback()


def translate_sqlite_placeholders(sql: str, parameters: Any = None) -> str:
    if isinstance(parameters, dict):
        return re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", sql)
    if parameters is not None:
        return sql.replace("?", "%s")
    return sql


def ensure_postgresql_supported_sql(sql: str) -> None:
    for pattern, description in POSTGRESQL_UNSUPPORTED_SQL_PATTERNS:
        if pattern.search(sql):
            raise PostgreSQLUnsupportedSQLError(
                f"PostgreSQL runtime does not support {description}"
            )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def decode_json_field(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    return json.loads(str(value))
