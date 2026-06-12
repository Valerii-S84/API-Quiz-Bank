#!/usr/bin/env python3
"""Build a deterministic PostgreSQL load plan from governed import artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from quizbank_common import (
    DEFAULT_CONTENT_BANK_ID,
    DEFAULT_IMPORT_BANK_VERSION,
    DEFAULT_IMPORT_BANK_VERSION_ID,
    DEFAULT_LANGUAGE_CODE,
    IMPORT_TARGET_BANK_VERSION_STATUSES,
    SUPPORTED_LANGUAGE_CODES,
)


DEFAULT_IMPORT_REPORT_PATH = Path("reports/imports/control_sample_import.json")
DEFAULT_CANONICAL_INPUT_PATH = Path("data/imports/control_sample_items.jsonl")
DEFAULT_PLAN_OUT_PATH = Path("reports/imports/control_sample_postgresql_load_plan.json")
CREATED_BY = "tool:quizbank_postgresql_load_plan.py"


class LoadPlanError(ValueError):
    """Raised when import artifacts cannot form a PostgreSQL load plan."""


def default_content_scope() -> dict[str, str]:
    return {
        "language_code": DEFAULT_LANGUAGE_CODE,
        "content_bank_id": DEFAULT_CONTENT_BANK_ID,
        "bank_version_id": DEFAULT_IMPORT_BANK_VERSION_ID,
        "bank_version": DEFAULT_IMPORT_BANK_VERSION,
        "bank_version_status": "draft",
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha256_payload(payload: dict[str, str]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def import_batch_id(source_id: str, import_mode: str) -> str:
    return f"imp_{source_id}_{import_mode}_001"


def validate_inputs(report: dict[str, Any], canonical_items: list[dict[str, str]]) -> None:
    summary = report.get("validation_summary", {})
    if report.get("row_count_detected") != len(canonical_items):
        raise LoadPlanError("row_count_mismatch")
    if summary.get("canonical_item_count") != len(canonical_items):
        raise LoadPlanError("canonical_item_count_mismatch")
    if summary.get("accepted_candidate_count", 0) + summary.get(
        "rejected_candidate_count", 0
    ) > report.get("row_count_detected", 0):
        raise LoadPlanError("candidate_count_exceeds_detected_rows")
    if not canonical_items:
        raise LoadPlanError("empty_canonical_input")

    source_ids = {item.get("source_type", "") for item in canonical_items}
    provenance_notes = {item.get("provenance_note", "") for item in canonical_items}
    if "" in source_ids or "" in provenance_notes:
        raise LoadPlanError("missing_source_traceability")
    validate_content_scope(content_scope_from_report(report), canonical_items)


def content_scope_from_report(report: dict[str, Any]) -> dict[str, str]:
    scope = default_content_scope()
    scope.update(report.get("content_scope", {}))
    return {key: str(value) for key, value in scope.items()}


def validate_content_scope(
    content_scope: dict[str, str],
    canonical_items: list[dict[str, str]],
) -> None:
    language_code = content_scope["language_code"]
    if language_code not in SUPPORTED_LANGUAGE_CODES:
        raise LoadPlanError(f"unsupported_batch_language:{language_code}")
    if content_scope["bank_version_status"] not in IMPORT_TARGET_BANK_VERSION_STATUSES:
        raise LoadPlanError(
            f"invalid_import_bank_version_status:{content_scope['bank_version_status']}"
        )
    for item in canonical_items:
        if item.get("language", "") != language_code:
            raise LoadPlanError(f"language_scope_mismatch:{item.get('item_id', '')}")


def source_row(
    report: dict[str, Any],
    canonical_items: list[dict[str, str]],
    content_scope: dict[str, str],
) -> dict[str, str]:
    first_item = canonical_items[0]
    return {
        "source_id": str(report["source_id"]),
        "source_type": first_item["source_type"],
        "provenance_note": first_item["provenance_note"],
        "checksum_sha256": str(report["checksum_sha256"]),
        "status": "active",
        "created_at": str(report["generated_at"]),
        "language_code": content_scope["language_code"],
        "content_bank_id": content_scope["content_bank_id"],
        "bank_version_id": content_scope["bank_version_id"],
    }


def import_status_for(report: dict[str, Any]) -> str:
    errors = report["validation_summary"].get("validation_errors", [])
    return "dry_run_passed" if not errors else "rejected"


def content_bank_version_row(report: dict[str, Any], content_scope: dict[str, str]) -> dict[str, Any]:
    return {
        "id": content_scope["bank_version_id"],
        "content_bank_id": content_scope["content_bank_id"],
        "version": content_scope["bank_version"],
        "status": content_scope["bank_version_status"],
        "activated_at": None,
        "created_at": report["generated_at"],
    }


def import_batch_row(
    report: dict[str, Any],
    report_path: Path,
    content_scope: dict[str, str],
) -> dict[str, Any]:
    summary = report["validation_summary"]
    batch_id = import_batch_id(str(report["source_id"]), str(report["import_mode"]))
    return {
        "import_batch_id": batch_id,
        "source_id": report["source_id"],
        "parser_profile_id": report["parser_profile_id"],
        "import_mode": report["import_mode"],
        "import_status": import_status_for(report),
        "source_checksum_sha256": report["checksum_sha256"],
        "default_item_status": "draft",
        "row_count_detected": report["row_count_detected"],
        "accepted_candidate_count": summary["accepted_candidate_count"],
        "rejected_candidate_count": summary["rejected_candidate_count"],
        "report_uri": report_path.as_posix(),
        "started_at": report["generated_at"],
        "completed_at": report["generated_at"],
        "created_by": CREATED_BY,
        "language_code": content_scope["language_code"],
        "content_bank_id": content_scope["content_bank_id"],
        "bank_version_id": content_scope["bank_version_id"],
    }


def import_batch_item_rows(
    batch_id: str,
    source_id: str,
    generated_at: str,
    content_scope: dict[str, str],
    canonical_items: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows = []
    for source_row_number, item in enumerate(canonical_items, start=2):
        rows.append(
            {
                "import_batch_id": batch_id,
                "item_id": runtime_item_id(content_scope["bank_version_id"], item["item_id"]),
                "source_id": source_id,
                "source_item_id": item["item_id"],
                "source_row_number": source_row_number,
                "canonical_status": item["status"],
                "content_hash_sha256": sha256_payload(item),
                "created_at": generated_at,
                "language_code": content_scope["language_code"],
                "content_bank_id": content_scope["content_bank_id"],
                "bank_version_id": content_scope["bank_version_id"],
            }
        )
    return rows


def runtime_item_id(bank_version_id: str, source_item_id: str) -> str:
    return f"{bank_version_id}:{source_item_id}"


def validation_result_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    errors = report["validation_summary"].get("validation_errors", [])
    rows = []
    batch_id = import_batch_id(str(report["source_id"]), str(report["import_mode"]))
    for index, error in enumerate(errors, start=1):
        rows.append(
            {
                "validation_result_id": f"val_{batch_id}_{index:03d}",
                "import_batch_id": batch_id,
                "source_id": report["source_id"],
                "source_item_id": None,
                "source_row_number": None,
                "severity": "error",
                "rule_id": str(error).split(":", 1)[0],
                "message": str(error),
                "created_at": report["generated_at"],
            }
        )
    return rows


def build_load_plan(
    report_path: Path,
    canonical_input_path: Path,
) -> dict[str, Any]:
    report = read_json(report_path)
    canonical_items = read_jsonl(canonical_input_path)
    validate_inputs(report, canonical_items)

    content_scope = content_scope_from_report(report)
    batch = import_batch_row(report, report_path, content_scope)
    return {
        "plan_type": "postgresql_load_plan",
        "generated_at": report["generated_at"],
        "content_scope": content_scope,
        "source_artifacts": {
            "import_report_path": report_path.as_posix(),
            "canonical_input_path": canonical_input_path.as_posix(),
        },
        "lineage": {
            "source_id": report["source_id"],
            "import_batch_id": batch["import_batch_id"],
            "language_code": content_scope["language_code"],
            "content_bank_id": content_scope["content_bank_id"],
            "bank_version_id": content_scope["bank_version_id"],
            "quiz_item_count": len(canonical_items),
            "traceability_chain": [
                "content_bank_versions",
                "sources",
                "import_batches",
                "import_batch_items",
                "quiz_items",
                "deliveries",
            ],
        },
        "tables": {
            "content_bank_versions": [content_bank_version_row(report, content_scope)],
            "sources": [source_row(report, canonical_items, content_scope)],
            "import_batches": [batch],
            "import_batch_items": import_batch_item_rows(
                batch["import_batch_id"],
                str(report["source_id"]),
                str(report["generated_at"]),
                content_scope,
                canonical_items,
            ),
            "import_validation_results": validation_result_rows(report),
        },
    }


def write_load_plan(path: Path, plan: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic PostgreSQL load plan from import artifacts."
    )
    parser.add_argument("--import-report", default=DEFAULT_IMPORT_REPORT_PATH, type=Path)
    parser.add_argument("--canonical-input", default=DEFAULT_CANONICAL_INPUT_PATH, type=Path)
    parser.add_argument("--plan-out", default=DEFAULT_PLAN_OUT_PATH, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = build_load_plan(args.import_report, args.canonical_input)
    except LoadPlanError as error:
        print(f"PostgreSQL load plan failed: {error}")
        return 1

    write_load_plan(args.plan_out, plan)
    print(f"PostgreSQL load plan written: {args.plan_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
