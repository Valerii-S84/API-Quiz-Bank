"""Selection orchestration for the MVP runtime."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .database_connection import connect
from .problems import QuizBankProblem
from .projections import build_learner_quiz_projection
from .selection_decision_log import (
    insert_selection_decision,
    no_candidate_decision,
    success_decision,
)
from .selection_delivery import (
    answer_feedback,
    create_delivery,
    delivery_projection,
    get_delivery,
)
from .selection_diagnostics import (
    blocked_reason_counts,
    candidate_count,
    success_blocked_reason_counts,
)
from .selection_eligibility import (
    append_filter,
    append_in_filter,
    append_not_in_filter,
    append_repeat_policy_filter,
    find_eligible_item,
    repeat_window_cutoff,
)
from .selection_errors import no_eligible_problem
from .selection_models import (
    ContentScope,
    ConsumerProfile,
    SelectionFilters,
    SelectionRequest,
    SelectionTargetMix,
)
from .selection_quota import (
    load_quota_usage,
    quota_exceeded_problem,
    quota_feature,
    raise_if_quota_exhausted,
    reserve_quota,
    upsert_quota_usage,
)
from .selection_scope import effective_scope_replacement, resolve_content_scope_request
from .selection_scope_enforcement import (
    enforce_consumer_scope,
    enforce_entitlement_scope,
    enforce_scope_list,
    load_active_consumer,
    load_active_entitlement,
)
from .time_ids import new_id


@dataclass(frozen=True)
class SelectionWritePlan:
    consumer: dict[str, Any]
    entitlement: dict[str, Any]
    request: SelectionRequest
    item: dict[str, Any]
    eligible_count: int
    blocked_counts: dict[str, int]


def select_next_item(db_path: Path | None, request: SelectionRequest) -> dict[str, Any]:
    selection_request_id = new_id("selreq")
    plan = prepare_selection_write_plan(db_path, request, selection_request_id)
    delivery, decision = commit_selection_write(db_path, plan, selection_request_id)
    return {
        "delivery": delivery,
        "quiz_item": build_learner_quiz_projection(plan.item),
        "answer_feedback": answer_feedback(plan.item),
        "selection_decision": decision.to_context(),
    }


def prepare_selection_write_plan(
    db_path: Path | None,
    request: SelectionRequest,
    selection_request_id: str,
) -> SelectionWritePlan:
    with connect(db_path) as connection:
        consumer = load_active_consumer(connection, request.consumer_id)
        entitlement = load_active_entitlement(connection, request)
        request = replace(request, **effective_scope_replacement(request, consumer, entitlement))
        request = resolve_content_scope_request(connection, request, consumer)
        enforce_consumer_scope(consumer, request)
        enforce_entitlement_scope(entitlement, request)
        item, eligible_count = find_eligible_item(connection, request)
        if item is None:
            raise_if_quota_exhausted(connection, consumer, request)
            candidate_total = candidate_count(connection, request)
            blocked_counts = blocked_reason_counts(connection, request)
            decision = no_candidate_decision(
                selection_request_id,
                request,
                candidate_total,
                blocked_counts,
            )
        else:
            blocked_counts = success_blocked_reason_counts(request)
            return SelectionWritePlan(
                consumer,
                entitlement,
                request,
                item,
                eligible_count,
                blocked_counts,
            )
    persist_no_candidate_decision(db_path, decision)
    raise no_eligible_problem(request, decision.to_context())


def commit_selection_write(
    db_path: Path | None,
    plan: SelectionWritePlan,
    selection_request_id: str,
):
    with connect(db_path) as connection:
        quota_usage = reserve_quota(connection, plan.consumer, plan.request)
        delivery = create_delivery(
            connection,
            plan.request,
            plan.item,
            plan.entitlement,
            quota_usage,
        )
        decision = success_decision(
            selection_request_id,
            plan.request,
            delivery,
            plan.item,
            plan.eligible_count,
            plan.eligible_count,
            plan.blocked_counts,
        )
        insert_selection_decision(connection, decision)
    return delivery, decision


def persist_no_candidate_decision(db_path: Path | None, decision) -> None:
    with connect(db_path) as connection:
        insert_selection_decision(connection, decision)


__all__ = [
    "ConsumerProfile",
    "ContentScope",
    "QuizBankProblem",
    "SelectionFilters",
    "SelectionRequest",
    "SelectionTargetMix",
    "answer_feedback",
    "append_filter",
    "append_in_filter",
    "append_not_in_filter",
    "append_repeat_policy_filter",
    "create_delivery",
    "delivery_projection",
    "enforce_consumer_scope",
    "enforce_entitlement_scope",
    "enforce_scope_list",
    "find_eligible_item",
    "get_delivery",
    "load_active_consumer",
    "load_active_entitlement",
    "load_quota_usage",
    "no_eligible_problem",
    "persist_no_candidate_decision",
    "quota_exceeded_problem",
    "quota_feature",
    "raise_if_quota_exhausted",
    "repeat_window_cutoff",
    "reserve_quota",
    "select_next_item",
    "upsert_quota_usage",
]
