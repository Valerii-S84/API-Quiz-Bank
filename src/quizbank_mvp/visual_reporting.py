"""Visual delivery reporting aggregates for admin and smoke evidence."""

from __future__ import annotations

from pathlib import Path

from .database_connection import connect


VISUAL_OUTCOME_EVENTS = ("cache_hit", "generation_succeeded", "fallback_used")


def visual_metrics_summary(db_path: Path | None) -> dict[str, object]:
    with connect(db_path) as connection:
        event_counts = count_visual_events(connection)
        event_counts_by_bank_version = count_visual_events_by_bank_version(connection)
        settings_by_mode = count_visual_settings_by_mode(connection)
        generation_count_by_consumer = count_generation_requests_by_consumer(connection)
        estimated_cost_minor_by_consumer = sum_estimated_cost_by_consumer(connection)
    outcome_count = sum(event_counts.get(event_type, 0) for event_type in VISUAL_OUTCOME_EVENTS)
    return {
        "settings_by_mode": settings_by_mode,
        "event_counts": event_counts,
        "event_counts_by_bank_version": event_counts_by_bank_version,
        "cache_hit_rate": ratio(event_counts.get("cache_hit", 0), outcome_count),
        "fallback_rate": ratio(event_counts.get("fallback_used", 0), outcome_count),
        "generation_count_by_consumer": generation_count_by_consumer,
        "qa_rejection_count": event_counts.get("qa_rejected", 0),
        "estimated_cost_minor_by_consumer": estimated_cost_minor_by_consumer,
        "estimated_cost_minor_total": sum(estimated_cost_minor_by_consumer.values()),
    }


def count_visual_events(connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT event_type, COALESCE(SUM(quantity), 0) AS count
        FROM visual_usage_events
        GROUP BY event_type
        """
    ).fetchall()
    return {str(row["event_type"]): int(row["count"]) for row in rows}


def count_visual_events_by_bank_version(connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT COALESCE(d.language_code, va.language_code, 'de') AS scoped_language_code,
               COALESCE(d.content_bank_id, va.content_bank_id, 'german-core') AS scoped_content_bank_id,
               COALESCE(
                   d.bank_version_id,
                   va.bank_version_id,
                   'german-core:2026-06-12-baseline'
               ) AS scoped_bank_version_id,
               e.event_type,
               COALESCE(SUM(e.quantity), 0) AS count
        FROM visual_usage_events e
        LEFT JOIN deliveries d ON d.delivery_id = e.delivery_id
        LEFT JOIN visual_assets va ON va.asset_id = e.asset_id
        GROUP BY scoped_language_code, scoped_content_bank_id, scoped_bank_version_id, e.event_type
        ORDER BY scoped_language_code, scoped_content_bank_id, scoped_bank_version_id, e.event_type
        """
    ).fetchall()
    return [
        {
            "language_code": str(row["scoped_language_code"]),
            "content_bank_id": str(row["scoped_content_bank_id"]),
            "bank_version_id": str(row["scoped_bank_version_id"]),
            "event_type": str(row["event_type"]),
            "count": int(row["count"]),
        }
        for row in rows
    ]


def count_visual_settings_by_mode(connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT delivery_mode, COUNT(*) AS count
        FROM consumer_visual_settings
        GROUP BY delivery_mode
        """
    ).fetchall()
    return {str(row["delivery_mode"]): int(row["count"]) for row in rows}


def count_generation_requests_by_consumer(connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT consumer_id, COALESCE(SUM(quantity), 0) AS count
        FROM visual_usage_events
        WHERE event_type = 'generation_requested'
        GROUP BY consumer_id
        """
    ).fetchall()
    return {str(row["consumer_id"]): int(row["count"]) for row in rows}


def sum_estimated_cost_by_consumer(connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT consumer_id, COALESCE(SUM(estimated_cost_minor), 0) AS total
        FROM visual_usage_events
        GROUP BY consumer_id
        """
    ).fetchall()
    return {str(row["consumer_id"]): int(row["total"]) for row in rows}


def ratio(part: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(part / total, 4)
