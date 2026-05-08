#!/usr/bin/env python3
"""Run a deterministic status-aware selection smoke test."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from quizbank_common import CANONICAL_LEVELS, NORMAL_DELIVERY_STATUSES, THEME_TITLES


DEFAULT_CANONICAL_INPUT_PATH = Path("data/imports/control_sample_items.jsonl")
DEFAULT_REPORT_PATH = Path("reports/delivery/control_selection_report.json")
DEFAULT_GENERATED_AT = "2026-05-07T00:00:00+00:00"
REQUIRED_TRACEABILITY_FIELDS = ("item_id", "source_type", "provenance_note")


def read_jsonl(path: Path) -> list[dict[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def delivered_item_ids(path: Path | None, consumer_id: str) -> set[str]:
    if path is None:
        return set()

    report = json.loads(path.read_text(encoding="utf-8"))
    delivery_log = report.get("delivery_log")
    if not delivery_log:
        return set()
    if delivery_log.get("consumer_id") != consumer_id:
        return set()
    return {delivery_log["quiz_item_id"]}


def matches_filters(item: dict[str, str], cefr_level: str, theme_id: str) -> bool:
    return item.get("sublevel") == cefr_level and item.get("theme_id") == theme_id


def has_traceability(item: dict[str, str]) -> bool:
    return all(item.get(field, "").strip() for field in REQUIRED_TRACEABILITY_FIELDS)


def select_eligible_item(
    items: list[dict[str, str]],
    cefr_level: str,
    theme_id: str,
    delivered_item_ids_for_consumer: set[str],
) -> tuple[dict[str, str] | None, dict[str, object]]:
    matching_items = [item for item in items if matches_filters(item, cefr_level, theme_id)]
    status_counts = Counter(item.get("status", "(missing)") for item in matching_items)
    status_eligible_items = status_eligible_items_with_traceability(matching_items)
    repeat_blocked_items = [
        item for item in status_eligible_items if item["item_id"] in delivered_item_ids_for_consumer
    ]
    eligible_items = [
        item for item in status_eligible_items if item["item_id"] not in delivered_item_ids_for_consumer
    ]
    diagnostics = {
        "candidate_count": len(matching_items),
        "eligible_count": len(eligible_items),
        "rejected_by_status": {
            status: count
            for status, count in sorted(status_counts.items())
            if status not in NORMAL_DELIVERY_STATUSES
        },
        "excluded_by_repeat_count": len(repeat_blocked_items),
        "excluded_by_repeat_item_ids": [item["item_id"] for item in repeat_blocked_items],
        "traceability_violations": traceability_violations(matching_items),
    }
    return (eligible_items[0] if eligible_items else None), diagnostics


def status_eligible_items_with_traceability(
    items: list[dict[str, str]],
) -> list[dict[str, str]]:
    return [
        item
        for item in items
        if item.get("status") in NORMAL_DELIVERY_STATUSES and has_traceability(item)
    ]


def traceability_violations(items: list[dict[str, str]]) -> list[str]:
    return [
        item.get("item_id", "(missing)")
        for item in items
        if item.get("status") in NORMAL_DELIVERY_STATUSES and not has_traceability(item)
    ]


def filters_applied(repeat_policy_applied: bool) -> list[str]:
    filters = [
        "status",
        "cefr_level",
        "theme_id",
        "source_traceability",
    ]
    if repeat_policy_applied:
        filters.append("repeat_policy")
    return filters


def problem_details(
    consumer_id: str,
    cefr_level: str,
    theme_id: str,
    repeat_policy_applied: bool,
) -> dict[str, object]:
    return {
        "type": "https://api.quizbank.example/problems/no-eligible-item",
        "title": "No eligible quiz item",
        "status": 409,
        "instance": "/v1/quiz-items/next",
        "reason_code": "SELECTION_NO_ELIGIBLE_ITEM",
        "selection_context": {
            "consumer_id": consumer_id,
            "cefr_levels": [cefr_level],
            "theme_ids": [theme_id],
            "filters_applied": filters_applied(repeat_policy_applied),
        },
    }


def public_projection(item: dict[str, str]) -> dict[str, str]:
    return {
        "item_id": item["item_id"],
        "language": item["language"],
        "cefr_level": item["sublevel"],
        "theme_id": item["theme_id"],
        "objective_id": item["objective_id"],
        "pattern_id": item["pattern_id"],
        "prompt": item["prompt"],
        "stem_text": item["stem_text"],
        "options": json.loads(item["options"]),
    }


def delivery_log(item: dict[str, str], consumer_id: str) -> dict[str, object]:
    return {
        "delivery_id": "delivery_control_001",
        "selection_request_id": "sel_control_001",
        "consumer_id": consumer_id,
        "quiz_item_id": item["item_id"],
        "item_status": item["status"],
        "source_traceability": {
            "source_type": item["source_type"],
            "provenance_note": item["provenance_note"],
        },
        "delivery_status": "created",
        "reason_summary": "eligible_by_status_level_theme_traceability",
    }


def selection_request_payload(
    consumer_id: str,
    cefr_level: str,
    theme_id: str,
    delivered_item_ids_for_consumer: set[str],
) -> dict[str, object]:
    return {
        "selection_request_id": "sel_control_001",
        "consumer_id": consumer_id,
        "cefr_level": cefr_level,
        "theme_id": theme_id,
        "normal_delivery_statuses": list(NORMAL_DELIVERY_STATUSES),
        "repeat_policy": {
            "applied": bool(delivered_item_ids_for_consumer),
            "delivered_item_ids_for_consumer": sorted(delivered_item_ids_for_consumer),
        },
    }


def selection_problem_payload(
    consumer_id: str,
    cefr_level: str,
    theme_id: str,
    repeat_policy_applied: bool,
) -> dict[str, object] | None:
    return problem_details(
        consumer_id,
        cefr_level,
        theme_id,
        repeat_policy_applied,
    )


def build_report(
    items: list[dict[str, str]],
    consumer_id: str,
    cefr_level: str,
    theme_id: str,
    generated_at: str,
    delivered_item_ids_for_consumer: set[str],
) -> dict[str, object]:
    selected_item, diagnostics = select_eligible_item(
        items,
        cefr_level,
        theme_id,
        delivered_item_ids_for_consumer,
    )
    no_eligible = selected_item is None
    repeat_policy_applied = bool(delivered_item_ids_for_consumer)
    return {
        "report_type": "selection_smoke",
        "generated_at": generated_at,
        "selection_request": selection_request_payload(
            consumer_id,
            cefr_level,
            theme_id,
            delivered_item_ids_for_consumer,
        ),
        "diagnostics": diagnostics,
        "selected_item": None if no_eligible else public_projection(selected_item),
        "problem_details": (
            selection_problem_payload(
                consumer_id,
                cefr_level,
                theme_id,
                repeat_policy_applied,
            )
            if no_eligible
            else None
        ),
        "delivery_created": not no_eligible,
        "delivery_log": None if no_eligible else delivery_log(selected_item, consumer_id),
    }


def validate_request(cefr_level: str, theme_id: str) -> None:
    if cefr_level not in CANONICAL_LEVELS:
        raise ValueError(f"invalid cefr level: {cefr_level}")
    if theme_id not in THEME_TITLES:
        raise ValueError(f"invalid theme id: {theme_id}")


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic selection smoke test.")
    parser.add_argument("--canonical-input", default=DEFAULT_CANONICAL_INPUT_PATH, type=Path)
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--consumer-id", default="consumer_control_normal")
    parser.add_argument("--cefr-level", default="A2")
    parser.add_argument("--theme-id", default="T10")
    parser.add_argument("--delivery-history", type=Path)
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_request(args.cefr_level, args.theme_id)
    except ValueError as error:
        print(f"selection smoke failed: {error}")
        return 1

    items = read_jsonl(args.canonical_input)
    history_item_ids = delivered_item_ids(args.delivery_history, args.consumer_id)
    report = build_report(
        items,
        args.consumer_id,
        args.cefr_level,
        args.theme_id,
        args.generated_at,
        history_item_ids,
    )
    write_report(args.report_out, report)
    status = "no eligible item" if report["selected_item"] is None else "selected item"
    print(f"selection smoke passed: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
