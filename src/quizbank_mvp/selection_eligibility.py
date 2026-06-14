"""Eligibility SQL for selecting quiz item candidates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from .database_connection import row_to_dict
from .database_status import DELIVERABLE_STATUSES
from .weighted_selection import candidate_score, select_ranked_candidate

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


CANDIDATE_POOL_LIMIT = 150
HISTORY_SCORING_CANDIDATE_LIMIT = 24


def find_eligible_item(
    connection,
    request: "SelectionRequest",
) -> tuple[dict[str, Any] | None, int]:
    candidates = [row_to_dict(row) for row in fetch_candidate_pool(connection, request)]
    candidate_count = len(candidates)
    if request.selection_strategy == "first_eligible":
        return select_ranked_candidate(candidates, request), candidate_count
    scored_candidates = enrich_candidates_with_delivery_metrics(
        connection,
        history_metric_candidates(candidates, request),
        request,
    )
    return select_ranked_candidate(scored_candidates, request), candidate_count


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
          AND qi.language_code = ?
          AND qi.bank_version_id = ?
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """
    )
    parameters.extend(
        [
            *DELIVERABLE_STATUSES,
            request.language_code,
            request.bank_version_id,
        ]
    )
    if repeat_join_applied:
        query.append("AND state_repeat.quiz_item_id IS NULL")
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
    request: "SelectionRequest",
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    item_metrics = load_item_delivery_metrics(
        connection,
        tuple(str(candidate["item_id"]) for candidate in candidates),
        request,
    )
    enriched_candidates = []
    for candidate in candidates:
        item_id = str(candidate["item_id"])
        metrics = item_metrics.get(item_id, {})
        enriched_candidates.append(
            {
                **candidate,
                "delivery_count": int(metrics.get("delivery_count", 0)),
                "last_delivered_at": str(metrics.get("last_delivered_at", "")),
                "cell_delivery_count": 0,
            }
        )
    return enriched_candidates


def history_metric_candidates(
    candidates: list[dict[str, Any]],
    request: "SelectionRequest",
) -> list[dict[str, Any]]:
    if len(candidates) <= HISTORY_SCORING_CANDIDATE_LIMIT:
        return candidates
    scored_candidates = [
        (candidate_score(candidate, request).total, candidate)
        for candidate in candidates
    ]
    scored_candidates.sort(
        key=lambda scored: (scored[0], str(scored[1]["item_id"])),
        reverse=True,
    )
    return [candidate for _score, candidate in scored_candidates[:HISTORY_SCORING_CANDIDATE_LIMIT]]


def load_item_delivery_metrics(
    connection,
    item_ids: tuple[str, ...],
    request: "SelectionRequest",
) -> dict[str, dict[str, Any]]:
    placeholders = ", ".join("?" for _ in item_ids)
    rows = connection.execute(
        f"""
        SELECT quiz_item_id, delivery_count,
               COALESCE(CAST(last_delivered_at AS TEXT), '') AS last_delivered_at
        FROM consumer_delivery_state
        WHERE consumer_id = ?
          AND channel_id = ?
          AND quiz_item_id IN ({placeholders})
          AND language_code = ?
          AND content_bank_id = ?
          AND bank_version_id = ?
        """,
        (
            request.consumer_id,
            request.consumer_profile.delivery_channel,
            *item_ids,
            request.language_code,
            request.content_bank_id,
            request.bank_version_id,
        ),
    ).fetchall()
    return {str(row["quiz_item_id"]): row_to_dict(row) for row in rows}


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
        LEFT JOIN consumer_delivery_state state_repeat
          ON state_repeat.consumer_id = ?
         AND state_repeat.channel_id = ?
         AND state_repeat.quiz_item_id = qi.item_id
         AND state_repeat.language_code = ?
         AND state_repeat.content_bank_id = ?
         AND state_repeat.bank_version_id = ?
         AND state_repeat.last_delivery_status IN ({placeholders})
        """
    )
    parameters.extend(
        [
            request.consumer_id,
            request.consumer_profile.delivery_channel,
            request.language_code,
            request.content_bank_id,
            request.bank_version_id,
            *policy.blocked_delivery_statuses,
        ]
    )
    cutoff = repeat_window_cutoff(policy.repeat_window_days)
    if cutoff is not None:
        query.append("AND state_repeat.last_delivered_at >= ?")
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
            SELECT 1 FROM consumer_delivery_state state_repeat
            WHERE state_repeat.consumer_id = ?
              AND state_repeat.channel_id = ?
              AND state_repeat.quiz_item_id = qi.item_id
              AND state_repeat.language_code = ?
              AND state_repeat.content_bank_id = ?
              AND state_repeat.bank_version_id = ?
              AND state_repeat.last_delivery_status IN ({placeholders})
        """
    )
    parameters.extend(
        [
            request.consumer_id,
            request.consumer_profile.delivery_channel,
            request.language_code,
            request.content_bank_id,
            request.bank_version_id,
            *policy.blocked_delivery_statuses,
        ]
    )
    cutoff = repeat_window_cutoff(policy.repeat_window_days)
    if cutoff is not None:
        query.append("AND state_repeat.last_delivered_at >= ?")
        parameters.append(cutoff)
    query.append(")")


def repeat_window_cutoff(repeat_window_days: int | None) -> str | None:
    if repeat_window_days is None:
        return None
    cutoff = datetime.now(UTC).replace(microsecond=0) - timedelta(days=repeat_window_days)
    return cutoff.isoformat().replace("+00:00", "Z")
