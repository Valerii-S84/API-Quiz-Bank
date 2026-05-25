"""Problem detail exception types for API-facing runtime failures."""

from __future__ import annotations

from typing import Any


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
