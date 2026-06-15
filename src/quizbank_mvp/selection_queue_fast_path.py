"""PostgreSQL queue-first selection hot path."""

from __future__ import annotations

from dataclasses import dataclass, replace
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
from .selection_queue_models import selection_queue_id
from .selection_quota import reserve_quota
from .selection_scope import effective_scope_replacement
from .selection_scope_enforcement import enforce_consumer_scope, enforce_entitlement_scope
from .time_ids import new_id, utc_now


class PostgreSQLQueueFastPathMiss(RuntimeError):
    """Signals that the regular selector should produce the precise error."""


@dataclass(frozen=True)
class PostgreSQLQueueSelectionContext:
    consumer: dict[str, Any]
    entitlement: dict[str, Any]
    request: SelectionRequest


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
    context = prepare_postgresql_queue_selection_context(connection, request)
    claimed = claim_postgresql_queue_item(connection, context.request)
    quota_usage = reserve_quota(connection, context.consumer, context.request)
    delivery = new_delivery(context.request, claimed.item, context.entitlement, quota_usage)
    finalize_postgresql_queue_delivery(connection, context.request, claimed, delivery)
    decision = success_decision(
        selection_request_id,
        context.request,
        delivery,
        claimed.item,
        1,
        1,
        {},
    )
    insert_selection_decision(connection, decision)
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
    return PostgreSQLQueueSelectionContext(consumer, entitlement, prepared_request)


def postgresql_context_sql() -> str:
    return """
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
               scope.language_code, scope.content_bank_id, scope.bank_version_id
        FROM active_consumer c
        JOIN active_entitlement e ON TRUE
        JOIN resolved_scope scope ON TRUE
    """


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
    )


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
        raise queue_not_ready_problem(request, queue_ids)
    return claimed_item_from_row(row_to_dict(row))


def postgresql_claim_item_sql(
    queue_ids: tuple[str, ...],
    excluded_item_ids: tuple[str, ...],
) -> str:
    queue_placeholders = ", ".join("?" for _ in queue_ids)
    status_placeholders = ", ".join("?" for _ in DELIVERABLE_STATUSES)
    excluded_clause = postgresql_excluded_item_clause(excluded_item_ids)
    return f"""
        WITH candidate AS (
            SELECT sqi.queue_item_id
            FROM selection_queue_items sqi
            JOIN selection_queues sq ON sq.queue_id = sqi.queue_id
            JOIN quiz_items qi ON qi.item_id = sqi.item_id
            WHERE sqi.queue_id IN ({queue_placeholders})
              AND sq.queue_status IN ('ready', 'draining')
              AND sqi.claim_status = 'available'
              AND qi.status IN ({status_placeholders})
              AND qi.language_code = sq.language_code
              AND qi.content_bank_id = sq.content_bank_id
              AND qi.bank_version_id = sq.bank_version_id
              AND (sq.cefr_level = '' OR qi.sublevel = sq.cefr_level)
              AND (sq.theme_id = '' OR qi.theme_id = sq.theme_id)
              AND (sq.objective_id = '' OR qi.objective_id = sq.objective_id)
              AND (sq.pattern_id = '' OR qi.pattern_id = sq.pattern_id)
              {excluded_clause}
            ORDER BY sqi.position ASC, sqi.queue_item_id ASC
            LIMIT 1
        ),
        updated AS (
            UPDATE selection_queue_items sqi
            SET claim_status = 'claimed',
                claim_token = ?,
                claimed_at = ?,
                claim_expires_at = NULL,
                updated_at = ?
            FROM candidate
            WHERE sqi.queue_item_id = candidate.queue_item_id
            RETURNING sqi.queue_item_id, sqi.queue_id, sqi.item_id, sqi.score_snapshot_json
        )
        SELECT updated.queue_item_id, updated.queue_id, updated.score_snapshot_json,
               qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note,
               iq.theme_group, iq.image_quality_recommended,
               iq.image_quality_source, iq.image_quality_policy_share,
               iq.image_quality_override
        FROM updated
        JOIN quiz_items qi ON qi.item_id = updated.item_id
        JOIN sources s ON s.source_id = qi.source_id
        LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
        WHERE qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
    """


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
        *DELIVERABLE_STATUSES,
        *request.excluded_item_ids,
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
    connection.execute(
        postgresql_finalize_delivery_sql(),
        postgresql_finalize_delivery_parameters(request, claimed.claim, delivery),
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
        UPDATE selection_queues
        SET available_count = CASE
                WHEN available_count > 0 THEN available_count - 1
                ELSE 0
            END,
            queue_status = CASE
                WHEN available_count > 1 THEN queue_status
                ELSE 'warming'
            END,
            refill_after_at = CASE
                WHEN available_count > 1 THEN refill_after_at
                ELSE ?
            END,
            updated_at = ?
        WHERE queue_id = (SELECT queue_id FROM delivered_queue_item)
          AND EXISTS (SELECT 1 FROM inserted_delivery)
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
        now,
        now,
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
