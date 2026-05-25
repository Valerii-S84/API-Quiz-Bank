"""Runtime analytics snapshots for MVP selection and delivery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .database_connection import connect, decode_json_field, utc_now


def selection_analytics_snapshot(db_path: Path | None) -> dict[str, object]:
    with connect(db_path) as connection:
        return {
            "generated_at": utc_now(),
            "inventory": {
                "by_level": grouped_counts(connection, "quiz_items", "sublevel"),
                "by_theme": grouped_counts(connection, "quiz_items", "theme_id"),
                "by_objective": grouped_counts(connection, "quiz_items", "objective_id"),
                "by_pattern": grouped_counts(connection, "quiz_items", "pattern_id"),
            },
            "deliveries": deliveries_by_consumer_theme_pattern(connection),
            "repeat_blocks": repeat_blocks(connection),
            "no_candidate_reasons": no_candidate_reasons(connection),
        }


def grouped_counts(connection, table: str, column: str) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT {column} AS key, COUNT(*) AS count
        FROM {table}
        GROUP BY {column}
        ORDER BY {column}
        """
    ).fetchall()
    return {str(row["key"]): int(row["count"]) for row in rows}


def deliveries_by_consumer_theme_pattern(connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT d.consumer_id, qi.theme_id, qi.pattern_id, COUNT(*) AS count
        FROM deliveries d
        JOIN quiz_items qi ON qi.item_id = d.quiz_item_id
        GROUP BY d.consumer_id, qi.theme_id, qi.pattern_id
        ORDER BY d.consumer_id, qi.theme_id, qi.pattern_id
        """
    ).fetchall()
    return [
        {
            "consumer_id": str(row["consumer_id"]),
            "theme_id": str(row["theme_id"]),
            "pattern_id": str(row["pattern_id"]),
            "count": int(row["count"]),
        }
        for row in rows
    ]


def repeat_blocks(connection) -> int:
    rows = connection.execute("SELECT blocked_reason_counts_json FROM selection_decisions").fetchall()
    return sum(reason_count(row, "repeat_policy") for row in rows)


def no_candidate_reasons(connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT fallback_reason_code, COUNT(*) AS count
        FROM selection_decisions
        WHERE fallback_reason_code IS NOT NULL
        GROUP BY fallback_reason_code
        ORDER BY fallback_reason_code
        """
    ).fetchall()
    return {str(row["fallback_reason_code"]): int(row["count"]) for row in rows}


def reason_count(row: Any, key: str) -> int:
    try:
        counts = decode_json_field(row["blocked_reason_counts_json"])
    except (json.JSONDecodeError, TypeError):
        return 0
    return int(counts.get(key, 0))
