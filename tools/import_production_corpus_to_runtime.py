#!/usr/bin/env python3
"""Import the promoted production corpus into the runtime database."""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any

from quizbank_common import THEME_TITLES, load_inventory

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


DEFAULT_REPORT_PATH = Path("reports/deploy/production_corpus_runtime_import_2026-05-12.json")
DEFAULT_EXPECTED_ROWS = 30974
DEFAULT_EXPECTED_SOURCES = 115
SMOKE_CONSUMER_ID = "production_corpus_smoke"
SMOKE_API_KEY = "production_corpus_smoke_api_key"
QUOTA_CONSUMER_ID = "production_corpus_quota_blocked"
QUOTA_API_KEY = "production_corpus_quota_blocked_api_key"
NO_ENTITLEMENT_CONSUMER_ID = "consumer_no_entitlement"
NO_ENTITLEMENT_API_KEY = "no_entitlement_api_key"


class RuntimeImportError(RuntimeError):
    """Raised when the runtime import preconditions or checks fail."""


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
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_options(raw_options: str) -> list[object]:
    try:
        parsed = json.loads(raw_options)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(raw_options)
    if not isinstance(parsed, list):
        raise RuntimeImportError("options_not_list")
    return parsed


def runtime_item(row: dict[str, str]) -> dict[str, str]:
    item = dict(row)
    item["options"] = json.dumps(parse_options(row["options"]), ensure_ascii=False)
    return item


def validate_inventory(inventory, expected_rows: int, expected_sources: int) -> None:
    status_counts = Counter(row.get("status", "").strip() for row in inventory.rows)
    if inventory.active_row_count != expected_rows:
        raise RuntimeImportError(f"unexpected_active_rows:{inventory.active_row_count}")
    if len(inventory.active_sources) != expected_sources:
        raise RuntimeImportError(f"unexpected_active_sources:{len(inventory.active_sources)}")
    if status_counts.get("published", 0) != expected_rows:
        raise RuntimeImportError(f"unexpected_status_counts:{dict(status_counts)}")


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


def import_sources_and_items(connection, inventory, now: str) -> None:
    source_ids_by_filename = {source.filename: source.source_id for source in inventory.active_sources}
    for source in inventory.active_sources:
        connection.execute(
            """
            INSERT INTO sources (
                source_id, source_type, provenance_note, checksum_sha256, status, created_at
            ) VALUES (?, ?, ?, ?, 'active', ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type = excluded.source_type,
                provenance_note = excluded.provenance_note,
                checksum_sha256 = excluded.checksum_sha256,
                status = excluded.status
            """,
            (
                source.source_id,
                "quizbank_csv",
                f"production_promotion:QuizBank/{source.filename}",
                source.checksum_sha256,
                now,
            ),
        )
    for filename, rows in inventory.rows_by_file.items():
        source_id = source_ids_by_filename[filename]
        for row in rows:
            upsert_quiz_item(connection, runtime_item(row), row["status"], source_id)


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


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_import(args: argparse.Namespace) -> dict[str, Any]:
    inventory = load_inventory(args.quizbank_dir)
    validate_inventory(inventory, args.expected_published_items, args.expected_active_sources)
    before_counts = database_counts(args.db_path) if database_exists(args.db_path) else {}
    if args.dry_run:
        after_counts = before_counts
    else:
        initialize_database(args.db_path)
        item_ids = [row["item_id"] for row in inventory.rows]
        source_ids = [source.source_id for source in inventory.active_sources]
        now = utc_now()
        with connect(args.db_path) as connection:
            create_temp_id_tables(connection, item_ids, source_ids)
            import_sources_and_items(connection, inventory, now)
            if args.retire_non_corpus_items:
                retire_non_corpus_rows(connection, now)
        if args.seed_smoke_consumers:
            seed_runtime_smoke_consumers(args.db_path)
        after_counts = database_counts(args.db_path)
        validate_database_counts(
            after_counts,
            args.expected_published_items,
            args.expected_active_sources,
        )
    return {
        "report_type": "production_corpus_runtime_import",
        "executed_at": args.executed_at,
        "decision": "production_corpus_import_dry_run" if args.dry_run else "production_corpus_import_committed",
        "quizbank_dir": str(args.quizbank_dir),
        "expected_published_items": args.expected_published_items,
        "expected_active_sources": args.expected_active_sources,
        "source_active_rows": inventory.active_row_count,
        "source_active_sources": len(inventory.active_sources),
        "retire_non_corpus_items": args.retire_non_corpus_items,
        "seed_smoke_consumers": args.seed_smoke_consumers,
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
    if not args.dry_run:
        write_report(args.report_out, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
