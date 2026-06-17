"""Quota reservation tokens for PostgreSQL queue-first delivery."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .database_connection import PostgreSQLConnection, row_to_dict
from .selection_quota import quota_exceeded_problem, quota_feature, quota_scope_values
from .time_ids import new_id, today_usage_date, utc_now

if TYPE_CHECKING:
    from .selection_models import SelectionRequest


logger = logging.getLogger(__name__)
USED_RESERVATION_STATUSES = ("claimed", "finalized")
INSERT_MISSING_QUOTA_TOKENS_SQL = """
    WITH token_numbers AS (
        SELECT generate_series(1, ?) AS reservation_index
    )
    INSERT INTO quota_reservations (
        quota_reservation_id, quota_usage_id, consumer_id, feature,
        usage_date, language_code, content_bank_id, bank_version_id,
        reservation_index, reservation_status, claim_token, claimed_at,
        finalized_at, created_at, updated_at
    )
    SELECT
        'qres:' || md5(? || ':' || token_numbers.reservation_index::text),
        ?, ?, ?, ?, ?, ?, ?,
        token_numbers.reservation_index,
        CASE
            WHEN token_numbers.reservation_index <= ? THEN 'finalized'
            ELSE 'available'
        END,
        NULL,
        CASE
            WHEN token_numbers.reservation_index <= ? THEN CAST(? AS TIMESTAMPTZ)
            ELSE CAST(NULL AS TIMESTAMPTZ)
        END,
        CASE
            WHEN token_numbers.reservation_index <= ? THEN CAST(? AS TIMESTAMPTZ)
            ELSE CAST(NULL AS TIMESTAMPTZ)
        END,
        ?,
        ?
    FROM token_numbers
    ON CONFLICT(
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id,
        reservation_index
    ) DO NOTHING
"""


def claim_postgresql_quota_reservation(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    request: "SelectionRequest",
) -> dict[str, Any]:
    quota_limit = int(consumer["daily_quota_limit"])
    if quota_limit <= 0:
        log_quota_exhausted(consumer, request, 0, quota_limit)
        raise quota_exceeded_problem(0, quota_limit)
    usage_date = today_usage_date()
    feature = quota_feature(request)
    scope = quota_scope_values(consumer, request)
    claim = claim_available_quota_token(connection, consumer, request, usage_date, feature, scope)
    if claim is not None:
        return claim
    ensure_quota_tokens(connection, consumer, request, usage_date, feature, scope, quota_limit)
    claim = claim_available_quota_token(connection, consumer, request, usage_date, feature, scope)
    if claim is not None:
        return claim
    used_count = count_used_quota_reservations(connection, consumer, usage_date, feature, scope)
    log_quota_exhausted(consumer, request, used_count, quota_limit)
    raise quota_exceeded_problem(used_count, quota_limit)


def claim_available_quota_token(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    request: "SelectionRequest",
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
) -> dict[str, Any] | None:
    now = utc_now()
    row = connection.execute(
        """
        WITH candidate AS (
            SELECT quota_reservation_id
            FROM quota_reservations
            WHERE consumer_id = ?
              AND feature = ?
              AND usage_date = ?
              AND language_code = ?
              AND content_bank_id = ?
              AND bank_version_id = ?
              AND reservation_status = 'available'
              AND reservation_index <= ?
            ORDER BY reservation_index ASC, quota_reservation_id ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        ),
        claimed AS (
            UPDATE quota_reservations qr
            SET reservation_status = 'claimed',
                claim_token = ?,
                claimed_at = ?,
                updated_at = ?
            FROM candidate
            WHERE qr.quota_reservation_id = candidate.quota_reservation_id
              AND qr.reservation_status = 'available'
            RETURNING qr.quota_reservation_id, qr.quota_usage_id
        )
        SELECT quota_reservation_id, quota_usage_id
        FROM claimed
        """,
        (
            consumer["consumer_id"],
            feature,
            usage_date,
            scope[0],
            scope[1],
            scope[2],
            int(consumer["daily_quota_limit"]),
            new_id("qclaim"),
            now,
            now,
        ),
    ).fetchone()
    return None if row is None else row_to_dict(row)


def ensure_quota_tokens(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    request: "SelectionRequest",
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
    quota_limit: int,
) -> None:
    token_target = max(quota_limit, load_legacy_used_count(connection, consumer, usage_date, feature, scope))
    if count_quota_tokens(connection, consumer, usage_date, feature, scope) >= token_target:
        return
    quota_usage = ensure_quota_usage_anchor(connection, consumer, usage_date, feature, scope, quota_limit)
    insert_missing_quota_tokens(connection, consumer, usage_date, feature, scope, quota_usage, token_target)


def ensure_quota_usage_anchor(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
    quota_limit: int,
) -> dict[str, Any]:
    now = utc_now()
    connection.execute(
        """
        INSERT INTO quota_usage (
            quota_usage_id, consumer_id, feature, usage_date,
            language_code, content_bank_id, bank_version_id,
            used_count, quota_limit, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        ON CONFLICT(
            consumer_id,
            feature,
            usage_date,
            language_code,
            content_bank_id,
            bank_version_id
        ) DO NOTHING
        """,
        (
            new_id("quota"),
            consumer["consumer_id"],
            feature,
            usage_date,
            scope[0],
            scope[1],
            scope[2],
            quota_limit,
            now,
        ),
    )
    row = connection.execute(
        """
        SELECT quota_usage_id, used_count
        FROM quota_usage
        WHERE consumer_id = ? AND feature = ? AND usage_date = ?
          AND language_code = ? AND content_bank_id = ? AND bank_version_id = ?
        """,
        (consumer["consumer_id"], feature, usage_date, scope[0], scope[1], scope[2]),
    ).fetchone()
    if row is None:
        raise RuntimeError("quota usage anchor could not be loaded")
    return row_to_dict(row)


def insert_missing_quota_tokens(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
    quota_usage: dict[str, Any],
    token_target: int,
) -> None:
    now = utc_now()
    legacy_used_count = int(quota_usage["used_count"])
    connection.execute(
        INSERT_MISSING_QUOTA_TOKENS_SQL,
        (
            token_target,
            quota_token_scope_key(consumer, usage_date, feature, scope),
            quota_usage["quota_usage_id"],
            consumer["consumer_id"],
            feature,
            usage_date,
            scope[0],
            scope[1],
            scope[2],
            legacy_used_count,
            legacy_used_count,
            now,
            legacy_used_count,
            now,
            now,
            now,
        ),
    )


def load_legacy_used_count(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(used_count, 0) AS used_count
        FROM quota_usage
        WHERE consumer_id = ? AND feature = ? AND usage_date = ?
          AND language_code = ? AND content_bank_id = ? AND bank_version_id = ?
        """,
        (consumer["consumer_id"], feature, usage_date, scope[0], scope[1], scope[2]),
    ).fetchone()
    return 0 if row is None else int(row["used_count"])


def count_quota_tokens(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM quota_reservations
        WHERE consumer_id = ? AND feature = ? AND usage_date = ?
          AND language_code = ? AND content_bank_id = ? AND bank_version_id = ?
        """,
        (consumer["consumer_id"], feature, usage_date, scope[0], scope[1], scope[2]),
    ).fetchone()
    return int(row["count"])


def count_used_quota_reservations(
    connection: PostgreSQLConnection,
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM quota_reservations
        WHERE consumer_id = ? AND feature = ? AND usage_date = ?
          AND language_code = ? AND content_bank_id = ? AND bank_version_id = ?
          AND reservation_status IN (?, ?)
        """,
        (
            consumer["consumer_id"],
            feature,
            usage_date,
            scope[0],
            scope[1],
            scope[2],
            *USED_RESERVATION_STATUSES,
        ),
    ).fetchone()
    return int(row["count"])


def quota_token_scope_key(
    consumer: dict[str, Any],
    usage_date: str,
    feature: str,
    scope: tuple[str, str, str],
) -> str:
    return ":".join(
        (
            str(consumer["consumer_id"]),
            feature,
            usage_date,
            scope[0],
            scope[1],
            scope[2],
        )
    )


def log_quota_exhausted(
    consumer: dict[str, Any],
    request: "SelectionRequest",
    used_count: int,
    quota_limit: int,
) -> None:
    logger.info(
        "quota_exhausted consumer_id=%s feature=%s used=%s limit=%s",
        consumer["consumer_id"],
        quota_feature(request),
        used_count,
        quota_limit,
    )
