"""Database connection and shared persistence primitives."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import atexit
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
POSTGRES_POOL_DISABLED_VALUES = {"0", "false", "no", "off"}
DEFAULT_POSTGRES_POOL_MIN_SIZE = 1
DEFAULT_POSTGRES_POOL_MAX_SIZE = 5
DEFAULT_POSTGRES_POOL_TIMEOUT_SECONDS = 5.0
_POSTGRESQL_POOL_LOCK = threading.Lock()
_POSTGRESQL_POOLS: dict[str, Any] = {}


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
    pool = postgresql_connection_pool(database_url, dict_row)
    if pool is not None:
        return PostgreSQLConnection(context_manager=pool.connection())
    connection = psycopg.connect(database_url, row_factory=dict_row)
    return PostgreSQLConnection(connection)


def postgresql_connection_pool(database_url: str, row_factory: Any):
    if not postgresql_pool_enabled():
        return None
    try:
        from psycopg_pool import ConnectionPool
    except ImportError:
        return None
    with _POSTGRESQL_POOL_LOCK:
        pool = _POSTGRESQL_POOLS.get(database_url)
        if pool is None:
            pool = ConnectionPool(
                conninfo=database_url,
                min_size=postgresql_pool_min_size(),
                max_size=postgresql_pool_max_size(),
                timeout=postgresql_pool_timeout_seconds(),
                kwargs={"row_factory": row_factory},
            )
            _POSTGRESQL_POOLS[database_url] = pool
        return pool


def close_postgresql_pools() -> None:
    with _POSTGRESQL_POOL_LOCK:
        pools = list(_POSTGRESQL_POOLS.values())
        _POSTGRESQL_POOLS.clear()
    for pool in pools:
        pool.close()


def postgresql_pool_enabled() -> bool:
    raw_value = os.environ.get("QUIZBANK_POSTGRES_POOL_ENABLED", "1").strip().lower()
    return raw_value not in POSTGRES_POOL_DISABLED_VALUES


def postgresql_pool_min_size() -> int:
    return bounded_int_env("QUIZBANK_POSTGRES_POOL_MIN_SIZE", DEFAULT_POSTGRES_POOL_MIN_SIZE, 0, 20)


def postgresql_pool_max_size() -> int:
    minimum = max(1, postgresql_pool_min_size())
    return bounded_int_env("QUIZBANK_POSTGRES_POOL_MAX_SIZE", DEFAULT_POSTGRES_POOL_MAX_SIZE, minimum, 50)


def postgresql_pool_timeout_seconds() -> float:
    return bounded_float_env(
        "QUIZBANK_POSTGRES_POOL_TIMEOUT_SECONDS",
        DEFAULT_POSTGRES_POOL_TIMEOUT_SECONDS,
        0.1,
        60.0,
    )


def bounded_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def bounded_float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    raw_value = os.environ.get(name, str(default)).strip()
    try:
        value = float(raw_value)
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


class PostgreSQLConnection:
    def __init__(self, connection=None, context_manager=None) -> None:
        self.connection = connection
        self.context_manager = context_manager

    def __enter__(self) -> "PostgreSQLConnection":
        if self.context_manager is not None:
            self.connection = self.context_manager.__enter__()
            return self
        if self.connection is None:
            raise RuntimeError("PostgreSQL connection is not configured")
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.context_manager is not None:
            self.context_manager.__exit__(exc_type, exc_value, traceback)
            self.connection = None
            return
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


atexit.register(close_postgresql_pools)
