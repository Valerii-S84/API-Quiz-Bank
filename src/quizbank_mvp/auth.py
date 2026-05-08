"""Consumer-bound API credential checks for the MVP runtime."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from pathlib import Path

from .database import connect
from .selection import QuizBankProblem


API_KEY_PREFIX_LENGTH = 12


@dataclass(frozen=True)
class AuthenticatedConsumer:
    consumer_id: str
    credential_id: str


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def api_key_prefix(raw_key: str) -> str:
    return raw_key[:API_KEY_PREFIX_LENGTH]


def authenticate_consumer(
    db_path: Path | None,
    x_consumer_id: str | None,
    x_api_key: str | None,
) -> AuthenticatedConsumer:
    require_headers(x_consumer_id, x_api_key)
    row = load_credential(db_path, x_consumer_id or "", x_api_key or "")
    if row is None:
        raise auth_problem("AUTH_INVALID_API_KEY", "API key is invalid")
    if row["credential_status"] != "active":
        raise auth_problem("AUTH_CREDENTIAL_INACTIVE", "API credential is inactive", 403)
    if row["consumer_status"] != "active":
        raise auth_problem("CONSUMER_NOT_ACTIVE", "Consumer is not active", 403)
    return AuthenticatedConsumer(
        consumer_id=str(row["consumer_id"]),
        credential_id=str(row["credential_id"]),
    )


def require_headers(x_consumer_id: str | None, x_api_key: str | None) -> None:
    if not x_consumer_id or not x_api_key:
        raise auth_problem("AUTH_REQUIRED", "Authentication required")


def load_credential(db_path: Path | None, consumer_id: str, raw_key: str):
    prefix = api_key_prefix(raw_key)
    key_hash = hash_api_key(raw_key)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT ac.credential_id, ac.consumer_id, ac.key_hash,
                   ac.status AS credential_status, c.status AS consumer_status
            FROM api_credentials ac
            JOIN consumers c ON c.consumer_id = ac.consumer_id
            WHERE ac.consumer_id = ? AND ac.key_prefix = ?
            """,
            (consumer_id, prefix),
        ).fetchall()
    for row in rows:
        if hmac.compare_digest(str(row["key_hash"]), key_hash):
            return row
    return None


def auth_problem(reason_code: str, title: str, status: int = 401) -> QuizBankProblem:
    return QuizBankProblem(
        status,
        reason_code,
        title,
        "Provide valid consumer-bound API credentials.",
        "https://api.quizbank.example/problems/authentication",
    )
