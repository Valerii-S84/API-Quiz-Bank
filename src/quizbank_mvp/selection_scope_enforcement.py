"""Consumer and entitlement scope enforcement for selection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .database_connection import decode_json_field, row_to_dict
from .problems import QuizBankProblem
from .time_ids import utc_now

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


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


def load_active_entitlement(connection, request: "SelectionRequest") -> dict[str, Any]:
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


def enforce_consumer_scope(consumer: dict[str, Any], request: "SelectionRequest") -> None:
    enforce_scope_list(
        scope_list(consumer, "allowed_language_codes_json"),
        [request.language_code] if request.language_code else [],
        "CONSUMER_LANGUAGE_NOT_ALLOWED",
    )
    enforce_scope_list(
        scope_list(consumer, "allowed_content_bank_ids_json"),
        [request.content_bank_id] if request.content_bank_id else [],
        "CONSUMER_CONTENT_BANK_NOT_ALLOWED",
    )
    enforce_scope_list(
        scope_list(consumer, "allowed_bank_version_ids_json"),
        [request.bank_version_id] if request.bank_version_id else [],
        "CONSUMER_BANK_VERSION_NOT_ALLOWED",
    )
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


def enforce_entitlement_scope(entitlement: dict[str, Any], request: "SelectionRequest") -> None:
    enforce_scope_list(
        scope_list(entitlement, "allowed_language_codes_json"),
        [request.language_code] if request.language_code else [],
        "ENTITLEMENT_LANGUAGE_NOT_ALLOWED",
    )
    enforce_scope_list(
        scope_list(entitlement, "allowed_content_bank_ids_json"),
        [request.content_bank_id] if request.content_bank_id else [],
        "ENTITLEMENT_CONTENT_BANK_NOT_ALLOWED",
    )
    enforce_scope_list(
        scope_list(entitlement, "allowed_bank_version_ids_json"),
        [request.bank_version_id] if request.bank_version_id else [],
        "ENTITLEMENT_BANK_VERSION_NOT_ALLOWED",
    )
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


def scope_list(row: dict[str, Any], key: str) -> list[str]:
    return decode_json_field(row.get(key) or "[]")


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
