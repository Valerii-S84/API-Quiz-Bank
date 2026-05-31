"""Admin credential checks for governed MVP control surfaces."""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from pathlib import Path

from .credential_hashing import (
    api_key_prefix,
    hash_api_key,
)
from .database_connection import connect
from .problems import QuizBankProblem


READ_ROLES = frozenset({"owner", "content_admin", "read_only_reviewer"})
WRITE_ROLES = frozenset({"owner", "content_admin"})


@dataclass(frozen=True)
class AuthenticatedAdmin:
    actor: str
    role: str
    credential_id: str


def authenticate_admin(db_path: Path | None, admin_key: str | None) -> AuthenticatedAdmin:
    if not admin_key:
        raise admin_auth_problem("ADMIN_AUTH_REQUIRED", "Admin authentication required")
    row = load_admin_credential(db_path, admin_key)
    if row is None:
        raise admin_auth_problem("ADMIN_AUTH_INVALID_KEY", "Admin key is invalid")
    if row["status"] != "active":
        raise admin_auth_problem("ADMIN_CREDENTIAL_INACTIVE", "Admin credential is inactive", 403)
    return AuthenticatedAdmin(
        actor=str(row["actor"]),
        role=str(row["role"]),
        credential_id=str(row["credential_id"]),
    )


def require_admin_read(admin: AuthenticatedAdmin) -> None:
    if admin.role not in READ_ROLES:
        raise admin_auth_problem("ADMIN_ROLE_DENIED", "Admin role is not allowed", 403)


def require_admin_write(admin: AuthenticatedAdmin) -> None:
    if admin.role not in WRITE_ROLES:
        raise admin_auth_problem("ADMIN_WRITE_DENIED", "Admin write role is required", 403)


def require_owner(admin: AuthenticatedAdmin) -> None:
    if admin.role != "owner":
        raise admin_auth_problem("ADMIN_OWNER_REQUIRED", "Owner role is required", 403)


def load_admin_credential(db_path: Path | None, raw_key: str):
    prefix = api_key_prefix(raw_key)
    key_hash = hash_api_key(raw_key)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT credential_id, actor, role, key_hash, status
            FROM admin_credentials
            WHERE key_prefix = ?
            """,
            (prefix,),
        ).fetchall()
    for row in rows:
        if hmac.compare_digest(str(row["key_hash"]), key_hash):
            return row
    return None


def admin_auth_problem(reason_code: str, title: str, status: int = 401) -> QuizBankProblem:
    return QuizBankProblem(
        status,
        reason_code,
        title,
        "Provide active admin credentials with the required role.",
        "https://api.quizbank.example/problems/admin-authentication",
    )
