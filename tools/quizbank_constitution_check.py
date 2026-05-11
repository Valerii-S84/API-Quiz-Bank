#!/usr/bin/env python3
"""Validate core constitution invariants for the current QuizBank corpus."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from quizbank_common import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    build_arg_parser,
    inventory_summary,
    load_inventory,
    print_json,
)


DEFAULT_OWNER_APPROVAL_PATH = Path("reports/publication/owner_corpus_approval_2026-05-11.json")


def owner_approval_allows_production_statuses(path: Path, inventory) -> bool:
    if not path.exists():
        return False
    report = json.loads(path.read_text(encoding="utf-8"))
    return (
        report.get("conclusion") == "corpus is eligible for production promotion"
        and report.get("active_bank_files") == len(inventory.active_sources)
        and report.get("active_rows") == inventory.active_row_count
    )


def check_inventory(inventory, allow_production_statuses: bool = False) -> dict[str, list[str]]:
    violations: dict[str, list[str]] = {
        "header_mismatch": [],
        "invalid_level": [],
        "invalid_status": [],
        "non_draft_active_item_without_owner_approval": [],
        "missing_item_id": [],
        "duplicate_item_id": [],
    }

    item_ids: Counter[str] = Counter()
    for source in inventory.active_sources:
        if source.header != EXPECTED_HEADER:
            violations["header_mismatch"].append(source.filename)

    for filename, rows in inventory.rows_by_file.items():
        for line_number, row in enumerate(rows, start=2):
            item_id = row.get("item_id", "").strip()
            level = row.get("sublevel", "").strip()
            status = row.get("status", "").strip()
            if not item_id:
                violations["missing_item_id"].append(f"{filename}:{line_number}")
            else:
                item_ids[item_id] += 1
            if level not in CANONICAL_LEVELS:
                violations["invalid_level"].append(f"{filename}:{line_number}:{level}")
            if status not in ITEM_STATUSES:
                violations["invalid_status"].append(f"{filename}:{line_number}:{status}")
            if status != "draft" and not allow_production_statuses:
                violations["non_draft_active_item_without_owner_approval"].append(
                    f"{filename}:{line_number}:{status}"
                )

    for item_id, count in item_ids.items():
        if count > 1:
            violations["duplicate_item_id"].append(f"{item_id}:{count}")

    return {key: value for key, value in violations.items() if value}


def main() -> int:
    parser = build_arg_parser("Run QuizBank constitution checks.")
    parser.add_argument("--owner-approval", default=DEFAULT_OWNER_APPROVAL_PATH, type=Path)
    args = parser.parse_args()

    inventory = load_inventory(args.quizbank_dir)
    summary = inventory_summary(inventory)
    violations = check_inventory(
        inventory,
        owner_approval_allows_production_statuses(args.owner_approval, inventory),
    )
    payload = {
        "active_bank_files": summary["active_bank_files"],
        "active_rows": summary["active_rows"],
        "violations": sum(len(items) for items in violations.values()),
        "breakdown": violations,
    }

    if args.format == "json":
        print_json(payload)
    else:
        print(
            "active_bank_files={active_bank_files} active_rows={active_rows} violations={violations}".format(
                **payload
            )
        )
        print(f"breakdown={violations}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
