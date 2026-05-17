"""Selection, entitlement and delivery rules for the MVP runtime."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .database import (
    DELIVERABLE_STATUSES,
    connect,
    decode_json_field,
    new_id,
    row_to_dict,
    today_usage_date,
    utc_now,
)
from .projections import build_learner_quiz_projection
from .selection_decision_log import (
    insert_selection_decision,
    no_candidate_decision,
    success_decision,
)
from .selection_diagnostics import blocked_reason_counts, candidate_count
from .selection_policy import SelectionPolicy
from .selection_scope import effective_scope_replacement
from .weighted_selection import select_ranked_candidate


class QuizBankProblem(Exception):
    def __init__(
        self,
        status: int,
        reason_code: str,
        title: str,
        detail: str,
        problem_type: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.reason_code = reason_code
        self.title = title
        self.detail = detail
        self.problem_type = problem_type
        self.extra = extra or {}

    def to_problem_details(self) -> dict[str, Any]:
        return {
            "type": self.problem_type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "reason_code": self.reason_code,
            **self.extra,
        }


@dataclass(frozen=True)
class SelectionFilters:
    cefr_level: str | None = None
    theme_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    excluded_item_ids: tuple[str, ...] = ()

    def to_context(self) -> dict[str, object]:
        return {
            "cefr_level": self.cefr_level,
            "theme_ids": list(self.theme_ids),
            "objective_ids": list(self.objective_ids),
            "pattern_ids": list(self.pattern_ids),
            "excluded_item_ids": list(self.excluded_item_ids),
        }


@dataclass(frozen=True)
class ConsumerProfile:
    consumer_id: str
    delivery_channel: str

    def to_context(self) -> dict[str, str]:
        return {
            "consumer_id": self.consumer_id,
            "delivery_channel": self.delivery_channel,
        }


@dataclass(frozen=True)
class SelectionTargetMix:
    level_weights: dict[str, float] = field(default_factory=dict)
    theme_weights: dict[str, float] = field(default_factory=dict)
    objective_weights: dict[str, float] = field(default_factory=dict)
    pattern_weights: dict[str, float] = field(default_factory=dict)

    def to_context(self) -> dict[str, dict[str, float]]:
        return {
            "level_weights": dict(self.level_weights),
            "theme_weights": dict(self.theme_weights),
            "objective_weights": dict(self.objective_weights),
            "pattern_weights": dict(self.pattern_weights),
        }


@dataclass(frozen=True)
class SelectionRequest:
    consumer_id: str
    filters: SelectionFilters | None = None
    delivery_mode: str = "api"
    deterministic: bool = False
    selection_strategy: str = "weighted_policy"
    policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    consumer_profile: ConsumerProfile | None = None
    target_mix: SelectionTargetMix = field(default_factory=SelectionTargetMix)
    cefr_level: str | None = None
    theme_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    excluded_item_ids: tuple[str, ...] = ()
    quota_scope_key: str | None = None

    def __post_init__(self) -> None:
        filters = self.normalized_filters(self.filters or self.legacy_filters())
        self.validate_filter_contract(filters)
        object.__setattr__(self, "filters", filters)
        object.__setattr__(self, "consumer_profile", self.normalized_consumer_profile())
        object.__setattr__(self, "cefr_level", filters.cefr_level)
        object.__setattr__(self, "theme_ids", filters.theme_ids)
        object.__setattr__(self, "objective_ids", filters.objective_ids)
        object.__setattr__(self, "pattern_ids", filters.pattern_ids)
        object.__setattr__(self, "excluded_item_ids", filters.excluded_item_ids)

    def legacy_filters(self) -> SelectionFilters:
        return SelectionFilters(
            cefr_level=self.cefr_level,
            theme_ids=self.theme_ids,
            objective_ids=self.objective_ids,
            pattern_ids=self.pattern_ids,
            excluded_item_ids=self.excluded_item_ids,
        )

    def normalized_filters(self, filters: SelectionFilters) -> SelectionFilters:
        return SelectionFilters(
            cefr_level=filters.cefr_level,
            theme_ids=tuple(filters.theme_ids),
            objective_ids=tuple(filters.objective_ids),
            pattern_ids=tuple(filters.pattern_ids),
            excluded_item_ids=tuple(filters.excluded_item_ids),
        )

    def validate_filter_contract(self, filters: SelectionFilters) -> None:
        if self.filters is None:
            return
        if self.legacy_filters() != SelectionFilters():
            raise ValueError("SelectionRequest must use filters or legacy filter fields, not both")

    def normalized_consumer_profile(self) -> ConsumerProfile:
        if self.consumer_profile is not None:
            return self.consumer_profile
        return ConsumerProfile(
            consumer_id=self.consumer_id,
            delivery_channel=self.delivery_mode,
        )


def select_next_item(db_path: Path | None, request: SelectionRequest) -> dict[str, Any]:
    selection_request_id = new_id("selreq")
    with connect(db_path) as connection:
        consumer = load_active_consumer(connection, request.consumer_id)
        entitlement = load_active_entitlement(connection, request)
        request = replace(request, **effective_scope_replacement(request, consumer, entitlement))
        enforce_consumer_scope(consumer, request)
        enforce_entitlement_scope(entitlement, request)
        quota_usage = reserve_quota(connection, consumer, request)
        candidate_total = candidate_count(connection, request)
        item, eligible_count = find_eligible_item(connection, request)
        blocked_counts = blocked_reason_counts(connection, request)
        if item is None:
            decision = no_candidate_decision(
                selection_request_id,
                request,
                candidate_total,
                blocked_counts,
            )
            connection.rollback()
            persist_no_candidate_decision(db_path, decision)
            raise no_eligible_problem(request, decision.to_context())
        delivery = create_delivery(connection, request, item, entitlement, quota_usage)
        decision = success_decision(
            selection_request_id,
            request,
            delivery,
            item,
            candidate_total,
            eligible_count,
            blocked_counts,
        )
        insert_selection_decision(connection, decision)
    return {
        "delivery": delivery,
        "quiz_item": build_learner_quiz_projection(item),
        "answer_feedback": answer_feedback(item),
        "selection_decision": decision.to_context(),
    }


def persist_no_candidate_decision(db_path: Path | None, decision) -> None:
    with connect(db_path) as connection:
        insert_selection_decision(connection, decision)


def get_delivery(db_path: Path | None, delivery_id: str, consumer_id: str) -> dict[str, Any]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM deliveries
            WHERE delivery_id = ? AND consumer_id = ?
            """,
            (delivery_id, consumer_id),
        ).fetchone()
    if row is None:
        raise QuizBankProblem(
            404,
            "DELIVERY_NOT_FOUND",
            "Delivery not found",
            "No delivery is visible for this consumer.",
            "https://api.quizbank.example/problems/delivery-not-found",
        )
    return delivery_projection(row_to_dict(row))


def load_active_consumer(connection, consumer_id: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT * FROM consumers WHERE consumer_id = ? AND status = 'active'",
        (consumer_id,),
    ).fetchone()
    if row is None:
        raise QuizBankProblem(
            403,
            "CONSUMER_NOT_ACTIVE",
            "Consumer is not active",
            "The consumer is missing or inactive.",
            "https://api.quizbank.example/problems/consumer-not-active",
        )
    return row_to_dict(row)


def load_active_entitlement(connection, request: SelectionRequest) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT * FROM entitlements
        WHERE consumer_id = ?
          AND feature = 'quiz_delivery'
          AND status = 'active'
          AND (valid_until IS NULL OR valid_until >= ?)
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (request.consumer_id, utc_now()),
    ).fetchone()
    if row is None:
        raise QuizBankProblem(
            403,
            "ENTITLEMENT_MISSING_FEATURE",
            "Entitlement missing",
            "This consumer is not entitled to quiz delivery.",
            "https://api.quizbank.example/problems/entitlement-missing",
        )
    return row_to_dict(row)


def enforce_consumer_scope(consumer: dict[str, Any], request: SelectionRequest) -> None:
    enforce_scope_list(
        decode_json_field(consumer["allowed_cefr_levels_json"]),
        [request.cefr_level] if request.cefr_level else [],
        "CONSUMER_LEVEL_NOT_ALLOWED",
    )
    enforce_scope_list(
        decode_json_field(consumer["allowed_theme_ids_json"]),
        list(request.theme_ids),
        "CONSUMER_THEME_NOT_ALLOWED",
    )


def enforce_entitlement_scope(entitlement: dict[str, Any], request: SelectionRequest) -> None:
    enforce_scope_list(
        decode_json_field(entitlement["allowed_cefr_levels_json"]),
        [request.cefr_level] if request.cefr_level else [],
        "ENTITLEMENT_LEVEL_NOT_ALLOWED",
    )
    enforce_scope_list(
        decode_json_field(entitlement["allowed_theme_ids_json"]),
        list(request.theme_ids),
        "ENTITLEMENT_THEME_NOT_ALLOWED",
    )


def enforce_scope_list(allowed: list[str], requested: list[str], reason_code: str) -> None:
    if not requested or not allowed:
        return
    denied = [value for value in requested if value not in allowed]
    if denied:
        raise QuizBankProblem(
            403,
            reason_code,
            "Request is outside allowed scope",
            "The requested quiz scope is not allowed for this consumer.",
            "https://api.quizbank.example/problems/entitlement-scope-denied",
            {"denied_values": denied},
        )


def reserve_quota(
    connection,
    consumer: dict[str, Any],
    request: SelectionRequest,
) -> dict[str, Any]:
    usage_date = today_usage_date()
    feature = quota_feature(request)
    row = load_quota_usage(connection, consumer["consumer_id"], usage_date, feature)
    used_count = 0 if row is None else int(row["used_count"])
    quota_limit = int(consumer["daily_quota_limit"])
    if used_count >= quota_limit:
        raise quota_exceeded_problem(used_count, quota_limit)
    quota_usage_id = row["quota_usage_id"] if row else new_id("quota")
    upsert_quota_usage(
        connection,
        consumer,
        usage_date,
        feature,
        quota_usage_id,
        used_count + 1,
    )
    return {"quota_usage_id": quota_usage_id}


def quota_feature(request: SelectionRequest) -> str:
    if not request.quota_scope_key:
        return "quiz_delivery"
    digest = hashlib.sha256(request.quota_scope_key.encode("utf-8")).hexdigest()[:24]
    return f"quiz_delivery:scope:{digest}"


def load_quota_usage(connection, consumer_id: str, usage_date: str, feature: str):
    row = connection.execute(
        """
        SELECT * FROM quota_usage
        WHERE consumer_id = ? AND feature = ? AND usage_date = ?
        """,
        (consumer_id, feature, usage_date),
    ).fetchone()
    return row


def quota_exceeded_problem(used_count: int, quota_limit: int) -> QuizBankProblem:
    return QuizBankProblem(
        429,
        "QUOTA_EXCEEDED",
        "Quota exceeded",
        "This consumer has reached the configured delivery quota.",
        "https://api.quizbank.example/problems/quota-exceeded",
        {"quota": {"used": used_count, "limit": quota_limit, "window": "day"}},
    )


def upsert_quota_usage(
    connection,
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    quota_usage_id: str,
    next_used_count: int,
) -> None:
    connection.execute(
        """
        INSERT INTO quota_usage (
            quota_usage_id, consumer_id, feature, usage_date, used_count,
            quota_limit, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(consumer_id, feature, usage_date) DO UPDATE SET
            used_count = excluded.used_count,
            quota_limit = excluded.quota_limit,
            updated_at = excluded.updated_at
        """,
        (
            quota_usage_id,
            consumer["consumer_id"],
            feature,
            usage_date,
            next_used_count,
            int(consumer["daily_quota_limit"]),
            utc_now(),
        ),
    )


def find_eligible_item(
    connection,
    request: SelectionRequest,
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
    request: SelectionRequest,
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


def create_delivery(
    connection,
    request: SelectionRequest,
    item: dict[str, Any],
    entitlement: dict[str, Any],
    quota_usage: dict[str, Any],
) -> dict[str, Any]:
    delivery_id = new_id("deliv")
    connection.execute(
        """
        INSERT INTO deliveries (
            delivery_id, consumer_id, quiz_item_id, item_status, delivery_status,
            source_id, source_type, provenance_note, selection_reason_summary,
            selected_at, entitlement_id, quota_usage_id
        ) VALUES (?, ?, ?, ?, 'created', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            delivery_id,
            request.consumer_id,
            item["item_id"],
            item["status"],
            item["source_id"],
            item["resolved_source_type"],
            item["resolved_provenance_note"],
            request.policy.selection_reason_summary(),
            utc_now(),
            entitlement["entitlement_id"],
            quota_usage["quota_usage_id"],
        ),
    )
    row = connection.execute(
        "SELECT * FROM deliveries WHERE delivery_id = ?",
        (delivery_id,),
    ).fetchone()
    return delivery_projection(row_to_dict(row))


def delivery_projection(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "delivery_id": delivery["delivery_id"],
        "consumer_id": delivery["consumer_id"],
        "quiz_item_id": delivery["quiz_item_id"],
        "item_status": delivery["item_status"],
        "status": delivery["delivery_status"],
        "selected_at": delivery["selected_at"],
        "reason": delivery["selection_reason_summary"],
    }


def answer_feedback(item: dict[str, Any]) -> dict[str, str]:
    option_index = int(item["answer_key"]) + 1
    return {
        "correctAnswerId": f"option_{option_index}",
        "explanation": str(item["explanation"]).strip(),
    }


def no_eligible_problem(
    request: SelectionRequest,
    decision_context: dict[str, object] | None = None,
) -> QuizBankProblem:
    selection_context: dict[str, object] = {
        "consumer_id": request.consumer_id,
        "delivery_mode": request.delivery_mode,
        "deterministic": request.deterministic,
        "selection_strategy": request.selection_strategy,
        "policy": request.policy.to_context(),
        "fallback_reason_codes": request.policy.fallback_reason_codes(),
        "consumer_profile": request.consumer_profile.to_context(),
        "target_mix": request.target_mix.to_context(),
        "filters": request.filters.to_context(),
        "cefr_level": request.cefr_level,
        "theme_ids": list(request.theme_ids),
        "objective_ids": list(request.objective_ids),
        "pattern_ids": list(request.pattern_ids),
        "filters_applied": list(request.policy.hard_filters),
    }
    if decision_context is not None:
        selection_context["decision"] = decision_context
    return QuizBankProblem(
        404,
        "SELECTION_NO_ELIGIBLE_ITEM",
        "No eligible quiz item",
        "No item satisfies the selection constraints.",
        "https://api.quizbank.example/problems/no-eligible-item",
        {"selection_context": selection_context},
    )
