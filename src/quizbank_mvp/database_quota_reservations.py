"""SQLite compatibility helpers for quota reservation schema."""

from __future__ import annotations

import sqlite3


def ensure_sqlite_quota_reservation_link(connection: sqlite3.Connection) -> None:
    if not sqlite_table_exists(connection, "deliveries"):
        return
    if "quota_reservation_id" not in sqlite_table_columns(connection, "deliveries"):
        connection.execute(
            """
            ALTER TABLE deliveries
            ADD COLUMN quota_reservation_id TEXT REFERENCES quota_reservations(quota_reservation_id)
            """
        )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_deliveries_quota_reservation
        ON deliveries(quota_reservation_id)
        WHERE quota_reservation_id IS NOT NULL
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
