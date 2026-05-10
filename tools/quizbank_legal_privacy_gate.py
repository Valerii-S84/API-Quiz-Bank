#!/usr/bin/env python3
"""Build the legal/privacy production gate report."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = ROOT / "reports/compliance/legal_privacy_gate_2026-05-10.json"
DEFAULT_GENERATED_AT = "2026-05-10T00:00:00+00:00"
RETENTION_SCHEDULE = ROOT / "data/governance/privacy_retention_schedule.csv"
VENDOR_REGISTER = ROOT / "data/governance/vendor_register.csv"
PRIVACY_REQUEST_REGISTER = ROOT / "reports/compliance/privacy_request_register.csv"
LEGAL_REVIEW = ROOT / "reports/compliance/legal_review_record.md"
PRIVACY_NOTICE = ROOT / "policies/privacy_notice_baseline.md"
PRIVACY_WORKFLOW = ROOT / "runbooks/privacy_request_workflow.md"


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def contains_text(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8")


def build_report(generated_at: str) -> dict[str, object]:
    retention_rows = read_csv_dicts(RETENTION_SCHEDULE)
    vendor_rows = read_csv_dicts(VENDOR_REGISTER)
    request_rows = read_csv_dicts(PRIVACY_REQUEST_REGISTER)
    pending_vendors = [row["vendor_id"] for row in vendor_rows if row["status"] == "pending"]
    production_rows = [
        row for row in retention_rows if row["retention_production_target"].strip()
    ]
    blockers = [
        "exact public customer legal entity and jurisdiction are not finalized",
        "broad public, school, EU learner-facing and paid launch reviews remain pending",
    ]
    if pending_vendors:
        blockers.append("hosting, observability, backup or payment vendors remain pending")
    return {
        "report_type": "legal_privacy_gate",
        "generated_at": generated_at,
        "decision": "GO protected runtime only; NO-GO broad legal/privacy launch",
        "approved_scope": "owner-operated protected production API runtime",
        "blocked_scopes": [
            "unauthenticated broad public launch",
            "school deployment",
            "EU learner-facing public production",
            "paid public launch",
            "external legal/privacy production claim",
        ],
        "evidence": {
            "legal_review_record": str(LEGAL_REVIEW.relative_to(ROOT)),
            "privacy_notice": str(PRIVACY_NOTICE.relative_to(ROOT)),
            "retention_schedule": str(RETENTION_SCHEDULE.relative_to(ROOT)),
            "privacy_request_workflow": str(PRIVACY_WORKFLOW.relative_to(ROOT)),
            "privacy_request_register_rows": len(request_rows),
            "retention_data_families": len(retention_rows),
            "production_retention_rows": len(production_rows),
            "vendor_rows": len(vendor_rows),
            "pending_vendor_ids": pending_vendors,
        },
        "checks": {
            "owner_protected_runtime_approval_recorded": contains_text(
                LEGAL_REVIEW,
                "GO for owner-operated protected production API runtime",
            ),
            "privacy_notice_exists": PRIVACY_NOTICE.exists(),
            "deletion_export_workflow_exists": PRIVACY_WORKFLOW.exists(),
            "retention_schedule_exists": RETENTION_SCHEDULE.exists(),
            "request_register_exists": PRIVACY_REQUEST_REGISTER.exists(),
        },
        "production_legal_privacy_blockers": blockers,
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    report = build_report(DEFAULT_GENERATED_AT)
    write_report(DEFAULT_REPORT_PATH, report)
    print(report["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
