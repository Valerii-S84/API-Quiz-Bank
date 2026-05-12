#!/usr/bin/env python3
"""Build the production corpus readiness gate report."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from quizbank_common import (
    CANONICAL_LEVELS,
    ITEM_STATUSES,
    NORMAL_DELIVERY_STATUSES,
    PATTERN_IDS,
    THEME_TITLES,
    build_arg_parser,
    counter_for,
    load_inventory,
    print_json,
)


DEFAULT_REPORT_PATH = Path("reports/publication/production_corpus_gate_2026-05-11.json")
DEFAULT_GENERATED_AT = "2026-05-11T00:00:00+00:00"
DEFAULT_OWNER_APPROVAL_PATH = Path("reports/publication/owner_corpus_approval_2026-05-11.json")
DEFAULT_POSTGRESQL_PROOF_PATH = Path(
    "reports/imports/production_corpus_postgresql_smoke_2026-05-11.json"
)
NON_DELIVERABLE_STATUS_CONTROLS = ("draft", "blocked", "retired")


def zero_filled_counts(keys: tuple[str, ...], counts: Counter[str]) -> dict[str, int]:
    return {key: counts.get(key, 0) for key in keys}


def deliverable_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("status", "").strip() in NORMAL_DELIVERY_STATUSES]


def coverage_cell_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("sublevel", "").strip(),
        row.get("theme_id", "").strip(),
        row.get("pattern_id", "").strip(),
    )


def deliverable_coverage_cells(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str, str]] = Counter(
        coverage_cell_key(row)
        for row in rows
        if (
            row.get("sublevel", "").strip() in CANONICAL_LEVELS
            and row.get("theme_id", "").strip() in THEME_TITLES
            and row.get("pattern_id", "").strip() in PATTERN_IDS
        )
    )
    return [
        {
            "cefr_level": level,
            "theme_id": theme_id,
            "pattern_id": pattern_id,
            "deliverable_item_count": count,
        }
        for (level, theme_id, pattern_id), count in sorted(counts.items())
    ]


def build_deliverable_snapshot(rows: list[dict[str, str]]) -> dict[str, object]:
    deliverables = deliverable_rows(rows)
    return {
        "statuses": list(NORMAL_DELIVERY_STATUSES),
        "item_count": len(deliverables),
        "level_counts": zero_filled_counts(CANONICAL_LEVELS, counter_for(deliverables, "sublevel")),
        "theme_counts": zero_filled_counts(tuple(THEME_TITLES), counter_for(deliverables, "theme_id")),
        "pattern_counts": zero_filled_counts(PATTERN_IDS, counter_for(deliverables, "pattern_id")),
        "coverage_cells": deliverable_coverage_cells(deliverables),
        "sample_item_ids": [row["item_id"] for row in deliverables[:10]],
    }


def negative_controls(status_counts: dict[str, int]) -> dict[str, object]:
    return {
        "non_deliverable_statuses": list(NON_DELIVERABLE_STATUS_CONTROLS),
        "current_corpus_counts": {
            status: status_counts.get(status, 0)
            for status in NON_DELIVERABLE_STATUS_CONTROLS
        },
        "runtime_test_refs": [
            "tests/test_mvp_runtime.py::test_retired_items_are_not_delivery_eligible",
            "tests/test_mvp_runtime.py::test_blocked_items_are_not_delivery_eligible",
            "tests/test_reports_selection_invariants.py::test_selection_smoke_report_is_current",
        ],
        "required_after_real_import": [
            "draft items are not selected",
            "blocked items are not selected",
            "retired items are not selected",
            "approved/published items retain source traceability",
        ],
    }


def read_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def owner_approval_summary(
    path: Path,
    approval: dict[str, object] | None,
    inventory,
) -> dict[str, object]:
    if approval is None:
        return {
            "path": path.as_posix(),
            "present": False,
            "valid_for_current_row_count": False,
        }
    return {
        "path": path.as_posix(),
        "present": True,
        "decision": approval.get("decision"),
        "conclusion": approval.get("conclusion"),
        "active_bank_files": approval.get("active_bank_files"),
        "active_rows": approval.get("active_rows"),
        "snapshot_sha256": approval.get("snapshot_sha256"),
        "valid_for_current_row_count": (
            approval.get("active_bank_files") == len(inventory.active_sources)
            and approval.get("active_rows") == inventory.active_row_count
            and approval.get("conclusion") == "corpus is eligible for production promotion"
        ),
    }


def postgresql_proof_summary(
    path: Path,
    proof: dict[str, object] | None,
    deliverable_count: int,
) -> dict[str, object]:
    if proof is None:
        return {
            "path": path.as_posix(),
            "present": False,
            "valid_for_deliverable_count": False,
        }
    checks = proof.get("checks", {})
    if not isinstance(checks, dict):
        checks = {}
    api = proof.get("api_smoke", {})
    if not isinstance(api, dict):
        api = {}
    return {
        "path": path.as_posix(),
        "present": True,
        "report_type": proof.get("report_type"),
        "decision": proof.get("decision"),
        "postgresql_quiz_items": checks.get("quiz_items"),
        "postgresql_published_items": checks.get("published_items"),
        "api_next_item_status": api.get("next_item_status"),
        "api_selected_item_status": api.get("selected_item_status"),
        "valid_for_deliverable_count": (
            proof.get("decision") == "GO PostgreSQL production corpus smoke"
            and checks.get("published_items") == deliverable_count
            and api.get("next_item_status") == 200
            and api.get("selected_item_status") in NORMAL_DELIVERY_STATUSES
        ),
    }


def production_blockers(
    deliverable_count: int,
    status_counts: dict[str, int],
    owner_approval: dict[str, object],
    postgresql_proof: dict[str, object],
) -> list[str]:
    blockers = []
    if deliverable_count == 0:
        blockers.append("approved/published production corpus snapshot is empty")
    for status in NON_DELIVERABLE_STATUS_CONTROLS:
        if status_counts.get(status, 0):
            blockers.append(f"non-deliverable status remains in production corpus: {status}")
    if not owner_approval["valid_for_current_row_count"]:
        blockers.append("owner approval is required before corpus status promotion")
    if not postgresql_proof["valid_for_deliverable_count"]:
        blockers.append("PostgreSQL production content proof is required")
    return blockers


def build_report(
    inventory,
    generated_at: str,
    owner_approval_path: Path,
    postgresql_proof_path: Path,
) -> dict[str, object]:
    status_counts = zero_filled_counts(ITEM_STATUSES, counter_for(inventory.rows, "status"))
    snapshot = build_deliverable_snapshot(inventory.rows)
    deliverable_count = int(snapshot["item_count"])
    owner_approval = owner_approval_summary(
        owner_approval_path,
        read_optional_json(owner_approval_path),
        inventory,
    )
    postgresql_proof = postgresql_proof_summary(
        postgresql_proof_path,
        read_optional_json(postgresql_proof_path),
        deliverable_count,
    )
    blockers = production_blockers(
        deliverable_count,
        status_counts,
        owner_approval,
        postgresql_proof,
    )
    return {
        "report_type": "production_corpus_gate",
        "generated_at": generated_at,
        "decision": "NO-GO production corpus volume" if blockers else "GO production corpus volume",
        "source": {
            "quizbank_dir": "QuizBank",
            "active_bank_files": len(inventory.active_sources),
            "active_rows": inventory.active_row_count,
        },
        "status_counts": status_counts,
        "approved_published_snapshot": snapshot,
        "negative_controls": negative_controls(status_counts),
        "owner_approval": owner_approval,
        "postgresql_content_proof": postgresql_proof,
        "production_content_blockers": blockers,
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = build_arg_parser("Build production corpus readiness gate report.")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    parser.add_argument("--owner-approval", default=DEFAULT_OWNER_APPROVAL_PATH, type=Path)
    parser.add_argument("--postgresql-proof", default=DEFAULT_POSTGRESQL_PROOF_PATH, type=Path)
    args = parser.parse_args()
    report = build_report(
        load_inventory(args.quizbank_dir),
        args.generated_at,
        args.owner_approval,
        args.postgresql_proof,
    )

    if args.write_artifacts:
        write_report(args.report_out, report)
    if args.format == "json":
        print_json(report)
    else:
        print(f"decision={report['decision']}")
        print(f"deliverable_items={report['approved_published_snapshot']['item_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
