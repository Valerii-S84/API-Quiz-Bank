"""PostgreSQL queue-first selection hot path."""

from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from time import perf_counter
from typing import Any

from .database_connection import PostgreSQLConnection, decode_json_field, row_to_dict
from .database_runtime import DEFAULT_LANGUAGE_CODE
from .database_status import DELIVERABLE_STATUSES
from .problems import QuizBankProblem
from .projections import build_learner_quiz_projection
from .selection_decision_log import insert_selection_decision, success_decision
from .selection_delivery import answer_feedback, delivery_projection
from .selection_models import ContentScope, SelectionRequest
from .selection_queue_filler import queue_scopes_for_request
from .selection_queue_fast_path_sql import POSTGRESQL_CLAIM_ITEM_SQL_TEMPLATE
from .selection_queue_models import MAX_QUEUE_TARGET_SIZE, selection_queue_id
from .selection_quota import quota_exceeded_problem, quota_feature, reserve_quota
from .selection_scope import effective_scope_replacement
from .selection_scope_enforcement import enforce_consumer_scope, enforce_entitlement_scope
from .time_ids import new_id, today_usage_date, utc_now


logger = logging.getLogger(__name__)


class PostgreSQLQueueFastPathMiss(RuntimeError):
    """Signals that the regular selector should produce the precise error."""


@dataclass(frozen=True)
class PostgreSQLQueueSelectionContext:
    consumer: dict[str, Any]
    entitlement: dict[str, Any]
    request: SelectionRequest
    quota_used_count: int


@dataclass(frozen=True)
class PostgreSQLQueueClaim:
    queue_item_id: str
    queue_id: str
    item_id: str
    score_snapshot: dict[str, Any]


@dataclass(frozen=True)
class PostgreSQLQueueClaimedItem:
    claim: PostgreSQLQueueClaim
    item: dict[str, Any]


def can_use_postgresql_queue_fast_path(connection: Any) -> bool:
    return isinstance(connection, PostgreSQLConnection)


def select_next_item_from_postgresql_queue(
    connection: PostgreSQLConnection,
    request: SelectionRequest,
    selection_request_id: str,
) -> dict[str, Any]:
    started_at = perf_counter()
    timings: dict[str, float] = {}
    context_started_at = perf_counter()
    context = prepare_postgresql_queue_selection_context(connection, request)
    timings["context_ms"] = elapsed_ms(context_started_at)
    raise_if_context_quota_exhausted(context)
    claim_started_at = perf_counter()
    claimed = claim_postgresql_queue_item(connection, context.request)
    timings["queue_claim_ms"] = elapsed_ms(claim_started_at)
    quota_started_at = perf_counter()
    quota_usage = reserve_quota(connection, context.consumer, context.request)
    timings["quota_reserve_ms"] = elapsed_ms(quota_started_at)
    delivery = new_delivery(context.request, claimed.item, context.entitlement, quota_usage)
    finalize_started_at = perf_counter()
    finalize_postgresql_queue_delivery(connection, context.request, claimed, delivery)
    timings["delivery_finalize_link_ms"] = elapsed_ms(finalize_started_at)
    decision = success_decision(
        selection_request_id,
        context.request,
        delivery,
        claimed.item,
        1,
        1,
        {},
    )
    decision_started_at = perf_counter()
    insert_selection_decision(connection, decision)
    timings["decision_insert_ms"] = elapsed_ms(decision_started_at)
    timings["diagnostics_outbox_ms"] = 0.0
    timings["total_ms"] = elapsed_ms(started_at)
    log_postgresql_queue_timing(context.request, selection_request_id, delivery, timings)
    return {
        "delivery": delivery_projection(delivery),
        "quiz_item": build_learner_quiz_projection(claimed.item),
        "answer_feedback": answer_feedback(claimed.item),
        "selection_decision": decision.to_context(),
    }


def prepare_postgresql_queue_selection_context(
    connection: PostgreSQLConnection,
    request: SelectionRequest,
) -> PostgreSQLQueueSelectionContext:
    row = connection.execute(postgresql_context_sql(), postgresql_context_parameters(request)).fetchone()
    if row is None:
        raise PostgreSQLQueueFastPathMiss()
    values = row_to_dict(row)
    consumer = consumer_from_context_row(values)
    entitlement = entitlement_from_context_row(values)
    scope = ContentScope(
        language_code=str(values["language_code"]),
        content_bank_id=str(values["content_bank_id"]),
        bank_version_id=str(values["bank_version_id"]),
    )
    prepared_request = replace(
        request,
        **effective_scope_replacement(request, consumer, entitlement),
        content_scope=scope,
    )
    enforce_consumer_scope(consumer, prepared_request)
    enforce_entitlement_scope(entitlement, prepared_request)
    return PostgreSQLQueueSelectionContext(
        consumer,
        entitlement,
        prepared_request,
        int(values["quota_used_count"]),
    )


POSTGRESQL_CONTEXT_SQL = """
    WITH active_consumer AS (
        SELECT *
        FROM consumers
        WHERE consumer_id = ? AND status = 'active'
    ),
    active_entitlement AS (
        SELECT *
        FROM entitlements
        WHERE consumer_id = ?
          AND feature = 'quiz_delivery'
          AND status = 'active'
          AND (valid_until IS NULL OR valid_until >= ?)
        ORDER BY created_at DESC
        LIMIT 1
    ),
    requested_scope AS (
        SELECT CASE WHEN ? <> ? THEN ?
                    ELSE COALESCE(NULLIF(c.default_language_code, ''), ?)
               END AS language_code,
               COALESCE(NULLIF(?, ''), NULLIF(c.default_content_bank_id, ''))
                   AS content_bank_id,
               COALESCE(NULLIF(?, ''), NULLIF(c.default_bank_version_id, ''))
                   AS bank_version_id
        FROM active_consumer c
    ),
    resolved_scope AS (
        SELECT cb.language_code, cb.id AS content_bank_id, cbv.id AS bank_version_id
        FROM requested_scope requested
        JOIN languages lang ON lang.code = requested.language_code AND lang.is_active
        JOIN content_banks cb ON cb.language_code = requested.language_code
        JOIN content_bank_versions cbv ON cbv.content_bank_id = cb.id
        WHERE cb.status = 'active'
          AND cbv.status = 'active'
          AND (requested.content_bank_id IS NULL OR cb.id = requested.content_bank_id)
          AND (requested.bank_version_id IS NULL OR cbv.id = requested.bank_version_id)
        ORDER BY cb.created_at DESC, cbv.activated_at DESC, cbv.created_at DESC
        LIMIT 1
    )
    SELECT c.consumer_id, c.status AS consumer_status, c.daily_quota_limit,
           c.allowed_cefr_levels_json AS consumer_allowed_cefr_levels_json,
           c.allowed_theme_ids_json AS consumer_allowed_theme_ids_json,
           c.allowed_language_codes_json AS consumer_allowed_language_codes_json,
           c.allowed_content_bank_ids_json AS consumer_allowed_content_bank_ids_json,
           c.allowed_bank_version_ids_json AS consumer_allowed_bank_version_ids_json,
           c.default_language_code, c.default_content_bank_id, c.default_bank_version_id,
           e.entitlement_id,
           e.allowed_cefr_levels_json AS entitlement_allowed_cefr_levels_json,
           e.allowed_theme_ids_json AS entitlement_allowed_theme_ids_json,
           e.allowed_language_codes_json AS entitlement_allowed_language_codes_json,
           e.allowed_content_bank_ids_json AS entitlement_allowed_content_bank_ids_json,
           e.allowed_bank_version_ids_json AS entitlement_allowed_bank_version_ids_json,
           scope.language_code, scope.content_bank_id, scope.bank_version_id,
           COALESCE(quota.used_count, 0) AS quota_used_count
    FROM active_consumer c
    JOIN active_entitlement e ON TRUE
    JOIN resolved_scope scope ON TRUE
    LEFT JOIN quota_usage quota
      ON quota.consumer_id = c.consumer_id
     AND quota.feature = ?
     AND quota.usage_date = ?
     AND quota.language_code = scope.language_code
     AND quota.content_bank_id = scope.content_bank_id
     AND quota.bank_version_id = scope.bank_version_id
"""


def postgresql_context_sql() -> str:
    return POSTGRESQL_CONTEXT_SQL


def postgresql_context_parameters(request: SelectionRequest) -> tuple[Any, ...]:
    scope = request.content_scope
    return (
        request.consumer_id,
        request.consumer_id,
        utc_now(),
        scope.language_code,
        DEFAULT_LANGUAGE_CODE,
        scope.language_code,
        DEFAULT_LANGUAGE_CODE,
        scope.content_bank_id,
        scope.bank_version_id,
        quota_feature(request),
        today_usage_date(),
    )


def raise_if_context_quota_exhausted(context: PostgreSQLQueueSelectionContext) -> None:
    quota_limit = int(context.consumer["daily_quota_limit"])
    if quota_limit <= 0:
        raise quota_exceeded_problem(0, quota_limit)
    if context.quota_used_count >= quota_limit:
        raise quota_exceeded_problem(context.quota_used_count, quota_limit)


def consumer_from_context_row(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "consumer_id": values["consumer_id"],
        "status": values["consumer_status"],
        "daily_quota_limit": values["daily_quota_limit"],
        "allowed_cefr_levels_json": values["consumer_allowed_cefr_levels_json"],
        "allowed_theme_ids_json": values["consumer_allowed_theme_ids_json"],
        "allowed_language_codes_json": values["consumer_allowed_language_codes_json"],
        "allowed_content_bank_ids_json": values["consumer_allowed_content_bank_ids_json"],
        "allowed_bank_version_ids_json": values["consumer_allowed_bank_version_ids_json"],
        "default_language_code": values["default_language_code"],
        "default_content_bank_id": values["default_content_bank_id"],
        "default_bank_version_id": values["default_bank_version_id"],
    }


def entitlement_from_context_row(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "entitlement_id": values["entitlement_id"],
        "consumer_id": values["consumer_id"],
        "feature": "quiz_delivery",
        "status": "active",
        "allowed_cefr_levels_json": values["entitlement_allowed_cefr_levels_json"],
        "allowed_theme_ids_json": values["entitlement_allowed_theme_ids_json"],
        "allowed_language_codes_json": values["entitlement_allowed_language_codes_json"],
        "allowed_content_bank_ids_json": values["entitlement_allowed_content_bank_ids_json"],
        "allowed_bank_version_ids_json": values["entitlement_allowed_bank_version_ids_json"],
    }


def claim_postgresql_queue_item(
    connection: PostgreSQLConnection,
    request: SelectionRequest,
) -> PostgreSQLQueueClaimedItem:
    queue_ids = tuple(selection_queue_id(scope) for scope in queue_scopes_for_request(request))
    row = connection.execute(
        postgresql_claim_item_sql(queue_ids, request.excluded_item_ids),
        postgresql_claim_item_parameters(request, queue_ids),
    ).fetchone()
    if row is None:
        logger.warning(
            "queue_first path=503 consumer_id=%s queue_ids=%s reason=%s",
            request.consumer_id,
            ",".join(queue_ids),
            "SELECTION_QUEUE_NOT_READY",
        )
        raise queue_not_ready_problem(request, queue_ids)
    return claimed_item_from_row(row_to_dict(row))


def postgresql_claim_item_sql(
    queue_ids: tuple[str, ...],
    excluded_item_ids: tuple[str, ...],
) -> str:
    return POSTGRESQL_CLAIM_ITEM_SQL_TEMPLATE.format(
        queue_placeholders=", ".join("?" for _ in queue_ids),
        status_placeholders=", ".join("?" for _ in DELIVERABLE_STATUSES),
        excluded_clause=postgresql_excluded_item_clause(excluded_item_ids),
    )


def postgresql_excluded_item_clause(excluded_item_ids: tuple[str, ...]) -> str:
    if not excluded_item_ids:
        return ""
    excluded_placeholders = ", ".join("?" for _ in excluded_item_ids)
    return f"AND sqi.item_id NOT IN ({excluded_placeholders})"


def postgresql_claim_item_parameters(
    request: SelectionRequest,
    queue_ids: tuple[str, ...],
) -> tuple[Any, ...]:
    now = utc_now()
    return (
        *queue_ids,
        *request.excluded_item_ids,
        max(1, len(queue_ids) * MAX_QUEUE_TARGET_SIZE),
        *DELIVERABLE_STATUSES,
        new_id("selclaim"),
        now,
        now,
    )


def claimed_item_from_row(values: dict[str, Any]) -> PostgreSQLQueueClaimedItem:
    claim = PostgreSQLQueueClaim(
        str(values["queue_item_id"]),
        str(values["queue_id"]),
        str(values["item_id"]),
        decoded_score_snapshot(values["score_snapshot_json"]),
    )
    return PostgreSQLQueueClaimedItem(claim, item_with_queue_score(values, claim))


def decoded_score_snapshot(value: Any) -> dict[str, Any]:
    snapshot = decode_json_field(value)
    if isinstance(snapshot, dict):
        return snapshot
    return {}


def item_with_queue_score(
    item: dict[str, Any],
    claim: PostgreSQLQueueClaim,
) -> dict[str, Any]:
    score = claim.score_snapshot.get("selection_score", {})
    if not isinstance(score, dict):
        score = {}
    return {**item, "_selection_score": score}


def new_delivery(
    request: SelectionRequest,
    item: dict[str, Any],
    entitlement: dict[str, Any],
    quota_usage: dict[str, Any],
) -> dict[str, Any]:
    return {
        "delivery_id": new_id("deliv"),
        "consumer_id": request.consumer_id,
        "quiz_item_id": item["item_id"],
        "item_status": item["status"],
        "delivery_status": "created",
        "language_code": request.language_code,
        "content_bank_id": request.content_bank_id,
        "bank_version_id": request.bank_version_id,
        "source_id": item["source_id"],
        "source_type": item["resolved_source_type"],
        "provenance_note": item["resolved_provenance_note"],
        "selection_reason_summary": request.policy.selection_reason_summary(),
        "selected_at": utc_now(),
        "entitlement_id": entitlement["entitlement_id"],
        "quota_usage_id": quota_usage["quota_usage_id"],
    }


def finalize_postgresql_queue_delivery(
    connection: PostgreSQLConnection,
    request: SelectionRequest,
    claimed: PostgreSQLQueueClaimedItem,
    delivery: dict[str, Any],
) -> None:
    row = connection.execute(
        postgresql_finalize_delivery_sql(),
        postgresql_finalize_delivery_parameters(request, claimed.claim, delivery),
    ).fetchone()
    if row is None:
        logger.error(
            "queue_first path=503 consumer_id=%s queue_id=%s queue_item_id=%s "
            "delivery_id=%s reason=%s",
            request.consumer_id,
            claimed.claim.queue_id,
            claimed.claim.queue_item_id,
            delivery["delivery_id"],
            "SELECTION_QUEUE_DELIVERY_LINK_FAILED",
        )
        raise queue_delivery_link_failed_problem(request, claimed.claim, delivery)
    logger.info(
        "queue_first path=queue consumer_id=%s queue_id=%s queue_item_id=%s delivery_id=%s",
        request.consumer_id,
        claimed.claim.queue_id,
        claimed.claim.queue_item_id,
        delivery["delivery_id"],
    )


def postgresql_finalize_delivery_sql() -> str:
    return """
        WITH inserted_delivery AS (
            INSERT INTO deliveries (
                delivery_id, consumer_id, quiz_item_id, item_status, delivery_status,
                language_code, content_bank_id, bank_version_id, source_id, source_type,
                provenance_note, selection_reason_summary, selected_at, entitlement_id,
                quota_usage_id
            ) VALUES (?, ?, ?, ?, 'created', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING delivery_id, consumer_id, quiz_item_id, delivery_status,
                      language_code, content_bank_id, bank_version_id, selected_at
        ),
        upsert_state AS (
            INSERT INTO consumer_delivery_state (
                consumer_id, channel_id, language_code, content_bank_id,
                bank_version_id, quiz_item_id, delivery_count, last_delivery_id,
                last_delivery_status, last_delivered_at, updated_at
            )
            SELECT consumer_id, ?, language_code, content_bank_id, bank_version_id,
                   quiz_item_id, 1, delivery_id, delivery_status, selected_at, ?
            FROM inserted_delivery
            ON CONFLICT(
                consumer_id, channel_id, language_code, content_bank_id,
                bank_version_id, quiz_item_id
            ) DO UPDATE SET
                delivery_count = consumer_delivery_state.delivery_count + 1,
                last_delivery_id = excluded.last_delivery_id,
                last_delivery_status = excluded.last_delivery_status,
                last_delivered_at = excluded.last_delivered_at,
                updated_at = excluded.updated_at
            RETURNING quiz_item_id
        ),
        delivered_queue_item AS (
            UPDATE selection_queue_items
            SET claim_status = 'delivered',
                delivery_id = ?,
                updated_at = ?
            WHERE queue_item_id = ? AND claim_status = 'claimed'
            RETURNING queue_id
        )
        SELECT queue_id
        FROM delivered_queue_item
        WHERE EXISTS (SELECT 1 FROM inserted_delivery)
          AND EXISTS (SELECT 1 FROM upsert_state)
    """


def postgresql_finalize_delivery_parameters(
    request: SelectionRequest,
    claim: PostgreSQLQueueClaim,
    delivery: dict[str, Any],
) -> tuple[Any, ...]:
    now = utc_now()
    return (
        delivery["delivery_id"],
        delivery["consumer_id"],
        delivery["quiz_item_id"],
        delivery["item_status"],
        delivery["language_code"],
        delivery["content_bank_id"],
        delivery["bank_version_id"],
        delivery["source_id"],
        delivery["source_type"],
        delivery["provenance_note"],
        delivery["selection_reason_summary"],
        delivery["selected_at"],
        delivery["entitlement_id"],
        delivery["quota_usage_id"],
        request.consumer_profile.delivery_channel,
        now,
        delivery["delivery_id"],
        now,
        claim.queue_item_id,
    )


def elapsed_ms(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000.0


def log_postgresql_queue_timing(
    request: SelectionRequest,
    selection_request_id: str,
    delivery: dict[str, Any],
    timings: dict[str, float],
) -> None:
    logging.getLogger("uvicorn.error").info(
        "queue_first_timing consumer_id=%s selection_request_id=%s delivery_id=%s "
        "context_ms=%.3f queue_claim_ms=%.3f quota_reserve_ms=%.3f "
        "delivery_finalize_link_ms=%.3f decision_insert_ms=%.3f "
        "diagnostics_outbox_ms=%.3f total_ms=%.3f",
        request.consumer_id,
        selection_request_id,
        delivery["delivery_id"],
        timings["context_ms"],
        timings["queue_claim_ms"],
        timings["quota_reserve_ms"],
        timings["delivery_finalize_link_ms"],
        timings["decision_insert_ms"],
        timings["diagnostics_outbox_ms"],
        timings["total_ms"],
    )


def queue_not_ready_problem(
    request: SelectionRequest,
    queue_ids: tuple[str, ...],
) -> QuizBankProblem:
    return QuizBankProblem(
        503,
        "SELECTION_QUEUE_NOT_READY",
        "Selection queue is not ready",
        "No precomputed queue item is currently available for this request scope.",
        "https://api.quizbank.example/problems/selection-queue-not-ready",
        {
            "selection_context": {
                "consumer_id": request.consumer_id,
                "delivery_mode": request.delivery_mode,
                "consumer_profile": request.consumer_profile.to_context(),
                "filters": request.filter_context(),
                "content_scope": request.content_scope.to_context(),
                "queue_ids": list(queue_ids),
            }
        },
    )


def queue_delivery_link_failed_problem(
    request: SelectionRequest,
    claim: PostgreSQLQueueClaim,
    delivery: dict[str, Any],
) -> QuizBankProblem:
    return QuizBankProblem(
        503,
        "SELECTION_QUEUE_NOT_READY",
        "Selection queue is not ready",
        "A precomputed queue item could not be finalized for this request scope.",
        "https://api.quizbank.example/problems/selection-queue-not-ready",
        {
            "selection_context": {
                "consumer_id": request.consumer_id,
                "delivery_mode": request.delivery_mode,
                "consumer_profile": request.consumer_profile.to_context(),
                "filters": request.filter_context(),
                "content_scope": request.content_scope.to_context(),
                "queue_id": claim.queue_id,
                "queue_item_id": claim.queue_item_id,
                "delivery_id": delivery["delivery_id"],
            }
        },
    )
