"""Quota reservation for selection requests."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from .database_connection import row_to_dict
from .database_runtime import DEFAULT_BANK_VERSION_ID, DEFAULT_CONTENT_BANK_ID, DEFAULT_LANGUAGE_CODE
from .problems import QuizBankProblem
from .time_ids import new_id, today_usage_date, utc_now

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


def reserve_quota(
    connection,
    consumer: dict[str, Any],
    request: "SelectionRequest",
) -> dict[str, Any]:
    usage_date = today_usage_date()
    feature = quota_feature(request)
    quota_limit = int(consumer["daily_quota_limit"])
    if quota_limit <= 0:
        raise quota_exceeded_problem(0, quota_limit)
    reservation = upsert_quota_usage(
        connection,
        consumer,
        usage_date,
        feature,
        new_id("quota"),
        request,
    )
    if reservation is None:
        row = load_quota_usage(connection, consumer["consumer_id"], usage_date, feature, request)
        used_count = 0 if row is None else int(row["used_count"])
        raise quota_exceeded_problem(used_count, quota_limit)
    return {"quota_usage_id": reservation["quota_usage_id"]}


def raise_if_quota_exhausted(
    connection,
    consumer: dict[str, Any],
    request: "SelectionRequest",
) -> None:
    quota_limit = int(consumer["daily_quota_limit"])
    if quota_limit <= 0:
        raise quota_exceeded_problem(0, quota_limit)
    usage_date = today_usage_date()
    feature = quota_feature(request)
    row = load_quota_usage(connection, consumer["consumer_id"], usage_date, feature, request)
    used_count = 0 if row is None else int(row["used_count"])
    if used_count >= quota_limit:
        raise quota_exceeded_problem(used_count, quota_limit)


def quota_feature(request: "SelectionRequest") -> str:
    if not request.quota_scope_key:
        return "quiz_delivery"
    digest = hashlib.sha256(request.quota_scope_key.encode("utf-8")).hexdigest()[:24]
    return f"quiz_delivery:scope:{digest}"


def load_quota_usage(
    connection,
    consumer_id: str,
    usage_date: str,
    feature: str,
    request: "SelectionRequest | None" = None,
):
    language_code, content_bank_id, bank_version_id = quota_scope_values(request=request)
    row = connection.execute(
        """
        SELECT * FROM quota_usage
        WHERE consumer_id = ? AND feature = ? AND usage_date = ?
          AND language_code = ? AND content_bank_id = ? AND bank_version_id = ?
        """,
        (consumer_id, feature, usage_date, language_code, content_bank_id, bank_version_id),
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
    request: "SelectionRequest | None" = None,
) -> dict[str, Any] | None:
    language_code, content_bank_id, bank_version_id = quota_scope_values(consumer, request)
    row = connection.execute(
        """
        INSERT INTO quota_usage (
            quota_usage_id, consumer_id, feature, usage_date,
            language_code, content_bank_id, bank_version_id,
            used_count, quota_limit, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(
            consumer_id,
            feature,
            usage_date,
            language_code,
            content_bank_id,
            bank_version_id
        ) DO UPDATE SET
            used_count = quota_usage.used_count + 1,
            quota_limit = excluded.quota_limit,
            updated_at = excluded.updated_at
        WHERE quota_usage.used_count < excluded.quota_limit
        RETURNING quota_usage_id, used_count, quota_limit
        """,
        (
            quota_usage_id,
            consumer["consumer_id"],
            feature,
            usage_date,
            language_code,
            content_bank_id,
            bank_version_id,
            int(consumer["daily_quota_limit"]),
            utc_now(),
        ),
    ).fetchone()
    return None if row is None else row_to_dict(row)


def quota_scope_values(
    consumer: dict[str, Any] | None = None,
    request: "SelectionRequest | None" = None,
) -> tuple[str, str, str]:
    if request is not None:
        return (
            request.language_code or DEFAULT_LANGUAGE_CODE,
            request.content_bank_id or DEFAULT_CONTENT_BANK_ID,
            request.bank_version_id or DEFAULT_BANK_VERSION_ID,
        )
    if consumer is None:
        return DEFAULT_LANGUAGE_CODE, DEFAULT_CONTENT_BANK_ID, DEFAULT_BANK_VERSION_ID
    return (
        str(consumer.get("default_language_code") or DEFAULT_LANGUAGE_CODE),
        str(consumer.get("default_content_bank_id") or DEFAULT_CONTENT_BANK_ID),
        str(consumer.get("default_bank_version_id") or DEFAULT_BANK_VERSION_ID),
    )
