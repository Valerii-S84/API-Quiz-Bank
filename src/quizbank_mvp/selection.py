"""Selection orchestration for the MVP runtime."""

from __future__ import annotations

from dataclasses import replace
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
    ConsumerProfile,
    SelectionFilters,
    SelectionRequest,
    SelectionTargetMix,
)
from .selection_quota import (
    load_quota_usage,
    quota_exceeded_problem,
    quota_feature,
    reserve_quota,
    upsert_quota_usage,
)
from .selection_scope import effective_scope_replacement
from .selection_scope_enforcement import (
    enforce_consumer_scope,
    enforce_entitlement_scope,
    enforce_scope_list,
    load_active_consumer,
    load_active_entitlement,
)
from .time_ids import new_id


def select_next_item(db_path: Path | None, request: SelectionRequest) -> dict[str, Any]:
    selection_request_id = new_id("selreq")
    with connect(db_path) as connection:
        consumer = load_active_consumer(connection, request.consumer_id)
        entitlement = load_active_entitlement(connection, request)
        request = replace(request, **effective_scope_replacement(request, consumer, entitlement))
        enforce_consumer_scope(consumer, request)
        enforce_entitlement_scope(entitlement, request)
        quota_usage = reserve_quota(connection, consumer, request)
        item, eligible_count = find_eligible_item(connection, request)
        if item is None:
            candidate_total = candidate_count(connection, request)
            blocked_counts = blocked_reason_counts(connection, request)
            decision = no_candidate_decision(
                selection_request_id,
                request,
                candidate_total,
                blocked_counts,
            )
            connection.rollback()
            persist_no_candidate_decision(db_path, decision)
            raise no_eligible_problem(request, decision.to_context())
        blocked_counts = success_blocked_reason_counts(request)
        delivery = create_delivery(connection, request, item, entitlement, quota_usage)
        decision = success_decision(
            selection_request_id,
            request,
            delivery,
            item,
            eligible_count,
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


__all__ = [
    "ConsumerProfile",
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
    "repeat_window_cutoff",
    "reserve_quota",
    "select_next_item",
    "upsert_quota_usage",
]
