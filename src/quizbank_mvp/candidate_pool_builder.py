"""Idempotent candidate pool rebuilds for future queue-based selection."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .database_connection import connect, row_to_dict
from .database_status import DELIVERABLE_STATUSES
from .time_ids import utc_now


@dataclass(frozen=True)
class PoolScope:
    language_code: str
    content_bank_id: str
    bank_version_id: str
    cefr_level: str
    theme_id: str
    objective_id: str
    pattern_id: str


@dataclass(frozen=True)
class PoolRebuild:
    pool_id: str
    scope: PoolScope
    item_count: int
    pool_version: int
    action: str
    source_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "scope": self.scope.__dict__,
            "item_count": self.item_count,
            "pool_version": self.pool_version,
            "action": self.action,
            "source_fingerprint": self.source_fingerprint,
        }


def rebuild_candidate_pools(
    db_path: Path | None,
    language_code: str = "de",
    content_bank_id: str | None = None,
    bank_version_id: str | None = None,
) -> dict[str, object]:
    with connect(db_path) as connection:
        bank_scopes = load_bank_scopes(connection, language_code, content_bank_id, bank_version_id)
        rebuilds = [
            rebuild_pool_scope(connection, scope)
            for bank_scope in bank_scopes
            for scope in load_pool_scopes(connection, bank_scope)
        ]
    return rebuild_summary(language_code, content_bank_id, bank_version_id, rebuilds)


def load_bank_scopes(
    connection: Any,
    language_code: str,
    content_bank_id: str | None,
    bank_version_id: str | None,
) -> list[dict[str, str]]:
    clauses = ["cb.language_code = ?"]
    parameters = [language_code]
    if content_bank_id:
        clauses.append("cb.id = ?")
        parameters.append(content_bank_id)
    if bank_version_id:
        clauses.append("cbv.id = ?")
        parameters.append(bank_version_id)
    else:
        clauses.extend(["cb.status = 'active'", "cbv.status = 'active'"])
    rows = connection.execute(bank_scope_sql(clauses), tuple(parameters)).fetchall()
    return [row_to_dict(row) for row in rows]


def bank_scope_sql(clauses: list[str]) -> str:
    return f"""
        SELECT cb.language_code, cb.id AS content_bank_id, cbv.id AS bank_version_id
        FROM content_banks cb
        JOIN content_bank_versions cbv ON cbv.content_bank_id = cb.id
        WHERE {" AND ".join(clauses)}
        ORDER BY cb.language_code, cb.id, cbv.id
    """


def load_pool_scopes(connection: Any, bank_scope: dict[str, str]) -> list[PoolScope]:
    scopes = {
        scope_key(row_to_pool_scope(row))
        for row in load_current_item_scopes(connection, bank_scope)
    }
    scopes.update(
        scope_key(row_to_pool_scope(row))
        for row in load_existing_pool_scopes(connection, bank_scope)
    )
    return [PoolScope(*key) for key in sorted(scopes)]


def load_current_item_scopes(connection: Any, bank_scope: dict[str, str]):
    return connection.execute(
        """
        SELECT DISTINCT qi.language_code, qi.content_bank_id, qi.bank_version_id,
               qi.sublevel AS cefr_level, qi.theme_id, qi.objective_id, qi.pattern_id
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        WHERE qi.status IN (?, ?)
          AND qi.language_code = ?
          AND qi.content_bank_id = ?
          AND qi.bank_version_id = ?
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        """,
        (*DELIVERABLE_STATUSES, *bank_scope_values(bank_scope)),
    ).fetchall()


def load_existing_pool_scopes(connection: Any, bank_scope: dict[str, str]):
    return connection.execute(
        """
        SELECT language_code, content_bank_id, bank_version_id,
               cefr_level, theme_id, objective_id, pattern_id
        FROM candidate_pools
        WHERE language_code = ?
          AND content_bank_id = ?
          AND bank_version_id = ?
        """,
        bank_scope_values(bank_scope),
    ).fetchall()


def rebuild_pool_scope(connection: Any, scope: PoolScope) -> PoolRebuild:
    items = load_pool_items(connection, scope)
    fingerprint = source_fingerprint(items)
    pool_id = candidate_pool_id(scope)
    existing = load_candidate_pool(connection, pool_id)
    if pool_is_current(existing, fingerprint, len(items)):
        return PoolRebuild(pool_id, scope, len(items), int(existing["pool_version"]), "unchanged", fingerprint)
    pool_version = next_pool_version(existing)
    upsert_candidate_pool(connection, pool_id, scope, fingerprint, len(items), pool_version)
    replace_candidate_pool_items(connection, pool_id, items)
    return PoolRebuild(pool_id, scope, len(items), pool_version, "rebuilt", fingerprint)


def load_pool_items(connection: Any, scope: PoolScope) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT qi.item_id, qi.status, qi.updated_at
        FROM quiz_items qi
        JOIN sources s ON s.source_id = qi.source_id
        WHERE qi.status IN (?, ?)
          AND qi.language_code = ?
          AND qi.content_bank_id = ?
          AND qi.bank_version_id = ?
          AND qi.sublevel = ?
          AND qi.theme_id = ?
          AND qi.objective_id = ?
          AND qi.pattern_id = ?
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
        ORDER BY qi.status ASC, qi.item_id ASC
        """,
        (
            *DELIVERABLE_STATUSES,
            scope.language_code,
            scope.content_bank_id,
            scope.bank_version_id,
            scope.cefr_level,
            scope.theme_id,
            scope.objective_id,
            scope.pattern_id,
        ),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def upsert_candidate_pool(
    connection: Any,
    pool_id: str,
    scope: PoolScope,
    fingerprint: str,
    item_count: int,
    pool_version: int,
) -> None:
    now = utc_now()
    existing = load_candidate_pool(connection, pool_id)
    if existing is None:
        insert_candidate_pool(connection, pool_id, scope, fingerprint, item_count, pool_version, now)
        return
    connection.execute(
        """
        UPDATE candidate_pools
        SET pool_status = 'ready', pool_version = ?, source_fingerprint = ?,
            item_count = ?, rebuilt_at = ?, updated_at = ?
        WHERE pool_id = ?
        """,
        (pool_version, fingerprint, item_count, now, now, pool_id),
    )


def insert_candidate_pool(
    connection: Any,
    pool_id: str,
    scope: PoolScope,
    fingerprint: str,
    item_count: int,
    pool_version: int,
    now: str,
) -> None:
    connection.execute(
        """
        INSERT INTO candidate_pools (
            pool_id, language_code, content_bank_id, bank_version_id,
            cefr_level, theme_id, objective_id, pattern_id, pool_status,
            pool_version, source_fingerprint, item_count, rebuilt_at,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, ?, ?, ?, ?, ?)
        """,
        (
            pool_id,
            scope.language_code,
            scope.content_bank_id,
            scope.bank_version_id,
            scope.cefr_level,
            scope.theme_id,
            scope.objective_id,
            scope.pattern_id,
            pool_version,
            fingerprint,
            item_count,
            now,
            now,
            now,
        ),
    )


def replace_candidate_pool_items(
    connection: Any,
    pool_id: str,
    items: list[dict[str, Any]],
) -> None:
    connection.execute("DELETE FROM candidate_pool_items WHERE pool_id = ?", (pool_id,))
    for position, item in enumerate(items):
        insert_candidate_pool_item(connection, pool_id, position, item)


def insert_candidate_pool_item(
    connection: Any,
    pool_id: str,
    position: int,
    item: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO candidate_pool_items (
            pool_id, item_id, item_status, rank_position, score_snapshot_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            pool_id,
            item["item_id"],
            item["status"],
            position,
            json.dumps({"rank_position": position}, sort_keys=True),
            utc_now(),
        ),
    )


def load_candidate_pool(connection: Any, pool_id: str):
    row = connection.execute(
        "SELECT * FROM candidate_pools WHERE pool_id = ?",
        (pool_id,),
    ).fetchone()
    return None if row is None else row_to_dict(row)


def pool_is_current(existing: dict[str, Any] | None, fingerprint: str, item_count: int) -> bool:
    return (
        existing is not None
        and existing["pool_status"] == "ready"
        and existing["source_fingerprint"] == fingerprint
        and int(existing["item_count"]) == item_count
    )


def next_pool_version(existing: dict[str, Any] | None) -> int:
    if existing is None:
        return 1
    return int(existing["pool_version"]) + 1


def source_fingerprint(items: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in items:
        digest.update(str(item["item_id"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item["status"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item["updated_at"]).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def candidate_pool_id(scope: PoolScope) -> str:
    digest = hashlib.sha256("|".join(scope_key(scope)).encode("utf-8")).hexdigest()
    return f"pool_{digest[:24]}"


def row_to_pool_scope(row: Any) -> PoolScope:
    values = row_to_dict(row)
    return PoolScope(
        str(values["language_code"]),
        str(values["content_bank_id"]),
        str(values["bank_version_id"]),
        str(values["cefr_level"]),
        str(values["theme_id"]),
        str(values["objective_id"]),
        str(values["pattern_id"]),
    )


def scope_key(scope: PoolScope) -> tuple[str, str, str, str, str, str, str]:
    return (
        scope.language_code,
        scope.content_bank_id,
        scope.bank_version_id,
        scope.cefr_level,
        scope.theme_id,
        scope.objective_id,
        scope.pattern_id,
    )


def bank_scope_values(bank_scope: dict[str, str]) -> tuple[str, str, str]:
    return (
        bank_scope["language_code"],
        bank_scope["content_bank_id"],
        bank_scope["bank_version_id"],
    )


def rebuild_summary(
    language_code: str,
    content_bank_id: str | None,
    bank_version_id: str | None,
    rebuilds: list[PoolRebuild],
) -> dict[str, object]:
    rebuilt = [result for result in rebuilds if result.action == "rebuilt"]
    return {
        "language_code": language_code,
        "content_bank_id": content_bank_id,
        "bank_version_id": bank_version_id,
        "pool_count": len(rebuilds),
        "rebuilt_pool_count": len(rebuilt),
        "unchanged_pool_count": len(rebuilds) - len(rebuilt),
        "item_count": sum(result.item_count for result in rebuilds),
        "pools": [result.to_dict() for result in rebuilds],
    }
