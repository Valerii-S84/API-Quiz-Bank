"""FastAPI application for the API Quiz Bank MVP."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .admin_api import register_admin_routes
from .auth import authenticate_consumer, authenticate_consumer_connection
from .database_connection import connect, configured_database_url, configured_db_path
from .database_runtime import database_is_ready, visual_database_is_ready
from .problems import QuizBankProblem
from .rate_limit import FixedWindowRateLimiter, delivery_rate_limit_key
from .selection import SelectionFilters, SelectionRequest, get_delivery, select_next_item
from .selection_queue_selector import (
    select_next_item_from_queue,
    select_next_item_from_queue_existing_connection,
)
from .taxonomy import level_catalog, topic_catalog
from .trusted_delivery import (
    is_answer_enabled_consumer,
    lookup_trusted_quiz_item,
    record_delivery_outcome,
)


CefrLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
ThemeId = Literal[
    "T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09",
    "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18",
]
SCOPED_QUOTA_CONSUMERS = {"website_quiz_teaser"}
MAX_QUOTA_SCOPE_KEY_LENGTH = 128
SelectionRouteMode = Literal["queue_first", "controlled_pilot_fallback"]
QUEUE_FIRST_ENABLED_VALUES = {"1", "true", "yes", "queue", "queue_first", "queue-first"}
CONTROLLED_PILOT_FALLBACK_VALUES = {
    "controlled_pilot_fallback",
    "controlled-pilot-fallback",
    "pilot_fallback",
    "pilot-fallback",
    "queue_with_live_fallback",
    "queue-with-live-fallback",
}
LIVE_FALLBACK_CONSUMERS_ENV = "QUIZBANK_SELECTION_LIVE_FALLBACK_CONSUMERS"
SELECTION_QUEUE_NOT_READY_CODE = "SELECTION_QUEUE_NOT_READY"
DeliveryOutcomeStatus = Literal["sent", "failed", "cancelled"]
logger = logging.getLogger(__name__)
ObjectiveId = Literal[
    "O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08",
    "O09", "O10", "O11", "O12", "O13", "O14", "O15", "O16",
]
PatternId = Literal[
    "P01", "P02", "P03", "P04", "P05", "P06",
    "P07", "P08", "P09", "P10", "P11", "P12",
]
TopicLanguageCode = Literal["de"]


class NextQuizRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consumer_id: str = Field(min_length=1)
    cefr_level: CefrLevel | None = None
    theme_ids: list[ThemeId] = Field(default_factory=list)
    objective_ids: list[ObjectiveId] = Field(default_factory=list)
    pattern_ids: list[PatternId] = Field(default_factory=list)
    language_code: str | None = Field(default=None, min_length=1, max_length=8)
    content_bank_id: str | None = Field(default=None, min_length=1, max_length=128)
    bank_version_id: str | None = Field(default=None, min_length=1, max_length=160)


class DeliveryOutcomeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DeliveryOutcomeStatus
    reason: str | None = Field(default=None, max_length=500)


def create_app(db_path: Path | None = None) -> FastAPI:
    database_path = db_path if db_path is not None or configured_database_url() else configured_db_path()
    app = FastAPI(
        title="API Quiz Bank",
        version=__version__,
        summary="MVP runtime for governed quiz delivery.",
    )
    rate_limiter = FixedWindowRateLimiter.from_environment()
    register_error_handlers(app)
    register_operations_routes(app, database_path)
    register_delivery_routes(app, database_path, rate_limiter)
    register_trusted_delivery_routes(app, database_path)
    register_admin_routes(app, database_path)
    return app


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(QuizBankProblem)
    async def quizbank_problem_handler(_, error: QuizBankProblem) -> JSONResponse:
        return problem_response(error)


def register_operations_routes(app: FastAPI, database_path: Path) -> None:
    @app.get("/health", tags=["operations"])
    @app.get("/v1/health", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "api-quiz-bank", "version": __version__}

    @app.get("/ready", tags=["operations"], response_model=None)
    @app.get("/v1/ready", tags=["operations"], response_model=None)
    def ready():
        checks = readiness_checks(database_path)
        if all(check["status"] == "ok" for check in checks):
            return {"status": "ok", "checks": checks}
        return problem_response(
            QuizBankProblem(
                503,
                "DATABASE_NOT_READY",
                "Database is not ready",
                "Initialize the SQLite MVP database before serving delivery requests.",
                "https://api.quizbank.example/problems/database-not-ready",
            )
        )

    @app.get("/v1/levels", tags=["taxonomy"])
    def levels() -> dict[str, object]:
        return {"data": level_catalog()}

    @app.get("/v1/topics", tags=["taxonomy"])
    def topics(language_code: TopicLanguageCode = Query(default="de")) -> dict[str, object]:
        return {"data": topic_catalog(language_code)}


def readiness_checks(database_path: Path | None) -> list[dict[str, str]]:
    return [
        {"name": "database", "status": "ok" if database_is_ready(database_path) else "failed"},
        {"name": "visual_database", "status": "ok" if visual_database_is_ready(database_path) else "failed"},
    ]


def register_delivery_routes(
    app: FastAPI,
    database_path: Path,
    rate_limiter: FixedWindowRateLimiter,
) -> None:
    @app.post("/v1/quiz-items/next", tags=["quiz-delivery"])
    def next_quiz_item(
        request: Request,
        payload: NextQuizRequest,
        x_consumer_id: Annotated[str | None, Header()] = None,
        x_quizbank_api_key: Annotated[str | None, Header(alias="X-QuizBank-API-Key")] = None,
        x_quizbank_quota_key: Annotated[str | None, Header(alias="X-QuizBank-Quota-Key")] = None,
    ) -> dict[str, object]:
        started_at = perf_counter()
        timings: dict[str, float] = {}
        rate_limiter.check_delivery(
            delivery_rate_limit_key(
                request.client.host if request.client else None,
                x_consumer_id or payload.consumer_id,
                x_quizbank_api_key,
            )
        )
        timings["rate_limit_ms"] = elapsed_ms(started_at)
        response = select_next_route_result(
            database_path,
            payload,
            x_consumer_id,
            x_quizbank_api_key,
            x_quizbank_quota_key,
            timings,
        )
        timings["total_ms"] = elapsed_ms(started_at)
        log_next_route_timing(payload.consumer_id, timings)
        return response

    @app.get("/v1/deliveries/{delivery_id}", tags=["quiz-delivery"])
    def delivery(
        delivery_id: str,
        x_consumer_id: Annotated[str | None, Header()] = None,
        x_quizbank_api_key: Annotated[str | None, Header(alias="X-QuizBank-API-Key")] = None,
    ) -> dict[str, object]:
        authenticated = authenticate_consumer(
            database_path,
            x_consumer_id,
            x_quizbank_api_key,
        )
        return get_delivery(database_path, delivery_id, authenticated.consumer_id)


def select_next_route_result(
    database_path: Path | None,
    payload: NextQuizRequest,
    x_consumer_id: str | None,
    x_quizbank_api_key: str | None,
    x_quizbank_quota_key: str | None,
    timings: dict[str, float],
) -> dict[str, object]:
    with connect(database_path) as connection:
        auth_started_at = perf_counter()
        authenticated = authenticate_consumer_connection(
            connection,
            x_consumer_id,
            x_quizbank_api_key,
        )
        timings["auth_ms"] = elapsed_ms(auth_started_at)
        authorize_started_at = perf_counter()
        authorize_consumer(authenticated.consumer_id, payload.consumer_id)
        timings["authorize_ms"] = elapsed_ms(authorize_started_at)
        request_started_at = perf_counter()
        selection_request = next_selection_request(payload, x_quizbank_quota_key)
        timings["request_build_ms"] = elapsed_ms(request_started_at)
        selection_started_at = perf_counter()
        result = select_next_for_route_connection(connection, database_path, selection_request)
        timings["selection_ms"] = elapsed_ms(selection_started_at)
        response_started_at = perf_counter()
        response = next_quiz_response(payload.consumer_id, result)
        timings["response_ms"] = elapsed_ms(response_started_at)
        return response


def register_trusted_delivery_routes(app: FastAPI, database_path: Path) -> None:
    @app.get("/v1/quiz-items/{item_id}", tags=["quiz-delivery"])
    def trusted_quiz_item(
        item_id: str,
        x_consumer_id: Annotated[str | None, Header()] = None,
        x_quizbank_api_key: Annotated[str | None, Header(alias="X-QuizBank-API-Key")] = None,
    ) -> dict[str, object]:
        authenticated = authenticate_consumer(
            database_path,
            x_consumer_id,
            x_quizbank_api_key,
        )
        result = lookup_trusted_quiz_item(database_path, item_id, authenticated.consumer_id)
        return trusted_quiz_item_response(authenticated.consumer_id, result)

    @app.post("/v1/deliveries/{delivery_id}/outcome", tags=["quiz-delivery"])
    def delivery_outcome(
        delivery_id: str,
        payload: DeliveryOutcomeRequest,
        x_consumer_id: Annotated[str | None, Header()] = None,
        x_quizbank_api_key: Annotated[str | None, Header(alias="X-QuizBank-API-Key")] = None,
    ) -> dict[str, object]:
        authenticated = authenticate_consumer(
            database_path,
            x_consumer_id,
            x_quizbank_api_key,
        )
        return record_delivery_outcome(
            database_path,
            delivery_id,
            authenticated.consumer_id,
            payload.status,
            payload.reason,
        )


def next_quiz_response(consumer_id: str, result: dict[str, object]) -> dict[str, object]:
    delivery = result["delivery"]
    if not isinstance(delivery, dict):
        raise TypeError("delivery result must be a dictionary")
    quiz_item = result["quiz_item"]
    if not isinstance(quiz_item, dict):
        raise TypeError("quiz item result must be a dictionary")
    answer_feedback = result.get("answer_feedback")
    quiz_item = quiz_item_for_consumer(consumer_id, quiz_item, answer_feedback)
    selection_decision = result.get("selection_decision", {})
    if not isinstance(selection_decision, dict):
        raise TypeError("selection decision result must be a dictionary")
    return {
        "delivery_id": delivery["delivery_id"],
        "consumer_id": consumer_id,
        "language_code": delivery["language_code"],
        "content_bank_id": delivery["content_bank_id"],
        "bank_version_id": delivery["bank_version_id"],
        "quiz_item": quiz_item,
        "delivery": delivery,
        "interaction": {
            "mode": "hidden_before_attempt",
            "answer_key_included": answer_feedback_is_included(consumer_id, answer_feedback),
        },
        "selection": {
            "entitlement_checked": True,
            "quota_checked": True,
            "repeat_policy_applied": True,
            "decision": public_selection_decision(selection_decision),
        },
    }


def next_selection_request(
    payload: NextQuizRequest,
    raw_quota_key: str | None,
) -> SelectionRequest:
    return SelectionRequest(
        consumer_id=payload.consumer_id,
        quota_scope_key=quota_scope_key_for_consumer(payload.consumer_id, raw_quota_key),
        filters=SelectionFilters(
            cefr_level=payload.cefr_level,
            theme_ids=tuple(payload.theme_ids),
            objective_ids=tuple(payload.objective_ids),
            pattern_ids=tuple(payload.pattern_ids),
        ),
        language_code=payload.language_code,
        content_bank_id=payload.content_bank_id,
        bank_version_id=payload.bank_version_id,
        delivery_mode="api",
    )


def select_next_for_route(db_path: Path | None, request: SelectionRequest) -> dict[str, object]:
    mode = selection_route_mode()
    if mode == "queue_first":
        return select_next_item_from_queue(db_path, request)
    return select_next_with_controlled_pilot_fallback(db_path, request)


def select_next_for_route_connection(
    connection,
    db_path: Path | None,
    request: SelectionRequest,
) -> dict[str, object]:
    mode = selection_route_mode()
    if mode == "queue_first":
        return select_next_item_from_queue_existing_connection(connection, request)
    return select_next_with_controlled_pilot_fallback_connection(connection, db_path, request)


def selection_route_mode() -> SelectionRouteMode:
    raw_value = os.environ.get("QUIZBANK_NEXT_SELECTION_MODE", "")
    normalized = raw_value.strip().lower()
    if not normalized:
        return "queue_first"
    if normalized in QUEUE_FIRST_ENABLED_VALUES:
        return "queue_first"
    if normalized in CONTROLLED_PILOT_FALLBACK_VALUES:
        return "controlled_pilot_fallback"
    raise invalid_selection_mode_problem()


def queue_first_selection_enabled() -> bool:
    return selection_route_mode() == "queue_first"


def select_next_with_controlled_pilot_fallback(
    db_path: Path | None,
    request: SelectionRequest,
) -> dict[str, object]:
    try:
        return select_next_item_from_queue(db_path, request)
    except QuizBankProblem as error:
        if live_fallback_is_allowed(request, error):
            logger.warning(
                "queue_first path=fallback consumer_id=%s reason=%s",
                request.consumer_id,
                error.reason_code,
            )
            return select_next_item(db_path, request)
        raise


def select_next_with_controlled_pilot_fallback_connection(
    connection,
    db_path: Path | None,
    request: SelectionRequest,
) -> dict[str, object]:
    try:
        return select_next_item_from_queue_existing_connection(connection, request)
    except QuizBankProblem as error:
        if live_fallback_is_allowed(request, error):
            connection.rollback()
            logger.warning(
                "queue_first path=fallback consumer_id=%s reason=%s",
                request.consumer_id,
                error.reason_code,
            )
            return select_next_item(db_path, request)
        raise


def live_fallback_is_allowed(request: SelectionRequest, error: QuizBankProblem) -> bool:
    if error.reason_code != SELECTION_QUEUE_NOT_READY_CODE:
        return False
    return request.consumer_id in live_fallback_pilot_consumers()


def live_fallback_pilot_consumers() -> set[str]:
    raw_value = os.environ.get(LIVE_FALLBACK_CONSUMERS_ENV, "")
    return {
        consumer_id.strip()
        for consumer_id in raw_value.split(",")
        if consumer_id.strip()
    }


def invalid_selection_mode_problem() -> QuizBankProblem:
    return QuizBankProblem(
        503,
        "SELECTION_MODE_INVALID",
        "Selection mode is invalid",
        "Configure QUIZBANK_NEXT_SELECTION_MODE to queue_first or controlled_pilot_fallback.",
        "https://api.quizbank.example/problems/selection-mode-invalid",
    )


def trusted_quiz_item_response(consumer_id: str, result: dict[str, object]) -> dict[str, object]:
    quiz_item = result["quiz_item"]
    if not isinstance(quiz_item, dict):
        raise TypeError("quiz item result must be a dictionary")
    answer_feedback = result.get("answer_feedback")
    return {
        "consumer_id": consumer_id,
        "quiz_item": quiz_item_for_consumer(consumer_id, quiz_item, answer_feedback),
        "interaction": {
            "mode": "trusted_item_lookup",
            "answer_key_included": answer_feedback_is_included(consumer_id, answer_feedback),
        },
        "access": {
            "entitlement_checked": True,
            "deliverable_status_checked": True,
        },
    }


def quiz_item_for_consumer(
    consumer_id: str,
    quiz_item: dict[str, object],
    answer_feedback: object,
) -> dict[str, object]:
    if not answer_feedback_is_included(consumer_id, answer_feedback):
        return quiz_item
    return {**quiz_item, "feedback": answer_feedback}


def answer_feedback_is_included(consumer_id: str, answer_feedback: object) -> bool:
    return is_answer_enabled_consumer(consumer_id) and isinstance(answer_feedback, dict)


def public_selection_decision(decision: dict[str, object]) -> dict[str, object]:
    return {
        "selection_request_id": decision.get("selection_request_id"),
        "language_code": decision.get("language_code"),
        "content_bank_id": decision.get("content_bank_id"),
        "bank_version_id": decision.get("bank_version_id"),
        "candidate_count": decision.get("candidate_count"),
        "eligible_count": decision.get("eligible_count"),
        "selected_reason": decision.get("selected_reason"),
        "selected_score": decision.get("selected_score", {}),
        "blocked_reason_counts": decision.get("blocked_reason_counts", {}),
        "fallback_reason_code": decision.get("fallback_reason_code"),
    }


def authorize_consumer(authenticated_consumer_id: str, requested_consumer_id: str) -> None:
    if authenticated_consumer_id != requested_consumer_id:
        raise QuizBankProblem(
            403,
            "AUTH_CONSUMER_MISMATCH",
            "Consumer access denied",
            "The authenticated consumer cannot access another consumer's data.",
            "https://api.quizbank.example/problems/consumer-access-denied",
        )


def quota_scope_key_for_consumer(consumer_id: str, raw_quota_key: str | None) -> str | None:
    if consumer_id not in SCOPED_QUOTA_CONSUMERS:
        return None
    if raw_quota_key is None or not raw_quota_key.strip():
        raise QuizBankProblem(
            400,
            "QUOTA_SCOPE_REQUIRED",
            "Quota scope required",
            "This consumer requires a per-session, per-IP or per-user quota scope key.",
            "https://api.quizbank.example/problems/quota-scope-required",
        )
    quota_key = raw_quota_key.strip()
    if len(quota_key) > MAX_QUOTA_SCOPE_KEY_LENGTH or has_control_character(quota_key):
        raise QuizBankProblem(
            400,
            "QUOTA_SCOPE_INVALID",
            "Quota scope invalid",
            "Quota scope key must be printable and at most 128 characters.",
            "https://api.quizbank.example/problems/quota-scope-invalid",
        )
    return quota_key


def has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def elapsed_ms(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000.0


def log_next_route_timing(consumer_id: str, timings: dict[str, float]) -> None:
    logging.getLogger("uvicorn.error").info(
        "next_route_timing consumer_id=%s rate_limit_ms=%.3f auth_ms=%.3f "
        "authorize_ms=%.3f request_build_ms=%.3f selection_ms=%.3f "
        "response_ms=%.3f total_ms=%.3f",
        consumer_id,
        timings["rate_limit_ms"],
        timings["auth_ms"],
        timings["authorize_ms"],
        timings["request_build_ms"],
        timings["selection_ms"],
        timings["response_ms"],
        timings["total_ms"],
    )


def problem_response(error: QuizBankProblem) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content=error.to_problem_details(),
        media_type="application/problem+json",
    )


app = create_app()
