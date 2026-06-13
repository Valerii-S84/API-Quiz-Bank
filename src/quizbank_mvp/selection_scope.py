"""Scope-derived selection filters for consumer delivery."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .database_connection import decode_json_field
from .problems import QuizBankProblem
from .database_runtime import DEFAULT_LANGUAGE_CODE
from .selection_models import ContentScope


SCOPE_CONFLICT_VALUE = "__scope_conflict__"


def effective_scope_replacement(
    request: Any,
    consumer: dict[str, Any],
    entitlement: dict[str, Any],
) -> dict[str, Any]:
    return {
        "filters": effective_scope_filters(request.filters, consumer, entitlement),
        "cefr_level": None,
        "theme_ids": (),
        "objective_ids": (),
        "pattern_ids": (),
        "excluded_item_ids": (),
    }


def resolve_content_scope_request(connection, request: Any, consumer: dict[str, Any] | None = None):
    scope = resolve_content_scope(connection, request_scope_with_consumer_defaults(request, consumer))
    return replace(
        request,
        content_scope=scope,
        language_code=scope.language_code,
        content_bank_id=scope.content_bank_id,
        bank_version_id=scope.bank_version_id,
        cefr_level=None,
        theme_ids=(),
        objective_ids=(),
        pattern_ids=(),
        excluded_item_ids=(),
    )


def request_scope_with_consumer_defaults(
    request: Any,
    consumer: dict[str, Any] | None,
) -> ContentScope:
    requested_scope = request.content_scope
    if consumer is None:
        return requested_scope
    return ContentScope(
        language_code=effective_language_code(requested_scope, consumer),
        content_bank_id=requested_scope.content_bank_id
        or blank_to_none(consumer.get("default_content_bank_id")),
        bank_version_id=requested_scope.bank_version_id
        or blank_to_none(consumer.get("default_bank_version_id")),
    )


def effective_language_code(scope: ContentScope, consumer: dict[str, Any]) -> str:
    if scope.language_code != DEFAULT_LANGUAGE_CODE:
        return scope.language_code
    return str(consumer.get("default_language_code") or DEFAULT_LANGUAGE_CODE)


def blank_to_none(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def resolve_content_scope(connection, requested_scope: ContentScope) -> ContentScope:
    language_code = requested_scope.language_code
    ensure_language_is_active(connection, language_code)
    row = connection.execute(
        content_scope_sql(requested_scope),
        content_scope_parameters(requested_scope),
    ).fetchone()
    if row is None:
        raise content_scope_problem(
            404,
            "BANK_VERSION_NOT_AVAILABLE",
            "Bank version is not available",
            "No active content bank version is available for this content scope.",
        )
    return ContentScope(
        language_code=str(row["language_code"]),
        content_bank_id=str(row["content_bank_id"]),
        bank_version_id=str(row["bank_version_id"]),
    )


def ensure_language_is_active(connection, language_code: str) -> None:
    row = connection.execute(
        "SELECT code, is_active FROM languages WHERE code = ?",
        (language_code,),
    ).fetchone()
    if row is None:
        raise content_scope_problem(
            400,
            "LANGUAGE_UNSUPPORTED",
            "Language is unsupported",
            "The requested language is not supported by this runtime.",
        )
    if not bool(row["is_active"]):
        raise content_scope_problem(
            403,
            "LANGUAGE_NOT_ACTIVE",
            "Language is not active",
            "The requested language is not active for delivery.",
        )


def content_scope_sql(scope: ContentScope) -> str:
    clauses = [
        "cb.language_code = ?",
        "cb.status = 'active'",
        "cbv.status = 'active'",
    ]
    if scope.content_bank_id:
        clauses.append("cb.id = ?")
    if scope.bank_version_id:
        clauses.append("cbv.id = ?")
    where_clause = " AND ".join(clauses)
    return f"""
        SELECT cb.language_code, cb.id AS content_bank_id, cbv.id AS bank_version_id
        FROM content_banks cb
        JOIN content_bank_versions cbv ON cbv.content_bank_id = cb.id
        WHERE {where_clause}
        ORDER BY cb.created_at DESC, cbv.activated_at DESC, cbv.created_at DESC
        LIMIT 1
    """


def content_scope_parameters(scope: ContentScope) -> tuple[str, ...]:
    parameters = [scope.language_code]
    if scope.content_bank_id:
        parameters.append(scope.content_bank_id)
    if scope.bank_version_id:
        parameters.append(scope.bank_version_id)
    return tuple(parameters)


def content_scope_problem(status: int, reason_code: str, title: str, detail: str) -> QuizBankProblem:
    return QuizBankProblem(
        status,
        reason_code,
        title,
        detail,
        "https://api.quizbank.example/problems/content-scope",
    )


def effective_scope_filters(filters: Any, consumer: dict[str, Any], entitlement: dict[str, Any]):
    return type(filters)(
        cefr_level=effective_cefr_level(filters, consumer, entitlement),
        theme_ids=effective_theme_ids(filters, consumer, entitlement),
        objective_ids=filters.objective_ids,
        pattern_ids=filters.pattern_ids,
        excluded_item_ids=filters.excluded_item_ids,
    )


def effective_cefr_level(
    filters: Any,
    consumer: dict[str, Any],
    entitlement: dict[str, Any],
) -> str | None:
    if filters.cefr_level:
        return filters.cefr_level
    allowed_levels = bounded_scope_values(
        decode_json_field(consumer["allowed_cefr_levels_json"]),
        decode_json_field(entitlement["allowed_cefr_levels_json"]),
    )
    if allowed_levels is None:
        return None
    if len(allowed_levels) == 1:
        return allowed_levels[0]
    if not allowed_levels:
        return SCOPE_CONFLICT_VALUE
    return None


def effective_theme_ids(
    filters: Any,
    consumer: dict[str, Any],
    entitlement: dict[str, Any],
) -> tuple[str, ...]:
    if filters.theme_ids:
        return filters.theme_ids
    allowed_themes = bounded_scope_values(
        decode_json_field(consumer["allowed_theme_ids_json"]),
        decode_json_field(entitlement["allowed_theme_ids_json"]),
    )
    if allowed_themes is None:
        return ()
    return allowed_themes or (SCOPE_CONFLICT_VALUE,)


def bounded_scope_values(first: list[str], second: list[str]) -> tuple[str, ...] | None:
    if not first and not second:
        return None
    if not first:
        return tuple(second)
    if not second:
        return tuple(first)
    second_values = set(second)
    return tuple(value for value in first if value in second_values)
