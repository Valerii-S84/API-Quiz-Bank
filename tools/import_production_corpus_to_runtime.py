#!/usr/bin/env python3
"""Import the promoted production corpus into the runtime database."""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quizbank_common import (
    IMPORT_CONTENT_BANK_LANGUAGE_CODES,
    SUPPORTED_LANGUAGE_CODES,
    THEME_TITLES,
    load_inventory,
)

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_entitlement,
    upsert_quiz_item,
    utc_now,
)
from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools  # noqa: E402
from quizbank_mvp.image_quality_policy import (  # noqa: E402
    DEFAULT_THEME_GROUP_CONFIG_PATH,
    enriched_image_quality_fields,
    load_theme_groups,
    validate_theme_group_coverage,
)


DEFAULT_REPORT_PATH = Path("reports/deploy/production_corpus_runtime_import_2026-05-12.json")
DEFAULT_EXPECTED_ROWS = 30974
DEFAULT_EXPECTED_SOURCES = 115
SMOKE_CONSUMER_ID = "production_corpus_smoke"
SMOKE_API_KEY = "production_corpus_smoke_api_key"
QUOTA_CONSUMER_ID = "production_corpus_quota_blocked"
QUOTA_API_KEY = "production_corpus_quota_blocked_api_key"
NO_ENTITLEMENT_CONSUMER_ID = "consumer_no_entitlement"
NO_ENTITLEMENT_API_KEY = "no_entitlement_api_key"
TARGET_BANK_VERSION_STATUSES = ("draft", "audit", "active")


class RuntimeImportError(RuntimeError):
    """Raised when the runtime import preconditions or checks fail."""


@dataclass(frozen=True)
class RuntimeImportScope:
    language_code: str
    content_bank_id: str
    bank_version_id: str
    target_version_status: str

    def as_report(self) -> dict[str, str]:
        return {
            "language_code": self.language_code,
            "content_bank_id": self.content_bank_id,
            "bank_version_id": self.bank_version_id,
            "target_version_status": self.target_version_status,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a promoted QuizBank corpus into the runtime database."
    )
    parser.add_argument("--quizbank-dir", default="QuizBank", type=Path)
    parser.add_argument("--db-path", default=None, type=Path)
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--executed-at", default="2026-05-12T00:00:00Z")
    parser.add_argument("--expected-published-items", default=DEFAULT_EXPECTED_ROWS, type=int)
    parser.add_argument("--expected-active-sources", default=DEFAULT_EXPECTED_SOURCES, type=int)
    parser.add_argument("--retire-non-corpus-items", action="store_true")
    parser.add_argument("--seed-smoke-consumers", action="store_true")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--commit", action="store_true")
    mode_group.add_argument("--dry-run", action="store_true")
    parser.add_argument("--language-code")
    parser.add_argument("--content-bank-id")
    parser.add_argument("--bank-version-id")
    parser.add_argument("--target-version-status", choices=TARGET_BANK_VERSION_STATUSES)
    parser.add_argument("--approved-active-repair", action="store_true")
    return parser.parse_args()


def effective_dry_run(args: argparse.Namespace) -> bool:
    return not args.commit


def parse_runtime_import_scope(args: argparse.Namespace) -> RuntimeImportScope:
    missing = [
        flag_name
        for flag_name, value in (
            ("language-code", args.language_code),
            ("content-bank-id", args.content_bank_id),
            ("bank-version-id", args.bank_version_id),
            ("target-version-status", args.target_version_status),
        )
        if not str(value or "").strip()
    ]
    if missing:
        raise RuntimeImportError(f"missing_content_scope_args:{','.join(missing)}")
    return RuntimeImportScope(
        language_code=str(args.language_code).strip(),
        content_bank_id=str(args.content_bank_id).strip(),
        bank_version_id=str(args.bank_version_id).strip(),
        target_version_status=str(args.target_version_status).strip(),
    )


def validate_runtime_import_mode(
    args: argparse.Namespace,
    content_scope: RuntimeImportScope,
) -> None:
    if content_scope.language_code not in SUPPORTED_LANGUAGE_CODES:
        raise RuntimeImportError(f"unsupported_language_code:{content_scope.language_code}")
    expected_language = IMPORT_CONTENT_BANK_LANGUAGE_CODES.get(content_scope.content_bank_id)
    if expected_language is not None and expected_language != content_scope.language_code:
        raise RuntimeImportError(
            f"content_bank_language_mismatch:{content_scope.content_bank_id}:"
            f"{expected_language}!={content_scope.language_code}"
        )
    if content_scope.target_version_status == "active" and not args.approved_active_repair:
        raise RuntimeImportError("active_import_requires_approved_repair_mode")
    if args.retire_non_corpus_items and not args.approved_active_repair:
        raise RuntimeImportError("retire_non_corpus_requires_approved_repair_mode")


def parse_options(raw_options: str) -> list[object]:
    try:
        parsed = json.loads(raw_options)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(raw_options)
    if not isinstance(parsed, list):
        raise RuntimeImportError("options_not_list")
    return parsed


def runtime_item(
    row: dict[str, str],
    theme_groups: dict[str, str],
    content_scope: RuntimeImportScope,
) -> dict[str, object]:
    item = dict(row)
    item["options"] = json.dumps(parse_options(row["options"]), ensure_ascii=False)
    item["language_code"] = content_scope.language_code
    item["content_bank_id"] = content_scope.content_bank_id
    item["bank_version_id"] = content_scope.bank_version_id
    item.update(enriched_image_quality_fields(row, theme_groups))
    return item


def validate_inventory(
    inventory,
    expected_rows: int,
    expected_sources: int,
    content_scope: RuntimeImportScope,
) -> None:
    status_counts = Counter(row.get("status", "").strip() for row in inventory.rows)
    language_counts = Counter(row.get("language", "").strip() for row in inventory.rows)
    if inventory.active_row_count != expected_rows:
        raise RuntimeImportError(f"unexpected_active_rows:{inventory.active_row_count}")
    if len(inventory.active_sources) != expected_sources:
        raise RuntimeImportError(f"unexpected_active_sources:{len(inventory.active_sources)}")
    if status_counts.get("published", 0) != expected_rows:
        raise RuntimeImportError(f"unexpected_status_counts:{dict(status_counts)}")
    if set(language_counts) != {content_scope.language_code}:
        raise RuntimeImportError(f"language_scope_mismatch:{dict(language_counts)}")


def validate_image_quality_config(inventory, theme_groups: dict[str, str]) -> None:
    theme_ids = {row.get("theme_id", "").strip() for row in inventory.rows}
    validate_theme_group_coverage(theme_ids, theme_groups)


def scalar_count(db_path: Path | None, sql: str) -> int:
    with connect(db_path) as connection:
        row = connection.execute(sql).fetchone()
    return int(row["count"])


def status_counts(db_path: Path | None) -> dict[str, int]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM quiz_items GROUP BY status ORDER BY status"
        ).fetchall()
    return {row["status"]: int(row["count"]) for row in rows}


def create_temp_id_tables(connection, item_ids: list[str], source_ids: list[str]) -> None:
    connection.execute("DROP TABLE IF EXISTS production_corpus_item_ids")
    connection.execute("DROP TABLE IF EXISTS production_corpus_source_ids")
    connection.execute(
        "CREATE TEMP TABLE production_corpus_item_ids (item_id TEXT PRIMARY KEY)"
    )
    connection.execute(
        "CREATE TEMP TABLE production_corpus_source_ids (source_id TEXT PRIMARY KEY)"
    )
    for item_id in item_ids:
        connection.execute("INSERT INTO production_corpus_item_ids (item_id) VALUES (?)", (item_id,))
    for source_id in source_ids:
        connection.execute(
            "INSERT INTO production_corpus_source_ids (source_id) VALUES (?)", (source_id,)
        )


def import_sources_and_items(
    connection,
    inventory,
    now: str,
    content_scope: RuntimeImportScope,
) -> None:
    source_ids_by_filename = {source.filename: source.source_id for source in inventory.active_sources}
    load_theme_groups.cache_clear()
    theme_groups = load_theme_groups(DEFAULT_THEME_GROUP_CONFIG_PATH)
    for source in inventory.active_sources:
        connection.execute(
            """
            INSERT INTO sources (
                source_id, source_type, provenance_note, checksum_sha256, status,
                created_at, language_code, content_bank_id, bank_version_id
            ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type = excluded.source_type,
                provenance_note = excluded.provenance_note,
                checksum_sha256 = excluded.checksum_sha256,
                status = excluded.status,
                language_code = excluded.language_code,
                content_bank_id = excluded.content_bank_id,
                bank_version_id = excluded.bank_version_id
            """,
            (
                source.source_id,
                "quizbank_csv",
                f"production_promotion:QuizBank/{source.filename}",
                source.checksum_sha256,
                now,
                content_scope.language_code,
                content_scope.content_bank_id,
                content_scope.bank_version_id,
            ),
        )
    for filename, rows in inventory.rows_by_file.items():
        source_id = source_ids_by_filename[filename]
        for row in rows:
            upsert_quiz_item(
                connection,
                runtime_item(row, theme_groups, content_scope),
                row["status"],
                source_id,
            )


def retire_non_corpus_rows(connection, now: str) -> None:
    connection.execute(
        """
        UPDATE quiz_items
        SET status = 'retired', updated_at = ?
        WHERE item_id NOT IN (SELECT item_id FROM production_corpus_item_ids)
          AND status <> 'retired'
        """,
        (now,),
    )
    connection.execute(
        """
        UPDATE sources
        SET status = 'inactive'
        WHERE source_id NOT IN (SELECT source_id FROM production_corpus_source_ids)
          AND status <> 'inactive'
        """
    )


def seed_runtime_smoke_consumers(db_path: Path | None) -> None:
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    themes = list(THEME_TITLES)
    with connect(db_path) as connection:
        connection.execute(
            "DELETE FROM consumer_delivery_state WHERE consumer_id IN (?, ?)",
            (SMOKE_CONSUMER_ID, QUOTA_CONSUMER_ID),
        )
        connection.execute(
            "DELETE FROM deliveries WHERE consumer_id IN (?, ?)",
            (SMOKE_CONSUMER_ID, QUOTA_CONSUMER_ID),
        )
        connection.execute(
            "DELETE FROM quota_usage WHERE consumer_id IN (?, ?)",
            (SMOKE_CONSUMER_ID, QUOTA_CONSUMER_ID),
        )
    seed_consumer(db_path, SMOKE_CONSUMER_ID, 2, levels, themes)
    seed_api_credential(db_path, SMOKE_CONSUMER_ID, SMOKE_API_KEY)
    seed_entitlement(
        db_path,
        SMOKE_CONSUMER_ID,
        levels,
        themes,
        reason="protected production corpus deploy smoke",
    )
    seed_consumer(db_path, QUOTA_CONSUMER_ID, 0, levels, themes)
    seed_api_credential(db_path, QUOTA_CONSUMER_ID, QUOTA_API_KEY)
    seed_entitlement(
        db_path,
        QUOTA_CONSUMER_ID,
        levels,
        themes,
        reason="protected production corpus quota control",
    )
    seed_consumer(db_path, NO_ENTITLEMENT_CONSUMER_ID, 2, ["A2"], ["T10"])
    seed_api_credential(db_path, NO_ENTITLEMENT_CONSUMER_ID, NO_ENTITLEMENT_API_KEY)


def database_counts(db_path: Path | None) -> dict[str, Any]:
    return {
        "quiz_items": scalar_count(db_path, "SELECT COUNT(*) AS count FROM quiz_items"),
        "published_items": scalar_count(
            db_path,
            "SELECT COUNT(*) AS count FROM quiz_items WHERE status = 'published'",
        ),
        "active_sources": scalar_count(
            db_path,
            "SELECT COUNT(*) AS count FROM sources WHERE status = 'active'",
        ),
        "retired_items": scalar_count(
            db_path,
            "SELECT COUNT(*) AS count FROM quiz_items WHERE status = 'retired'",
        ),
        "inactive_sources": scalar_count(
            db_path,
            "SELECT COUNT(*) AS count FROM sources WHERE status = 'inactive'",
        ),
        "status_counts": status_counts(db_path),
        "image_quality_policy_rows": scalar_count(
            db_path,
            "SELECT COUNT(*) AS count FROM quiz_item_image_quality_policy",
        ),
        "image_quality_low_items": scalar_count(
            db_path,
            """
            SELECT COUNT(*) AS count
            FROM quiz_item_image_quality_policy
            WHERE image_quality_recommended = 'low'
            """,
        ),
        "image_quality_medium_items": scalar_count(
            db_path,
            """
            SELECT COUNT(*) AS count
            FROM quiz_item_image_quality_policy
            WHERE image_quality_recommended = 'medium'
            """,
        ),
    }


def validate_database_counts(
    counts: dict[str, Any],
    expected_published_items: int,
    expected_active_sources: int,
) -> None:
    if counts["published_items"] != expected_published_items:
        raise RuntimeImportError(f"unexpected_published_items:{counts['published_items']}")
    if counts["active_sources"] != expected_active_sources:
        raise RuntimeImportError(f"unexpected_active_sources:{counts['active_sources']}")
    if counts["image_quality_policy_rows"] != expected_published_items:
        raise RuntimeImportError(
            f"unexpected_image_quality_policy_rows:{counts['image_quality_policy_rows']}"
        )


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_import(args: argparse.Namespace) -> dict[str, Any]:
    content_scope = parse_runtime_import_scope(args)
    validate_runtime_import_mode(args, content_scope)
    is_dry_run = effective_dry_run(args)
    inventory = load_inventory(args.quizbank_dir)
    load_theme_groups.cache_clear()
    theme_groups = load_theme_groups(DEFAULT_THEME_GROUP_CONFIG_PATH)
    validate_inventory(
        inventory,
        args.expected_published_items,
        args.expected_active_sources,
        content_scope,
    )
    validate_image_quality_config(inventory, theme_groups)
    before_counts = database_counts(args.db_path) if database_exists(args.db_path) else {}
    if is_dry_run:
        after_counts = before_counts
        pool_rebuild = None
    else:
        initialize_database(args.db_path)
        item_ids = [row["item_id"] for row in inventory.rows]
        source_ids = [source.source_id for source in inventory.active_sources]
        now = utc_now()
        with connect(args.db_path) as connection:
            create_temp_id_tables(connection, item_ids, source_ids)
            import_sources_and_items(connection, inventory, now, content_scope)
            if args.retire_non_corpus_items:
                retire_non_corpus_rows(connection, now)
        if args.seed_smoke_consumers:
            seed_runtime_smoke_consumers(args.db_path)
        pool_rebuild = rebuild_candidate_pools(
            args.db_path,
            content_scope.language_code,
            content_scope.content_bank_id,
            content_scope.bank_version_id,
        )
        after_counts = database_counts(args.db_path)
        validate_database_counts(
            after_counts,
            args.expected_published_items,
            args.expected_active_sources,
        )
    return {
        "report_type": "production_corpus_runtime_import",
        "executed_at": args.executed_at,
        "decision": "production_corpus_import_dry_run" if is_dry_run else "production_corpus_import_committed",
        "quizbank_dir": str(args.quizbank_dir),
        "content_scope": content_scope.as_report(),
        "commit_requested": args.commit,
        "approved_active_repair": args.approved_active_repair,
        "expected_published_items": args.expected_published_items,
        "expected_active_sources": args.expected_active_sources,
        "source_active_rows": inventory.active_row_count,
        "source_active_sources": len(inventory.active_sources),
        "retire_non_corpus_items": args.retire_non_corpus_items,
        "seed_smoke_consumers": args.seed_smoke_consumers,
        "candidate_pool_rebuild": pool_rebuild,
        "before_counts": before_counts,
        "after_counts": after_counts,
    }


def database_exists(db_path: Path | None) -> bool:
    if db_path is None:
        return True
    return db_path.exists()


def main() -> int:
    args = parse_args()
    try:
        report = run_import(args)
    except RuntimeImportError as error:
        print(f"production corpus runtime import failed: {error}")
        return 1
    if not effective_dry_run(args):
        write_report(args.report_out, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
