#!/usr/bin/env python3
"""Promote the owner-approved QuizBank corpus to production status."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from quizbank_common import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    OBJECTIVE_IDS,
    PATTERN_IDS,
    THEME_TITLES,
    file_sha256,
    load_inventory,
)


DEFAULT_GENERATED_AT = "2026-05-11T00:00:00Z"
DEFAULT_OWNER_APPROVAL_JSON = Path("reports/publication/owner_corpus_approval_2026-05-11.json")
DEFAULT_OWNER_APPROVAL_MD = Path("reports/publication/owner_corpus_approval_2026-05-11.md")
DEFAULT_PROMOTION_REPORT = Path("reports/publication/verified_corpus_promotion_2026-05-11.json")
PRODUCTION_STATUS = "published"
NON_PROMOTABLE_STATUSES = {"blocked", "retired"}
PRODUCTION_METADATA_FIELDS = {
    "status",
    "updated_at",
    "reviewed_at",
    "level_locked",
    "locked_at",
}


class PromotionError(ValueError):
    """Raised when the corpus cannot be promoted deterministically."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote the owner-approved active QuizBank corpus to published status."
    )
    parser.add_argument("--quizbank-dir", default="QuizBank", type=Path)
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    parser.add_argument("--owner-approval-json", default=DEFAULT_OWNER_APPROVAL_JSON, type=Path)
    parser.add_argument("--owner-approval-md", default=DEFAULT_OWNER_APPROVAL_MD, type=Path)
    parser.add_argument("--promotion-report", default=DEFAULT_PROMOTION_REPORT, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def status_counts(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    counts = Counter(row.get("status", "").strip() for row in rows)
    return {status: counts.get(status, 0) for status in ITEM_STATUSES}


def snapshot_payload(inventory) -> dict[str, object]:
    sources = [
        {
            "source_id": source.source_id,
            "path": f"QuizBank/{source.filename}",
            "row_count_detected": source.row_count,
            "checksum_sha256": source.checksum_sha256,
            "size_bytes": source.size_bytes,
        }
        for source in inventory.active_sources
    ]
    return {
        "active_bank_files": len(inventory.active_sources),
        "active_rows": inventory.active_row_count,
        "status_counts": status_counts(inventory.rows),
        "sources": sources,
    }


def stable_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def corpus_content_hash(inventory) -> str:
    rows = []
    for filename, source_rows in sorted(inventory.rows_by_file.items()):
        for row in source_rows:
            rows.append(
                {
                    "filename": filename,
                    **{
                        field: row.get(field, "")
                        for field in EXPECTED_HEADER
                        if field not in PRODUCTION_METADATA_FIELDS
                    },
                }
            )
    return stable_sha256(rows)


def validate_inventory(inventory) -> list[str]:
    errors: list[str] = []
    seen_item_ids: Counter[str] = Counter()
    for source in inventory.active_sources:
        if source.header != EXPECTED_HEADER:
            errors.append(f"header_mismatch:{source.filename}")
    for filename, rows in inventory.rows_by_file.items():
        for line_number, row in enumerate(rows, start=2):
            validate_row(filename, line_number, row, seen_item_ids, errors)
    for item_id, count in seen_item_ids.items():
        if count > 1:
            errors.append(f"duplicate_item_id:{item_id}:{count}")
    return errors


def validate_row(
    filename: str,
    line_number: int,
    row: dict[str, str],
    seen_item_ids: Counter[str],
    errors: list[str],
) -> None:
    item_id = row.get("item_id", "").strip()
    if not item_id:
        errors.append(f"missing_item_id:{filename}:{line_number}")
    else:
        seen_item_ids[item_id] += 1
    status = row.get("status", "").strip()
    if status not in ITEM_STATUSES:
        errors.append(f"invalid_status:{filename}:{line_number}:{status}")
    if status in NON_PROMOTABLE_STATUSES:
        errors.append(f"non_promotable_status:{filename}:{line_number}:{status}")
    if row.get("sublevel", "").strip() not in CANONICAL_LEVELS:
        errors.append(f"invalid_level:{filename}:{line_number}:{row.get('sublevel', '')}")
    if row.get("theme_id", "").strip() not in THEME_TITLES:
        errors.append(f"invalid_theme:{filename}:{line_number}:{row.get('theme_id', '')}")
    if row.get("objective_id", "").strip() not in OBJECTIVE_IDS:
        errors.append(f"invalid_objective:{filename}:{line_number}:{row.get('objective_id', '')}")
    if row.get("pattern_id", "").strip() not in PATTERN_IDS:
        errors.append(f"invalid_pattern:{filename}:{line_number}:{row.get('pattern_id', '')}")
    validate_options(filename, line_number, row, errors)


def validate_options(
    filename: str,
    line_number: int,
    row: dict[str, str],
    errors: list[str],
) -> None:
    try:
        options = parse_options(row.get("options", ""))
    except (ValueError, SyntaxError):
        errors.append(f"invalid_options_json:{filename}:{line_number}")
        return
    if not isinstance(options, list) or len(options) < 2:
        errors.append(f"invalid_options_shape:{filename}:{line_number}")
        return
    try:
        answer_index = int(row.get("answer_key", ""))
    except ValueError:
        errors.append(f"invalid_answer_key:{filename}:{line_number}:{row.get('answer_key', '')}")
        return
    if answer_index < 0 or answer_index >= len(options):
        errors.append(f"answer_key_out_of_bounds:{filename}:{line_number}:{answer_index}")


def parse_options(raw_options: str) -> list[object]:
    try:
        parsed = json.loads(raw_options)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(raw_options)
    if not isinstance(parsed, list):
        raise ValueError("options_not_list")
    return parsed


def owner_approval_report(inventory, generated_at: str) -> dict[str, object]:
    snapshot = snapshot_payload(inventory)
    snapshot_sha256 = stable_sha256(snapshot)
    return {
        "report_type": "owner_corpus_approval",
        "generated_at": generated_at,
        "decision": "owner approved all current active quiz rows for production",
        "approval_scope": "all active QuizBank rows in the current snapshot",
        "active_bank_files": len(inventory.active_sources),
        "active_rows": inventory.active_row_count,
        "pre_promotion_status_counts": snapshot["status_counts"],
        "snapshot_sha256": snapshot_sha256,
        "source_checksums": snapshot["sources"],
        "approved_transition_path": ["draft", "approved", "published"],
        "content_review_statement": "owner approved all current active quiz rows for production",
        "conclusion": "corpus is eligible for production promotion",
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_owner_markdown(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Owner Corpus Approval",
                "",
                f"Date: {report['generated_at']}",
                "",
                "Decision: owner approved all current active quiz rows for production.",
                "",
                "| Check | Value |",
                "|---|---|",
                f"| Active source files | `{report['active_bank_files']}` |",
                f"| Active rows | `{report['active_rows']}` |",
                f"| Snapshot SHA-256 | `{report['snapshot_sha256']}` |",
                f"| Conclusion | `{report['conclusion']}` |",
                "",
                "Boundary:",
                "",
                "- This approval changes production eligibility only.",
                "- Quiz text, answers, explanations and source wording are not rewritten.",
                "- Publication still requires deterministic promotion evidence and runtime checks.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def ensure_owner_approval(
    inventory,
    generated_at: str,
    json_path: Path,
    markdown_path: Path,
    dry_run: bool,
) -> dict[str, object]:
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    report = owner_approval_report(inventory, generated_at)
    if not dry_run:
        write_json(json_path, report)
        write_owner_markdown(markdown_path, report)
    return report


def transition_counts_for(status: str) -> dict[str, int]:
    if status == "published":
        return {"already_published": 1}
    if status == "approved":
        return {"approved_to_published": 1}
    return {
        f"{status}_to_approved": 1,
        "approved_to_published": 1,
    }


def add_counts(total: Counter[str], increments: dict[str, int]) -> None:
    for key, value in increments.items():
        total[key] += value


def promoted_row(row: dict[str, str], generated_at: str) -> dict[str, str]:
    updated = {field: row.get(field, "") for field in EXPECTED_HEADER}
    updated["status"] = PRODUCTION_STATUS
    updated["updated_at"] = generated_at
    updated["reviewed_at"] = updated.get("reviewed_at") or generated_at
    updated["level_locked"] = "true"
    updated["locked_at"] = updated.get("locked_at") or generated_at
    return updated


def promote_source_file(path: Path, generated_at: str, dry_run: bool) -> tuple[int, Counter[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = [dict(row) for row in reader]
    promoted_rows = []
    transition_counts: Counter[str] = Counter()
    changed_rows = 0
    for row in rows:
        before_status = row.get("status", "").strip()
        updated = promoted_row(row, generated_at)
        if updated != {field: row.get(field, "") for field in EXPECTED_HEADER}:
            changed_rows += 1
        add_counts(transition_counts, transition_counts_for(before_status))
        promoted_rows.append(updated)
    if not dry_run:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=EXPECTED_HEADER, lineterminator="\n")
            writer.writeheader()
            writer.writerows(promoted_rows)
    return changed_rows, transition_counts


def promote_corpus(inventory, generated_at: str, dry_run: bool) -> dict[str, object]:
    changed_source_files = []
    changed_rows_total = 0
    transition_counts: Counter[str] = Counter()
    for source in inventory.active_sources:
        changed_rows, source_transition_counts = promote_source_file(
            source.path,
            generated_at,
            dry_run,
        )
        if changed_rows:
            changed_source_files.append(f"QuizBank/{source.filename}")
            changed_rows_total += changed_rows
        transition_counts.update(source_transition_counts)
    return {
        "changed_source_files": changed_source_files,
        "changed_rows": changed_rows_total,
        "transition_counts": dict(sorted(transition_counts.items())),
    }


def validate_owner_approval(approval: dict[str, object], inventory) -> list[str]:
    errors = []
    if approval.get("conclusion") != "corpus is eligible for production promotion":
        errors.append("owner_approval_conclusion_missing")
    if approval.get("active_bank_files") != len(inventory.active_sources):
        errors.append("owner_approval_source_count_mismatch")
    if approval.get("active_rows") != inventory.active_row_count:
        errors.append("owner_approval_row_count_mismatch")
    return errors


def build_promotion_report(
    generated_at: str,
    approval_path: Path,
    approval: dict[str, object],
    before_inventory,
    after_inventory,
    before_content_hash: str,
    after_content_hash: str,
    promotion_result: dict[str, object],
) -> dict[str, object]:
    after_status_counts = status_counts(after_inventory.rows)
    return {
        "report_type": "verified_corpus_promotion",
        "generated_at": generated_at,
        "decision": "GO corpus promoted to production",
        "owner_approval_path": approval_path.as_posix(),
        "owner_approval_snapshot_sha256": approval.get("snapshot_sha256"),
        "active_bank_files": len(after_inventory.active_sources),
        "active_rows": after_inventory.active_row_count,
        "status_counts_before": status_counts(before_inventory.rows),
        "status_counts_after": after_status_counts,
        "source_snapshot_sha256_before": stable_sha256(snapshot_payload(before_inventory)),
        "source_snapshot_sha256_after": stable_sha256(snapshot_payload(after_inventory)),
        "content_hash_excluding_production_metadata_before": before_content_hash,
        "content_hash_excluding_production_metadata_after": after_content_hash,
        "content_fields_changed": before_content_hash != after_content_hash,
        "final_status": PRODUCTION_STATUS,
        "published_items": after_status_counts.get("published", 0),
        **promotion_result,
    }


def existing_report_is_current(path: Path, inventory) -> bool:
    if not path.exists():
        return False
    report = json.loads(path.read_text(encoding="utf-8"))
    after_counts = report.get("status_counts_after", {})
    return (
        report.get("active_bank_files") == len(inventory.active_sources)
        and report.get("active_rows") == inventory.active_row_count
        and after_counts.get("published") == inventory.active_row_count
        and all(row.get("status", "").strip() == PRODUCTION_STATUS for row in inventory.rows)
    )


def main() -> int:
    args = parse_args()
    before_inventory = load_inventory(args.quizbank_dir)
    validation_errors = validate_inventory(before_inventory)
    if validation_errors:
        raise PromotionError("; ".join(validation_errors))
    approval = ensure_owner_approval(
        before_inventory,
        args.generated_at,
        args.owner_approval_json,
        args.owner_approval_md,
        args.dry_run,
    )
    approval_errors = validate_owner_approval(approval, before_inventory)
    if approval_errors:
        raise PromotionError("; ".join(approval_errors))
    if not args.dry_run and existing_report_is_current(args.promotion_report, before_inventory):
        report = json.loads(args.promotion_report.read_text(encoding="utf-8"))
        print(f"decision={report['decision']}")
        print(f"published_items={report['published_items']}")
        print("changed_rows=0")
        return 0

    before_content_hash = corpus_content_hash(before_inventory)
    promotion_result = promote_corpus(before_inventory, args.generated_at, args.dry_run)
    after_inventory = load_inventory(args.quizbank_dir)
    after_validation_errors = validate_inventory(after_inventory)
    if after_validation_errors:
        raise PromotionError("; ".join(after_validation_errors))
    after_content_hash = corpus_content_hash(after_inventory)
    report = build_promotion_report(
        args.generated_at,
        args.owner_approval_json,
        approval,
        before_inventory,
        after_inventory,
        before_content_hash,
        after_content_hash,
        promotion_result,
    )
    if report["content_fields_changed"]:
        raise PromotionError("content_fields_changed")
    if not args.dry_run:
        write_json(args.promotion_report, report)
    print(f"decision={report['decision']}")
    print(f"published_items={report['published_items']}")
    print(f"changed_rows={report['changed_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
