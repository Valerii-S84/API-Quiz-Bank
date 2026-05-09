"""Selection candidate diagnostics for decision logging."""

from __future__ import annotations

from typing import Any

from .database import DELIVERABLE_STATUSES


def candidate_count(connection, request: Any) -> int:
    query = [
        """
        SELECT COUNT(*) AS count
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        WHERE qi.status IN (?, ?)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """
    ]
    parameters: list[Any] = [*DELIVERABLE_STATUSES]
    append_taxonomy_filters(query, parameters, request)
    row = connection.execute(" ".join(query), parameters).fetchone()
    return int(row["count"])


def blocked_reason_counts(connection, request: Any) -> dict[str, int]:
    return {
        "non_deliverable_status": non_deliverable_status_count(connection, request),
        "repeat_policy": repeat_policy_block_count(connection, request),
        "explicit_exclusion": len(request.excluded_item_ids),
    }


def non_deliverable_status_count(connection, request: Any) -> int:
    query = [
        """
        SELECT COUNT(*) AS count
        FROM quiz_items qi
        WHERE qi.status NOT IN (?, ?)
        """
    ]
    parameters: list[Any] = [*DELIVERABLE_STATUSES]
    append_taxonomy_filters(query, parameters, request)
    row = connection.execute(" ".join(query), parameters).fetchone()
    return int(row["count"])


def repeat_policy_block_count(connection, request: Any) -> int:
    policy = request.policy.repeat_policy
    if not policy.enabled or not policy.blocked_delivery_statuses:
        return 0
    placeholders = ", ".join("?" for _ in policy.blocked_delivery_statuses)
    query = [
        f"""
        SELECT COUNT(DISTINCT qi.item_id) AS count
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        JOIN deliveries d ON d.quiz_item_id = qi.item_id
        WHERE qi.status IN (?, ?)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
          AND d.consumer_id = ?
          AND d.delivery_status IN ({placeholders})
        """
    ]
    parameters: list[Any] = [
        *DELIVERABLE_STATUSES,
        request.consumer_id,
        *policy.blocked_delivery_statuses,
    ]
    append_taxonomy_filters(query, parameters, request)
    row = connection.execute(" ".join(query), parameters).fetchone()
    return int(row["count"])


def append_taxonomy_filters(query: list[str], parameters: list[Any], request: Any) -> None:
    append_filter(query, parameters, "qi.sublevel = ?", request.cefr_level)
    append_in_filter(query, parameters, "qi.theme_id", request.theme_ids)
    append_in_filter(query, parameters, "qi.objective_id", request.objective_ids)
    append_in_filter(query, parameters, "qi.pattern_id", request.pattern_ids)


def append_filter(query: list[str], parameters: list[Any], clause: str, value: Any) -> None:
    if value is None:
        return
    query.append(f"AND {clause}")
    parameters.append(value)


def append_in_filter(query: list[str], parameters: list[Any], column: str, values) -> None:
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    query.append(f"AND {column} IN ({placeholders})")
    parameters.extend(values)
