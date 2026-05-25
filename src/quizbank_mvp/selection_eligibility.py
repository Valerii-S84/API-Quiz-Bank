"""Eligibility SQL for selecting quiz item candidates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from .database_connection import row_to_dict
from .database_status import DELIVERABLE_STATUSES
from .weighted_selection import select_ranked_candidate

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


def find_eligible_item(
    connection,
    request: "SelectionRequest",
) -> tuple[dict[str, Any] | None, int]:
    query = [
        """
        SELECT qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note,
               iq.theme_group, iq.image_quality_recommended,
               iq.image_quality_source, iq.image_quality_policy_share, iq.image_quality_override,
               (
                   SELECT COUNT(*)
                   FROM deliveries d_all
                   WHERE d_all.quiz_item_id = qi.item_id
               ) AS delivery_count,
               COALESCE((
                   SELECT CAST(MAX(d_last.selected_at) AS TEXT)
                   FROM deliveries d_last
                   WHERE d_last.quiz_item_id = qi.item_id
               ), '') AS last_delivered_at,
               (
                   SELECT COUNT(*)
                   FROM deliveries d_cell
                   JOIN quiz_items qi_cell ON qi_cell.item_id = d_cell.quiz_item_id
                   WHERE qi_cell.theme_id = qi.theme_id
                     AND qi_cell.pattern_id = qi.pattern_id
               ) AS cell_delivery_count
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
        WHERE qi.status IN (?, ?)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """
    ]
    parameters: list[Any] = [*DELIVERABLE_STATUSES]
    append_repeat_policy_filter(query, parameters, request)
    append_filter(query, parameters, "qi.sublevel = ?", request.cefr_level)
    append_in_filter(query, parameters, "qi.theme_id", request.theme_ids)
    append_in_filter(query, parameters, "qi.objective_id", request.objective_ids)
    append_in_filter(query, parameters, "qi.pattern_id", request.pattern_ids)
    append_not_in_filter(query, parameters, "qi.item_id", request.excluded_item_ids)
    query.append("ORDER BY qi.item_id ASC")
    rows = connection.execute(" ".join(query), parameters).fetchall()
    candidates = [row_to_dict(row) for row in rows]
    return select_ranked_candidate(candidates, request), len(candidates)


def append_filter(query: list[str], parameters: list[Any], clause: str, value: Any) -> None:
    if value is None:
        return
    query.append(f"AND {clause}")
    parameters.append(value)


def append_in_filter(
    query: list[str],
    parameters: list[Any],
    column: str,
    values: tuple[str, ...],
) -> None:
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    query.append(f"AND {column} IN ({placeholders})")
    parameters.extend(values)


def append_not_in_filter(
    query: list[str],
    parameters: list[Any],
    column: str,
    values: tuple[str, ...],
) -> None:
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    query.append(f"AND {column} NOT IN ({placeholders})")
    parameters.extend(values)


def append_repeat_policy_filter(
    query: list[str],
    parameters: list[Any],
    request: "SelectionRequest",
) -> None:
    policy = request.policy.repeat_policy
    if not policy.enabled or not policy.blocked_delivery_statuses:
        return
    placeholders = ", ".join("?" for _ in policy.blocked_delivery_statuses)
    query.append(
        f"""
        AND NOT EXISTS (
            SELECT 1 FROM deliveries d
            WHERE d.consumer_id = ?
              AND d.quiz_item_id = qi.item_id
              AND d.delivery_status IN ({placeholders})
        """
    )
    parameters.extend([request.consumer_id, *policy.blocked_delivery_statuses])
    cutoff = repeat_window_cutoff(policy.repeat_window_days)
    if cutoff is not None:
        query.append("AND d.selected_at >= ?")
        parameters.append(cutoff)
    query.append(")")


def repeat_window_cutoff(repeat_window_days: int | None) -> str | None:
    if repeat_window_days is None:
        return None
    cutoff = datetime.now(UTC).replace(microsecond=0) - timedelta(days=repeat_window_days)
    return cutoff.isoformat().replace("+00:00", "Z")
