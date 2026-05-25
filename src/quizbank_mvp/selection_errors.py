"""Selection-specific problem builders."""

from __future__ import annotations

from .problems import QuizBankProblem
from .selection_models import SelectionRequest


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
