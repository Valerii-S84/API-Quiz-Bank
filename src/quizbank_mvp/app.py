"""FastAPI application for the API Quiz Bank MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .auth import authenticate_consumer
from .database import configured_db_path, database_is_ready
from .selection import QuizBankProblem, SelectionFilters, SelectionRequest, get_delivery, select_next_item
from .taxonomy import level_catalog, topic_catalog


CefrLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
ThemeId = Literal[
    "T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09",
    "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18",
]
ObjectiveId = Literal[
    "O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08",
    "O09", "O10", "O11", "O12", "O13", "O14", "O15", "O16",
]
PatternId = Literal[
    "P01", "P02", "P03", "P04", "P05", "P06",
    "P07", "P08", "P09", "P10", "P11", "P12",
]


class NextQuizRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consumer_id: str = Field(min_length=1)
    cefr_level: CefrLevel | None = None
    theme_ids: list[ThemeId] = Field(default_factory=list)
    objective_ids: list[ObjectiveId] = Field(default_factory=list)
    pattern_ids: list[PatternId] = Field(default_factory=list)


def create_app(db_path: Path | None = None) -> FastAPI:
    database_path = db_path or configured_db_path()
    app = FastAPI(
        title="API Quiz Bank",
        version=__version__,
        summary="MVP runtime for governed quiz delivery.",
    )
    register_error_handlers(app)
    register_operations_routes(app, database_path)
    register_delivery_routes(app, database_path)
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
        if database_is_ready(database_path):
            return {"status": "ok", "checks": [{"name": "database", "status": "ok"}]}
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
    def topics() -> dict[str, object]:
        return {"data": topic_catalog()}


def register_delivery_routes(app: FastAPI, database_path: Path) -> None:
    @app.post("/v1/quiz-items/next", tags=["quiz-delivery"])
    def next_quiz_item(
        payload: NextQuizRequest,
        x_consumer_id: Annotated[str | None, Header()] = None,
        x_quizbank_api_key: Annotated[str | None, Header(alias="X-QuizBank-API-Key")] = None,
    ) -> dict[str, object]:
        authenticated = authenticate_consumer(
            database_path,
            x_consumer_id,
            x_quizbank_api_key,
        )
        authorize_consumer(authenticated.consumer_id, payload.consumer_id)
        result = select_next_item(
            database_path,
            SelectionRequest(
                consumer_id=payload.consumer_id,
                filters=SelectionFilters(
                    cefr_level=payload.cefr_level,
                    theme_ids=tuple(payload.theme_ids),
                    objective_ids=tuple(payload.objective_ids),
                    pattern_ids=tuple(payload.pattern_ids),
                ),
                delivery_mode="api",
            ),
        )
        return next_quiz_response(payload.consumer_id, result)

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


def next_quiz_response(consumer_id: str, result: dict[str, object]) -> dict[str, object]:
    delivery = result["delivery"]
    if not isinstance(delivery, dict):
        raise TypeError("delivery result must be a dictionary")
    return {
        "delivery_id": delivery["delivery_id"],
        "consumer_id": consumer_id,
        "quiz_item": result["quiz_item"],
        "delivery": delivery,
        "interaction": {
            "mode": "hidden_before_attempt",
            "answer_key_included": False,
        },
        "selection": {
            "entitlement_checked": True,
            "quota_checked": True,
            "repeat_policy_applied": True,
        },
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


def problem_response(error: QuizBankProblem) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content=error.to_problem_details(),
        media_type="application/problem+json",
    )


app = create_app()
