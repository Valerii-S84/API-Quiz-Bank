"""Eligibility SQL for selecting quiz item candidates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from .database_connection import row_to_dict
from .database_status import DELIVERABLE_STATUSES
from .weighted_selection import select_ranked_candidate

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


CANDIDATE_POOL_LIMIT = 300


def find_eligible_item(
    connection,
    request: "SelectionRequest",
) -> tuple[dict[str, Any] | None, int]:
    candidates = enrich_candidates_with_delivery_metrics(
        connection,
        [row_to_dict(row) for row in fetch_candidate_pool(connection, request)],
    )
    return select_ranked_candidate(candidates, request), len(candidates)


def fetch_candidate_pool(connection, request: "SelectionRequest"):
    query = [
        """
        SELECT qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note,
               iq.theme_group, iq.image_quality_recommended,
               iq.image_quality_source, iq.image_quality_policy_share, iq.image_quality_override
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
        """
    ]
    parameters: list[Any] = []
    repeat_join_applied = append_repeat_policy_join(query, parameters, request)
    query.append(
        """
        WHERE qi.status IN (?, ?)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """
    )
    parameters.extend(DELIVERABLE_STATUSES)
    if repeat_join_applied:
        query.append("AND d_repeat.quiz_item_id IS NULL")
    append_filter(query, parameters, "qi.sublevel = ?", request.cefr_level)
    append_in_filter(query, parameters, "qi.theme_id", request.theme_ids)
    append_in_filter(query, parameters, "qi.objective_id", request.objective_ids)
    append_in_filter(query, parameters, "qi.pattern_id", request.pattern_ids)
    append_not_in_filter(query, parameters, "qi.item_id", request.excluded_item_ids)
    query.append(
        """
        ORDER BY qi.status ASC, qi.sublevel ASC, qi.theme_id ASC,
                 qi.objective_id ASC, qi.pattern_id ASC, qi.item_id ASC
        LIMIT ?
        """
    )
    parameters.append(CANDIDATE_POOL_LIMIT)
    return connection.execute(" ".join(query), parameters).fetchall()


def enrich_candidates_with_delivery_metrics(
    connection,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    item_metrics = load_item_delivery_metrics(
        connection,
        tuple(str(candidate["item_id"]) for candidate in candidates),
    )
    cell_counts = load_cell_delivery_counts(connection, candidates)
    enriched_candidates = []
    for candidate in candidates:
        item_id = str(candidate["item_id"])
        cell_key = (str(candidate["theme_id"]), str(candidate["pattern_id"]))
        metrics = item_metrics.get(item_id, {})
        enriched_candidates.append(
            {
                **candidate,
                "delivery_count": int(metrics.get("delivery_count", 0)),
                "last_delivered_at": str(metrics.get("last_delivered_at", "")),
                "cell_delivery_count": int(cell_counts.get(cell_key, 0)),
            }
        )
    return enriched_candidates


def load_item_delivery_metrics(
    connection,
    item_ids: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    placeholders = ", ".join("?" for _ in item_ids)
    rows = connection.execute(
        f"""
        SELECT quiz_item_id, COUNT(*) AS delivery_count,
               COALESCE(CAST(MAX(selected_at) AS TEXT), '') AS last_delivered_at
        FROM deliveries
        WHERE quiz_item_id IN ({placeholders})
        GROUP BY quiz_item_id
        """,
        item_ids,
    ).fetchall()
    return {str(row["quiz_item_id"]): row_to_dict(row) for row in rows}


def load_cell_delivery_counts(
    connection,
    candidates: list[dict[str, Any]],
) -> dict[tuple[str, str], int]:
    themes = tuple(sorted({str(candidate["theme_id"]) for candidate in candidates}))
    patterns = tuple(sorted({str(candidate["pattern_id"]) for candidate in candidates}))
    theme_placeholders = ", ".join("?" for _ in themes)
    pattern_placeholders = ", ".join("?" for _ in patterns)
    rows = connection.execute(
        f"""
        SELECT qi.theme_id, qi.pattern_id, COUNT(*) AS cell_delivery_count
        FROM quiz_items qi
        JOIN deliveries d ON d.quiz_item_id = qi.item_id
        WHERE qi.theme_id IN ({theme_placeholders})
          AND qi.pattern_id IN ({pattern_placeholders})
        GROUP BY qi.theme_id, qi.pattern_id
        """,
        (*themes, *patterns),
    ).fetchall()
    return {
        (str(row["theme_id"]), str(row["pattern_id"])): int(row["cell_delivery_count"])
        for row in rows
    }


def append_repeat_policy_join(
    query: list[str],
    parameters: list[Any],
    request: "SelectionRequest",
) -> bool:
    policy = request.policy.repeat_policy
    if not policy.enabled or not policy.blocked_delivery_statuses:
        return False
    placeholders = ", ".join("?" for _ in policy.blocked_delivery_statuses)
    query.append(
        f"""
        LEFT JOIN deliveries d_repeat
          ON d_repeat.consumer_id = ?
         AND d_repeat.quiz_item_id = qi.item_id
         AND d_repeat.delivery_status IN ({placeholders})
        """
    )
    parameters.extend([request.consumer_id, *policy.blocked_delivery_statuses])
    cutoff = repeat_window_cutoff(policy.repeat_window_days)
    if cutoff is not None:
        query.append("AND d_repeat.selected_at >= ?")
        parameters.append(cutoff)
    return True


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
