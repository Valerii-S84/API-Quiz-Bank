"""Async queue refill helpers for precomputed selection state."""

from __future__ import annotations

from dataclasses import replace
import json
from itertools import product
from pathlib import Path
from typing import Any

from .database_connection import connect, row_to_dict
from .selection_eligibility import repeat_window_cutoff
from .selection_models import ContentScope, SelectionRequest, SelectionTargetMix
from .selection_queue_models import (
    DEFAULT_QUEUE_CHANNELS,
    DEFAULT_QUEUE_TARGET_SIZE,
    QueueRefillResult,
    QueueScope,
    normalized_channels,
    selection_queue_id,
    selection_queue_item_id,
    validate_target_size,
)
from .selection_scope import effective_scope_replacement, resolve_content_scope_request
from .selection_scope_enforcement import (
    enforce_consumer_scope,
    enforce_entitlement_scope,
    load_active_consumer,
    load_active_entitlement,
)
from .time_ids import utc_now
from .weighted_selection import candidate_score


def refill_selection_queues(
    db_path: Path | None,
    channel_ids: tuple[str, ...] = DEFAULT_QUEUE_CHANNELS,
    target_size: int = DEFAULT_QUEUE_TARGET_SIZE,
    language_code: str = "de",
    content_bank_id: str | None = None,
    bank_version_id: str | None = None,
    target_mix: SelectionTargetMix | None = None,
) -> dict[str, object]:
    validate_target_size(target_size)
    channels = normalized_channels(channel_ids)
    with connect(db_path) as connection:
        consumer_ids = load_entitled_consumer_ids(connection)
        results = [
            result
            for consumer_id in consumer_ids
            for channel_id in channels
            for result in refill_consumer_channel(
                connection,
                consumer_id,
                channel_id,
                target_size,
                ContentScope(language_code, content_bank_id, bank_version_id),
                target_mix or SelectionTargetMix(),
            )
        ]
    return refill_summary(target_size, consumer_ids, channels, results)


def refill_selection_queue_for_request(
    db_path: Path | None,
    request: SelectionRequest,
    target_size: int = DEFAULT_QUEUE_TARGET_SIZE,
) -> dict[str, object]:
    validate_target_size(target_size)
    with connect(db_path) as connection:
        prepared_request = prepare_queue_request(connection, request)
        results = refill_prepared_selection_queues(connection, prepared_request, target_size)
    channel_id = prepared_request.consumer_profile.delivery_channel
    return refill_summary(target_size, [prepared_request.consumer_id], [channel_id], results)


def refill_prepared_selection_queues(
    connection: Any,
    request: SelectionRequest,
    target_size: int = DEFAULT_QUEUE_TARGET_SIZE,
) -> list[QueueRefillResult]:
    validate_target_size(target_size)
    return [
        refill_queue_scope(connection, request, scope, target_size)
        for scope in queue_scopes_for_request(request)
    ]


def refill_consumer_channel(
    connection: Any,
    consumer_id: str,
    channel_id: str,
    target_size: int,
    content_scope: ContentScope,
    target_mix: SelectionTargetMix,
) -> list[QueueRefillResult]:
    request = SelectionRequest(
        consumer_id=consumer_id,
        delivery_mode=channel_id,
        content_scope=content_scope,
        target_mix=target_mix,
    )
    prepared_request = prepare_queue_request(connection, request)
    return refill_prepared_selection_queues(connection, prepared_request, target_size)


def prepare_queue_request(connection: Any, request: SelectionRequest) -> SelectionRequest:
    consumer = load_active_consumer(connection, request.consumer_id)
    entitlement = load_active_entitlement(connection, request)
    request = replace(request, **effective_scope_replacement(request, consumer, entitlement))
    request = resolve_content_scope_request(connection, request, consumer)
    enforce_consumer_scope(consumer, request)
    enforce_entitlement_scope(entitlement, request)
    return request


def queue_scopes_for_request(request: SelectionRequest) -> list[QueueScope]:
    return [
        QueueScope(
            request.consumer_id,
            request.consumer_profile.delivery_channel,
            str(request.language_code),
            str(request.content_bank_id),
            str(request.bank_version_id),
            cefr_level,
            theme_id,
            objective_id,
            pattern_id,
        )
        for cefr_level, theme_id, objective_id, pattern_id in product(
            values_or_blank(request.cefr_level),
            values_or_blank(request.theme_ids),
            values_or_blank(request.objective_ids),
            values_or_blank(request.pattern_ids),
        )
    ]


def refill_queue_scope(
    connection: Any,
    request: SelectionRequest,
    scope: QueueScope,
    target_size: int,
) -> QueueRefillResult:
    queue_id = selection_queue_id(scope)
    existing = load_selection_queue(connection, queue_id)
    if existing and existing["queue_status"] == "disabled":
        return disabled_queue_result(queue_id, scope, target_size, existing)
    upsert_selection_queue(connection, queue_id, scope, target_size)
    available_count = queue_available_count(connection, queue_id)
    added_count = insert_refill_candidates(
        connection,
        queue_id,
        request,
        scope,
        max(0, target_size - available_count),
    )
    available_count = update_queue_availability(connection, queue_id)
    return QueueRefillResult(
        queue_id,
        scope,
        target_size,
        added_count,
        available_count,
        queue_status(available_count),
    )


def insert_refill_candidates(
    connection: Any,
    queue_id: str,
    request: SelectionRequest,
    scope: QueueScope,
    needed_count: int,
) -> int:
    if needed_count <= 0:
        return 0
    candidates = load_queue_candidates(connection, queue_id, request, scope)
    candidates = ranked_queue_candidates(candidates, request)
    start_position = next_queue_position(connection, queue_id)
    for offset, candidate in enumerate(candidates[:needed_count]):
        insert_queue_item(connection, queue_id, start_position + offset, candidate)
    return min(needed_count, len(candidates))


def load_queue_candidates(
    connection: Any,
    queue_id: str,
    request: SelectionRequest,
    scope: QueueScope,
) -> list[dict[str, Any]]:
    query = [queue_candidate_sql()]
    parameters: list[Any] = [
        queue_id,
        scope.consumer_id,
        scope.channel_id,
        scope.language_code,
        scope.content_bank_id,
        scope.bank_version_id,
        scope.language_code,
        scope.content_bank_id,
        scope.bank_version_id,
    ]
    append_scope_filters(query, parameters, scope)
    append_repeat_filter(query, parameters, request)
    append_exclusion_filter(query, parameters, request.excluded_item_ids)
    query.append("ORDER BY cpi.rank_position ASC, cpi.item_id ASC")
    rows = connection.execute(" ".join(query), tuple(parameters)).fetchall()
    return [candidate_row(row) for row in rows]


def queue_candidate_sql() -> str:
    return """
        SELECT cpi.pool_id, cpi.item_id, cpi.rank_position,
               qi.sublevel, qi.theme_id, qi.objective_id, qi.pattern_id,
               COALESCE(state.delivery_count, 0) AS delivery_count,
               COALESCE(CAST(state.last_delivered_at AS TEXT), '') AS last_delivered_at
        FROM candidate_pool_items cpi
        JOIN candidate_pools cp ON cp.pool_id = cpi.pool_id
        JOIN quiz_items qi ON qi.item_id = cpi.item_id
        LEFT JOIN selection_queue_items queued
          ON queued.queue_id = ? AND queued.item_id = cpi.item_id
        LEFT JOIN consumer_delivery_state state
          ON state.consumer_id = ?
         AND state.channel_id = ?
         AND state.quiz_item_id = cpi.item_id
         AND state.language_code = ?
         AND state.content_bank_id = ?
         AND state.bank_version_id = ?
        WHERE cp.pool_status = 'ready'
          AND cp.language_code = ?
          AND cp.content_bank_id = ?
          AND cp.bank_version_id = ?
          AND queued.item_id IS NULL
    """


def append_scope_filters(query: list[str], parameters: list[Any], scope: QueueScope) -> None:
    for column, value in (
        ("cp.cefr_level", scope.cefr_level),
        ("cp.theme_id", scope.theme_id),
        ("cp.objective_id", scope.objective_id),
        ("cp.pattern_id", scope.pattern_id),
    ):
        if value:
            query.append(f"AND {column} = ?")
            parameters.append(value)


def append_repeat_filter(
    query: list[str],
    parameters: list[Any],
    request: SelectionRequest,
) -> None:
    policy = request.policy.repeat_policy
    if not policy.enabled or not policy.blocked_delivery_statuses:
        return
    placeholders = ", ".join("?" for _ in policy.blocked_delivery_statuses)
    query.append(
        "AND (state.quiz_item_id IS NULL "
        f"OR state.last_delivery_status NOT IN ({placeholders})"
    )
    parameters.extend(policy.blocked_delivery_statuses)
    cutoff = repeat_window_cutoff(policy.repeat_window_days)
    if cutoff is not None:
        query.append("OR state.last_delivered_at < ? OR state.last_delivered_at IS NULL")
        parameters.append(cutoff)
    query.append(")")


def append_exclusion_filter(
    query: list[str],
    parameters: list[Any],
    excluded_item_ids: tuple[str, ...],
) -> None:
    if not excluded_item_ids:
        return
    placeholders = ", ".join("?" for _ in excluded_item_ids)
    query.append(f"AND cpi.item_id NOT IN ({placeholders})")
    parameters.extend(excluded_item_ids)


def ranked_queue_candidates(
    candidates: list[dict[str, Any]],
    request: SelectionRequest,
) -> list[dict[str, Any]]:
    if request.selection_strategy == "first_eligible":
        return sorted(candidates, key=lambda candidate: str(candidate["item_id"]))
    scored = [(candidate_score(candidate, request), candidate) for candidate in candidates]
    ranked = []
    for score, candidate in sorted(scored, key=scored_candidate_key, reverse=True):
        ranked.append({**candidate, "_selection_score": score.to_context()})
    return ranked


def scored_candidate_key(scored: tuple[Any, dict[str, Any]]) -> tuple[float, str]:
    return scored[0].total, str(scored[1]["item_id"])


def insert_queue_item(
    connection: Any,
    queue_id: str,
    position: int,
    candidate: dict[str, Any],
) -> None:
    now = utc_now()
    connection.execute(
        """
        INSERT INTO selection_queue_items (
            queue_item_id, queue_id, pool_id, item_id, position, claim_status,
            claim_token, claimed_at, claim_expires_at, delivery_id,
            score_snapshot_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'available', NULL, NULL, NULL, NULL, ?, ?, ?)
        """,
        (
            selection_queue_item_id(queue_id, str(candidate["item_id"])),
            queue_id,
            candidate["pool_id"],
            candidate["item_id"],
            position,
            stable_json(queue_item_score_snapshot(candidate)),
            now,
            now,
        ),
    )


def upsert_selection_queue(
    connection: Any,
    queue_id: str,
    scope: QueueScope,
    target_size: int,
) -> None:
    now = utc_now()
    connection.execute(
        """
        INSERT INTO selection_queues (
            queue_id, consumer_id, channel_id, language_code, content_bank_id,
            bank_version_id, cefr_level, theme_id, objective_id, pattern_id,
            queue_status, target_size, available_count, refill_after_at,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'warming', ?, 0, NULL, ?, ?)
        ON CONFLICT(queue_id) DO UPDATE SET
            target_size = excluded.target_size,
            updated_at = excluded.updated_at
        """,
        (
            queue_id,
            scope.consumer_id,
            scope.channel_id,
            scope.language_code,
            scope.content_bank_id,
            scope.bank_version_id,
            scope.cefr_level,
            scope.theme_id,
            scope.objective_id,
            scope.pattern_id,
            target_size,
            now,
            now,
        ),
    )


def load_selection_queue(connection: Any, queue_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM selection_queues WHERE queue_id = ?",
        (queue_id,),
    ).fetchone()
    return None if row is None else row_to_dict(row)


def queue_available_count(connection: Any, queue_id: str) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM selection_queue_items
        WHERE queue_id = ? AND claim_status = 'available'
        """,
        (queue_id,),
    ).fetchone()
    return int(row["count"])


def update_queue_availability(connection: Any, queue_id: str) -> int:
    available_count = queue_available_count(connection, queue_id)
    connection.execute(
        """
        UPDATE selection_queues
        SET queue_status = ?, available_count = ?, refill_after_at = NULL, updated_at = ?
        WHERE queue_id = ?
        """,
        (queue_status(available_count), available_count, utc_now(), queue_id),
    )
    return available_count


def next_queue_position(connection: Any, queue_id: str) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(MAX(position), -1) + 1 AS next_position
        FROM selection_queue_items
        WHERE queue_id = ?
        """,
        (queue_id,),
    ).fetchone()
    return int(row["next_position"])


def load_entitled_consumer_ids(connection: Any) -> list[str]:
    rows = connection.execute(
        """
        SELECT DISTINCT c.consumer_id
        FROM consumers c
        JOIN entitlements e ON e.consumer_id = c.consumer_id
        WHERE c.status = 'active'
          AND e.feature = 'quiz_delivery'
          AND e.status = 'active'
          AND (e.valid_until IS NULL OR e.valid_until >= ?)
        ORDER BY c.consumer_id
        """,
        (utc_now(),),
    ).fetchall()
    return [str(row["consumer_id"]) for row in rows]


def refill_summary(
    target_size: int,
    consumer_ids: list[str],
    channel_ids: tuple[str, ...],
    results: list[QueueRefillResult],
) -> dict[str, object]:
    return {
        "target_size": target_size,
        "consumer_count": len(set(consumer_ids)),
        "channel_count": len(channel_ids),
        "queue_count": len(results),
        "ready_queue_count": sum(1 for result in results if result.queue_status == "ready"),
        "warming_queue_count": sum(1 for result in results if result.queue_status == "warming"),
        "disabled_queue_count": sum(1 for result in results if result.queue_status == "disabled"),
        "added_item_count": sum(result.added_count for result in results),
        "available_item_count": sum(result.available_count for result in results),
        "queues": [result.to_dict() for result in results],
    }


def disabled_queue_result(
    queue_id: str,
    scope: QueueScope,
    target_size: int,
    existing: dict[str, Any],
) -> QueueRefillResult:
    return QueueRefillResult(
        queue_id,
        scope,
        target_size,
        0,
        int(existing["available_count"]),
        "disabled",
        "queue_disabled",
    )


def candidate_row(row: Any) -> dict[str, Any]:
    values = row_to_dict(row)
    return {
        **values,
        "delivery_count": int(values["delivery_count"] or 0),
        "last_delivered_at": str(values["last_delivered_at"] or ""),
        "cell_delivery_count": 0,
    }


def queue_item_score_snapshot(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "pool_id": candidate["pool_id"],
        "pool_rank_position": int(candidate["rank_position"]),
        "selection_score": dict(candidate.get("_selection_score", {})),
    }


def queue_status(available_count: int) -> str:
    if available_count > 0:
        return "ready"
    return "warming"


def values_or_blank(values: str | tuple[str, ...] | None) -> tuple[str, ...]:
    if values is None or values == "":
        return ("",)
    if isinstance(values, str):
        return (values,)
    return tuple(values) or ("",)


def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
