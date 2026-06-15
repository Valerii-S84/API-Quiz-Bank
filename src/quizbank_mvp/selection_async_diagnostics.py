"""Outbox-backed selection diagnostics outside the request hot path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database_connection import connect, decode_json_field
from .selection_decision_log import SelectionDecisionLog, stable_json
from .selection_diagnostics import blocked_reason_counts, candidate_count
from .selection_models import (
    ConsumerProfile,
    ContentScope,
    SelectionFilters,
    SelectionRequest,
    SelectionTargetMix,
)
from .selection_policy import (
    ChannelCyclePolicy,
    RepeatPolicy,
    SelectionPolicy,
    TargetDistributionPolicy,
)
from .time_ids import new_id, utc_now


DEFAULT_WORKER_ID = "selection-diagnostics-worker"


@dataclass(frozen=True)
class QueuedDiagnosticEvent:
    outbox_id: str
    event_id: str
    selection_request_id: str | None
    event_type: str
    payload: dict[str, Any]


def minimal_no_candidate_blocked_counts(request: SelectionRequest) -> dict[str, int]:
    if not request.excluded_item_ids:
        return {}
    return {"explicit_exclusion": len(request.excluded_item_ids)}


def enqueue_no_candidate_diagnostics(
    connection: Any,
    selection_request_id: str,
    request: SelectionRequest,
    decision: SelectionDecisionLog,
) -> None:
    event_id = new_id("seldiag")
    now = utc_now()
    payload = {
        "diagnostic_status": "pending",
        "request": request_context(request),
        "decision": decision.to_context(),
    }
    connection.execute(
        """
        INSERT INTO selection_diagnostic_events (
            event_id, selection_request_id, consumer_id, channel_id,
            language_code, content_bank_id, bank_version_id, event_type,
            reason_code, payload_json, occurred_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            selection_request_id,
            request.consumer_id,
            request.consumer_profile.delivery_channel,
            request.language_code,
            required_scope_value(request.content_bank_id, "content_bank_id"),
            required_scope_value(request.bank_version_id, "bank_version_id"),
            "no_candidate",
            decision.fallback_reason_code or "",
            stable_json(payload),
            now,
            now,
        ),
    )
    connection.execute(
        """
        INSERT INTO selection_diagnostic_outbox (
            outbox_id, event_id, status, created_at, updated_at
        ) VALUES (?, ?, 'pending', ?, ?)
        """,
        (new_id("seldiagout"), event_id, now, now),
    )


def process_pending_selection_diagnostics(
    db_path: Path | None,
    limit: int = 50,
    worker_id: str = DEFAULT_WORKER_ID,
) -> dict[str, int]:
    if limit <= 0:
        return {"processed": 0, "published": 0, "failed": 0}
    summary = {"processed": 0, "published": 0, "failed": 0}
    with connect(db_path) as connection:
        for event in pending_diagnostic_events(connection, limit):
            mark_outbox_processing(connection, event.outbox_id, worker_id)
            summary["processed"] += 1
            try:
                process_diagnostic_event(connection, event)
            except Exception as error:  # keep one bad diagnostic from blocking the batch
                mark_outbox_failed(connection, event.outbox_id, error)
                summary["failed"] += 1
            else:
                mark_outbox_published(connection, event.outbox_id)
                summary["published"] += 1
    return summary


def pending_diagnostic_events(connection: Any, limit: int) -> list[QueuedDiagnosticEvent]:
    rows = connection.execute(
        """
        SELECT outbox.outbox_id, events.event_id, events.selection_request_id,
               events.event_type, events.payload_json
        FROM selection_diagnostic_outbox outbox
        JOIN selection_diagnostic_events events ON events.event_id = outbox.event_id
        WHERE outbox.status IN ('pending', 'failed')
          AND (outbox.next_attempt_at IS NULL OR outbox.next_attempt_at <= ?)
        ORDER BY outbox.created_at ASC, outbox.outbox_id ASC
        LIMIT ?
        """,
        (utc_now(), limit),
    ).fetchall()
    return [queued_event_from_row(row) for row in rows]


def process_diagnostic_event(connection: Any, event: QueuedDiagnosticEvent) -> None:
    if event.event_type != "no_candidate":
        return
    request = request_from_payload(event.payload)
    diagnostics = {
        "candidate_count": candidate_count(connection, request),
        "blocked_reason_counts": blocked_reason_counts(connection, request),
        "diagnosed_at": utc_now(),
    }
    payload = {
        **event.payload,
        "diagnostic_status": "published",
        "diagnostics": diagnostics,
    }
    connection.execute(
        """
        UPDATE selection_diagnostic_events
        SET payload_json = ?
        WHERE event_id = ?
        """,
        (stable_json(payload), event.event_id),
    )
    if event.selection_request_id is not None:
        update_no_candidate_decision(connection, event.selection_request_id, diagnostics)


def update_no_candidate_decision(
    connection: Any,
    selection_request_id: str,
    diagnostics: dict[str, Any],
) -> None:
    connection.execute(
        """
        UPDATE selection_decisions
        SET candidate_count = ?,
            blocked_reason_counts_json = ?
        WHERE selection_request_id = ?
          AND delivery_id IS NULL
        """,
        (
            int(diagnostics["candidate_count"]),
            stable_json(diagnostics["blocked_reason_counts"]),
            selection_request_id,
        ),
    )


def mark_outbox_processing(connection: Any, outbox_id: str, worker_id: str) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE selection_diagnostic_outbox
        SET status = 'processing',
            attempt_count = attempt_count + 1,
            locked_at = ?,
            locked_by = ?,
            updated_at = ?
        WHERE outbox_id = ?
        """,
        (now, worker_id, now, outbox_id),
    )


def mark_outbox_published(connection: Any, outbox_id: str) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE selection_diagnostic_outbox
        SET status = 'published',
            locked_at = NULL,
            locked_by = NULL,
            updated_at = ?
        WHERE outbox_id = ?
        """,
        (now, outbox_id),
    )


def mark_outbox_failed(connection: Any, outbox_id: str, error: Exception) -> None:
    now = utc_now()
    connection.execute(
        """
        UPDATE selection_diagnostic_outbox
        SET status = 'failed',
            locked_at = NULL,
            locked_by = NULL,
            last_error = ?,
            updated_at = ?
        WHERE outbox_id = ?
        """,
        (diagnostic_error_message(error), now, outbox_id),
    )


def request_context(request: SelectionRequest) -> dict[str, Any]:
    return {
        "consumer_id": request.consumer_id,
        "delivery_mode": request.delivery_mode,
        "deterministic": request.deterministic,
        "selection_strategy": request.selection_strategy,
        "filters": request.filters.to_context(),
        "content_scope": request.content_scope.to_context(),
        "consumer_profile": request.consumer_profile.to_context(),
        "target_mix": request.target_mix.to_context(),
        "policy": request.policy.to_context(),
    }


def request_from_payload(payload: dict[str, Any]) -> SelectionRequest:
    context = dict(payload["request"])
    return SelectionRequest(
        consumer_id=str(context["consumer_id"]),
        filters=selection_filters_from_context(context["filters"]),
        delivery_mode=str(context["delivery_mode"]),
        deterministic=bool(context["deterministic"]),
        selection_strategy=str(context["selection_strategy"]),
        policy=selection_policy_from_context(context["policy"]),
        consumer_profile=consumer_profile_from_context(context["consumer_profile"]),
        target_mix=target_mix_from_context(context["target_mix"]),
        content_scope=content_scope_from_context(context["content_scope"]),
    )


def selection_filters_from_context(context: dict[str, Any]) -> SelectionFilters:
    return SelectionFilters(
        cefr_level=optional_string(context.get("cefr_level")),
        theme_ids=string_tuple(context.get("theme_ids")),
        objective_ids=string_tuple(context.get("objective_ids")),
        pattern_ids=string_tuple(context.get("pattern_ids")),
        excluded_item_ids=string_tuple(context.get("excluded_item_ids")),
    )


def content_scope_from_context(context: dict[str, Any]) -> ContentScope:
    return ContentScope(
        language_code=str(context["language_code"]),
        content_bank_id=optional_string(context.get("content_bank_id")),
        bank_version_id=optional_string(context.get("bank_version_id")),
    )


def consumer_profile_from_context(context: dict[str, Any]) -> ConsumerProfile:
    return ConsumerProfile(
        consumer_id=str(context["consumer_id"]),
        delivery_channel=str(context["delivery_channel"]),
    )


def target_mix_from_context(context: dict[str, Any]) -> SelectionTargetMix:
    return SelectionTargetMix(
        level_weights=float_map(context.get("level_weights")),
        theme_weights=float_map(context.get("theme_weights")),
        objective_weights=float_map(context.get("objective_weights")),
        pattern_weights=float_map(context.get("pattern_weights")),
    )


def selection_policy_from_context(context: dict[str, Any]) -> SelectionPolicy:
    return SelectionPolicy(
        hard_filters=string_tuple(context.get("hard_filters")),
        repeat_policy=repeat_policy_from_context(context.get("repeat_policy", {})),
        channel_cycle_policy=channel_cycle_policy_from_context(
            context.get("channel_cycle_policy", {})
        ),
        target_distribution_policy=target_distribution_policy_from_context(
            context.get("target_distribution_policy", {})
        ),
        no_candidate_reason_code=str(
            context.get("no_candidate_reason_code", "SELECTION_NO_ELIGIBLE_ITEM")
        ),
    )


def repeat_policy_from_context(context: dict[str, Any]) -> RepeatPolicy:
    return RepeatPolicy(
        enabled=bool(context.get("enabled", True)),
        scope=str(context.get("scope", "consumer")),
        repeat_window_days=optional_int(context.get("repeat_window_days")),
        blocked_delivery_statuses=string_tuple(context.get("blocked_delivery_statuses")),
        fallback_reason_code=str(
            context.get("fallback_reason_code", "SELECTION_REPEAT_POLICY_EXHAUSTED")
        ),
    )


def channel_cycle_policy_from_context(context: dict[str, Any]) -> ChannelCyclePolicy:
    return ChannelCyclePolicy(
        enabled=bool(context.get("enabled", True)),
        scope=str(context.get("scope", "consumer_channel")),
        exhaustion_rule=str(context.get("exhaustion_rule", "deny_when_cycle_exhausted")),
        fallback_reason_code=str(
            context.get("fallback_reason_code", "SELECTION_CHANNEL_CYCLE_EXHAUSTED")
        ),
    )


def target_distribution_policy_from_context(
    context: dict[str, Any],
) -> TargetDistributionPolicy:
    return TargetDistributionPolicy(
        enabled=bool(context.get("enabled", True)),
        scope=str(context.get("scope", "consumer_channel")),
        fallback_reason_code=str(
            context.get("fallback_reason_code", "SELECTION_TARGET_DISTRIBUTION_UNAVAILABLE")
        ),
    )


def queued_event_from_row(row: Any) -> QueuedDiagnosticEvent:
    return QueuedDiagnosticEvent(
        outbox_id=str(row["outbox_id"]),
        event_id=str(row["event_id"]),
        selection_request_id=optional_string(row["selection_request_id"]),
        event_type=str(row["event_type"]),
        payload=decoded_payload(row["payload_json"]),
    )


def decoded_payload(value: Any) -> dict[str, Any]:
    payload = decode_json_field(value)
    if not isinstance(payload, dict):
        raise ValueError("selection diagnostic payload must be an object")
    return payload


def required_scope_value(value: str | None, field_name: str) -> str:
    if value is None:
        raise ValueError(f"resolved selection request is missing {field_name}")
    return value


def optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(str(item) for item in value)


def float_map(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    return {str(key): float(score) for key, score in value.items()}


def diagnostic_error_message(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"[:500]
