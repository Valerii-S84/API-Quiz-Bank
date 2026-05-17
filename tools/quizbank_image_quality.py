#!/usr/bin/env python3
"""Validate and report deterministic image quality policy for QuizBank."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_common import CANONICAL_LEVELS, THEME_TITLES, load_inventory, print_json  # noqa: E402
from quizbank_mvp.image_quality_policy import (  # noqa: E402
    ALLOWED_IMAGE_QUALITIES,
    DEFAULT_THEME_GROUP_CONFIG_PATH,
    ImageQualityPolicyError,
    enriched_image_quality_fields,
    load_theme_groups,
    normalize_level,
    resolve_image_quality_decision,
    validate_theme_group_coverage,
)


DEFAULT_GENERATED_AT = "2026-05-17"
DEFAULT_THEME_AUDIT_PATH = Path("reports/image_quality/theme_audit.md")
DEFAULT_BUDGET_REPORT_PATH = Path("reports/image_quality/budget_report.md")
LOW_IMAGE_COST = Decimal("0.013")
MEDIUM_IMAGE_COST = Decimal("0.05")
FORECAST_ITEMS = 30000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate QuizBank image quality policy.")
    parser.add_argument("--quizbank-dir", default="QuizBank", type=Path)
    parser.add_argument("--theme-config", default=DEFAULT_THEME_GROUP_CONFIG_PATH, type=Path)
    parser.add_argument("--theme-audit-out", default=DEFAULT_THEME_AUDIT_PATH, type=Path)
    parser.add_argument("--budget-report-out", default=DEFAULT_BUDGET_REPORT_PATH, type=Path)
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    parser.add_argument("--write-reports", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def theme_audit_rows(inventory, theme_groups: dict[str, str]) -> list[dict[str, object]]:
    counts: Counter[str] = Counter()
    levels: dict[str, set[str]] = defaultdict(set)
    for row in inventory.rows:
        theme_id = row.get("theme_id", "").strip()
        counts[theme_id] += 1
        levels[theme_id].add(normalize_level(row.get("sublevel", "")))
    return [
        {
            "theme_id": theme_id,
            "count": counts[theme_id],
            "levels_present": ",".join(sorted(levels[theme_id])),
            "proposed_theme_group": theme_groups[theme_id],
        }
        for theme_id in sorted(counts)
    ]


def image_quality_decisions(inventory, theme_groups: dict[str, str]) -> list[dict[str, object]]:
    decisions = []
    for row in inventory.rows:
        fields = enriched_image_quality_fields(row, theme_groups)
        if fields["image_quality_recommended"] not in ALLOWED_IMAGE_QUALITIES:
            raise ImageQualityPolicyError("policy returned forbidden image quality")
        decisions.append({"item_id": row["item_id"], **fields})
    return decisions


def budget_payload(inventory, decisions: list[dict[str, object]]) -> dict[str, object]:
    counts = Counter(str(decision["image_quality_recommended"]) for decision in decisions)
    low_count = counts.get("low", 0)
    medium_count = counts.get("medium", 0)
    total_items = inventory.active_row_count
    estimated_medium = round(FORECAST_ITEMS * medium_count / total_items)
    estimated_low = FORECAST_ITEMS - estimated_medium
    return {
        "total_items": total_items,
        "low_count": low_count,
        "medium_count": medium_count,
        "low_cost": str(cost(low_count, LOW_IMAGE_COST)),
        "medium_cost": str(cost(medium_count, MEDIUM_IMAGE_COST)),
        "total_cost": str(cost(low_count, LOW_IMAGE_COST) + cost(medium_count, MEDIUM_IMAGE_COST)),
        "forecast_items": FORECAST_ITEMS,
        "estimated_low_count": estimated_low,
        "estimated_medium_count": estimated_medium,
        "estimated_total_cost": str(
            cost(estimated_low, LOW_IMAGE_COST) + cost(estimated_medium, MEDIUM_IMAGE_COST)
        ),
    }


def cost(count: int, unit_cost: Decimal) -> Decimal:
    return (Decimal(count) * unit_cost).quantize(Decimal("0.001"))


def validate_policy(inventory, theme_groups: dict[str, str], decisions: list[dict[str, object]]) -> None:
    theme_ids = {row.get("theme_id", "").strip() for row in inventory.rows}
    validate_theme_group_coverage(theme_ids, theme_groups)
    if len(theme_ids) == len(THEME_TITLES) and theme_ids != set(THEME_TITLES):
        raise ImageQualityPolicyError("corpus theme ids do not match canonical theme ids")
    for row in inventory.rows:
        normalize_level(row.get("sublevel", ""))
        override = row.get("image_quality_override")
        resolve_image_quality_decision(row["item_id"], row["sublevel"], row["theme_id"], override, theme_groups)
    for decision in decisions:
        if decision["image_quality_recommended"] not in ALLOWED_IMAGE_QUALITIES:
            raise ImageQualityPolicyError("forbidden image quality in decision")
    validate_no_forbidden_quality_values()
    validate_no_policy_randomness()


def validate_no_forbidden_quality_values() -> None:
    provider = ROOT / "src" / "quizbank_mvp" / "visual_provider_openai.py"
    provider_text = provider.read_text(encoding="utf-8")
    if '"high"' in provider_text or '"auto"' in provider_text:
        raise ImageQualityPolicyError("runtime image generation allows high or auto")


def validate_no_policy_randomness() -> None:
    paths = [
        ROOT / "src" / "quizbank_mvp" / "image_quality_policy.py",
        ROOT / "src" / "quizbank_mvp" / "visual_delivery.py",
        ROOT / "src" / "quizbank_mvp" / "visual_provider.py",
        ROOT / "src" / "quizbank_mvp" / "visual_provider_openai.py",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if "import random" in text or "from random" in text or "random." in text:
            raise ImageQualityPolicyError(f"runtime image quality path uses random: {path}")


def write_theme_audit(path: Path, generated_at: str, inventory, rows: list[dict[str, object]]) -> None:
    lines = [
        "# Image Quality Theme Audit",
        "",
        f"Generated: `{generated_at}`",
        "Source: top-level `QuizBank/*.csv`; service template and `QuizBank/staging/` are excluded.",
        "",
        f"Total active items: `{inventory.active_row_count}`",
        f"Canonical themes detected: `{len(rows)}`",
        "",
        "| theme_id | count | levels_present | proposed_theme_group |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {theme_id} | {count} | {levels_present} | {proposed_theme_group} |".format(**row)
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_budget_report(path: Path, generated_at: str, payload: dict[str, object]) -> None:
    lines = [
        "# Image Quality Budget Report",
        "",
        f"Generated: `{generated_at}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| total_items | `{payload['total_items']}` |",
        f"| low_count | `{payload['low_count']}` |",
        f"| medium_count | `{payload['medium_count']}` |",
        f"| low_cost | `${payload['low_cost']}` |",
        f"| medium_cost | `${payload['medium_cost']}` |",
        f"| total_cost | `${payload['total_cost']}` |",
        "",
        "## Forecast For 30,000 Items",
        "",
        "Forecast scales the current deterministic corpus ratio to 30,000 items.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| estimated_low_count | `{payload['estimated_low_count']}` |",
        f"| estimated_medium_count | `{payload['estimated_medium_count']}` |",
        f"| estimated_total_cost | `${payload['estimated_total_cost']}` |",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    inventory = load_inventory(args.quizbank_dir)
    load_theme_groups.cache_clear()
    theme_groups = load_theme_groups(args.theme_config)
    audit_rows = theme_audit_rows(inventory, theme_groups)
    decisions = image_quality_decisions(inventory, theme_groups)
    budget = budget_payload(inventory, decisions)
    validate_policy(inventory, theme_groups, decisions)
    return {
        "report_type": "image_quality_policy",
        "generated_at": args.generated_at,
        "theme_audit": audit_rows,
        "budget": budget,
    }


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args)
    except ImageQualityPolicyError as error:
        print(f"image_quality_policy_error={error}", file=sys.stderr)
        return 1
    if args.write_reports:
        write_theme_audit(args.theme_audit_out, args.generated_at, load_inventory(args.quizbank_dir), report["theme_audit"])
        write_budget_report(args.budget_report_out, args.generated_at, report["budget"])
    if args.format == "json":
        print_json(report)
    else:
        budget = report["budget"]
        print(f"total_items={budget['total_items']}")
        print(f"low_count={budget['low_count']}")
        print(f"medium_count={budget['medium_count']}")
        print(f"total_cost={budget['total_cost']}")
        print(f"estimated_total_cost={budget['estimated_total_cost']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
