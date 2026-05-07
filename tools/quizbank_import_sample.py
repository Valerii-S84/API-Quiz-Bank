#!/usr/bin/env python3
"""Dry-run a single QuizBank source import into local evidence artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from quizbank_common import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    PARSER_PROFILE_ID,
    file_sha256,
)


DEFAULT_SOURCE_PATH = Path("tests/fixtures/control_source/control_sample.csv")
DEFAULT_REGISTRY_PATH = Path("data/registry/source_registry.csv")
DEFAULT_REPORT_PATH = Path("reports/imports/control_sample_import.json")
DEFAULT_GENERATED_AT = "2026-05-07T00:00:00+00:00"


class ImportValidationError(ValueError):
    """Raised when a dry-run import source fails the governed contract."""


def read_source_rows(source_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with source_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        header = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return header, rows


def validate_source(header: list[str], rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if header != EXPECTED_HEADER:
        errors.append("header_mismatch")
    if not rows:
        errors.append("empty_source")

    seen_item_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        item_id = row.get("item_id", "").strip()
        if not item_id:
            errors.append(f"missing_item_id:{line_number}")
        elif item_id in seen_item_ids:
            errors.append(f"duplicate_item_id:{item_id}")
        else:
            seen_item_ids.add(item_id)

        level = row.get("sublevel", "").strip()
        if level not in CANONICAL_LEVELS:
            errors.append(f"invalid_level:{line_number}:{level}")

        status = row.get("status", "").strip()
        if status not in ITEM_STATUSES:
            errors.append(f"invalid_status:{line_number}:{status}")
        elif status != "draft":
            errors.append(f"non_draft_sample_item:{line_number}:{status}")

        try:
            options = json.loads(row.get("options", ""))
        except json.JSONDecodeError:
            errors.append(f"invalid_options_json:{line_number}")
        else:
            if not isinstance(options, list) or len(options) < 2:
                errors.append(f"invalid_options_shape:{line_number}")
            elif not all(isinstance(option, str) and option for option in options):
                errors.append(f"invalid_option_value:{line_number}")

    return errors


def registry_row(
    source_id: str,
    source_path: Path,
    checksum_sha256: str,
    row_count: int,
    generated_at: str,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "path": source_path.as_posix(),
        "format": "CSV",
        "parser_profile_id": PARSER_PROFILE_ID,
        "source_state": "dry_run_passed",
        "checksum_sha256": checksum_sha256,
        "row_count_detected": row_count,
        "registered_at": generated_at,
        "notes": "control sample fixture for MVP import pipeline",
    }


def write_registry(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def public_projection(row: dict[str, str], source_id: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_item_id": row["item_id"],
        "language": row["language"],
        "cefr_level": row["sublevel"],
        "theme_id": row["theme_id"],
        "objective_id": row["objective_id"],
        "pattern_id": row["pattern_id"],
        "prompt": row["prompt"],
        "stem_text": row["stem_text"],
        "options": json.loads(row["options"]),
        "status": row["status"],
    }


def build_report(
    source_id: str,
    source_path: Path,
    rows: list[dict[str, str]],
    checksum_sha256: str,
    generated_at: str,
) -> dict[str, object]:
    return {
        "import_mode": "dry_run",
        "source_id": source_id,
        "source_path": source_path.as_posix(),
        "parser_profile_id": PARSER_PROFILE_ID,
        "checksum_sha256": checksum_sha256,
        "row_count_detected": len(rows),
        "generated_at": generated_at,
        "imported_items": [public_projection(row, source_id) for row in rows],
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")


def run_import(
    source_path: Path,
    registry_path: Path,
    report_path: Path,
    source_id: str,
    generated_at: str,
) -> None:
    header, rows = read_source_rows(source_path)
    errors = validate_source(header, rows)
    if errors:
        raise ImportValidationError("; ".join(errors))

    checksum_sha256 = file_sha256(source_path)
    write_registry(
        registry_path,
        registry_row(source_id, source_path, checksum_sha256, len(rows), generated_at),
    )
    write_report(
        report_path,
        build_report(source_id, source_path, rows, checksum_sha256, generated_at),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run one governed sample CSV import.")
    parser.add_argument("--source", default=DEFAULT_SOURCE_PATH, type=Path)
    parser.add_argument("--registry-out", default=DEFAULT_REGISTRY_PATH, type=Path)
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--source-id", default="sample_control_001")
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_import(
            args.source,
            args.registry_out,
            args.report_out,
            args.source_id,
            args.generated_at,
        )
    except ImportValidationError as error:
        print(f"dry-run import failed: {error}")
        return 1

    print(f"dry-run import passed: {args.source_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
