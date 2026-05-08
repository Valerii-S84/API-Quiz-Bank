#!/usr/bin/env python3
"""Report corpus coverage by level, theme, objective and pattern."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from quizbank_common import (
    CANONICAL_LEVELS,
    ITEM_STATUSES,
    OBJECTIVE_IDS,
    PATTERN_IDS,
    THEME_TITLES,
    build_arg_parser,
    counter_for,
    load_inventory,
    nested_level_counts,
    print_json,
)


DEFAULT_REPORT_PATH = Path("reports/coverage/corpus_coverage.json")
DEFAULT_GENERATED_AT = "2026-05-07T00:00:00+00:00"


def count_by_status(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = counter_for(rows, "status")
    return {status: counts.get(status, 0) for status in ITEM_STATUSES}


def level_theme_matrix(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str]] = Counter()
    status_counts: dict[tuple[str, str], Counter[str]] = {}
    for row in rows:
        level = row.get("sublevel", "").strip()
        theme = row.get("theme_id", "").strip()
        status = row.get("status", "").strip()
        if level in CANONICAL_LEVELS and theme in THEME_TITLES:
            key = (level, theme)
            counts[key] += 1
            status_counts.setdefault(key, Counter())[status] += 1

    matrix = []
    for level in CANONICAL_LEVELS:
        for theme_id, title in THEME_TITLES.items():
            key = (level, theme_id)
            total = counts.get(key, 0)
            matrix.append(
                {
                    "cefr_level": level,
                    "theme_id": theme_id,
                    "theme_title": title,
                    "item_count_total": total,
                    "item_count_draft": status_counts.get(key, Counter()).get("draft", 0),
                    "item_count_approved": status_counts.get(key, Counter()).get("approved", 0),
                    "item_count_published": status_counts.get(key, Counter()).get("published", 0),
                    "item_count_retired": status_counts.get(key, Counter()).get("retired", 0),
                    "item_count_blocked": status_counts.get(key, Counter()).get("blocked", 0),
                    "coverage_status": "covered" if total else "gap",
                }
            )
    return matrix


def coverage_status_counts(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], Counter[str]]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in rows:
        key = (
            row.get("sublevel", "").strip(),
            row.get("theme_id", "").strip(),
            row.get("objective_id", "").strip(),
            row.get("pattern_id", "").strip(),
            row.get("status", "").strip(),
        )
        counts[key] += 1

    grouped: dict[tuple[str, str, str, str], Counter[str]] = {}
    for (level, theme, objective, pattern, status), count in counts.items():
        if (
            level in CANONICAL_LEVELS
            and theme in THEME_TITLES
            and objective in OBJECTIVE_IDS
            and pattern in PATTERN_IDS
        ):
            grouped.setdefault((level, theme, objective, pattern), Counter())[status] += count
    return grouped


def coverage_cell(
    key: tuple[str, str, str, str],
    statuses: Counter[str],
    generated_at: str,
) -> dict[str, object]:
    level, theme, objective, pattern = key
    total = sum(statuses.values())
    return {
        "cefr_level": level,
        "primary_theme_id": theme,
        "objective_id": objective,
        "pattern_id": pattern,
        "item_count_total": total,
        "item_count_draft": statuses.get("draft", 0),
        "item_count_approved": statuses.get("approved", 0),
        "item_count_published": statuses.get("published", 0),
        "item_count_retired": statuses.get("retired", 0),
        "item_count_blocked": statuses.get("blocked", 0),
        "coverage_status": "covered" if total else "gap",
        "last_generated_at": generated_at,
    }


def coverage_cells(rows: list[dict[str, str]], generated_at: str) -> list[dict[str, object]]:
    grouped = coverage_status_counts(rows)
    cells = []
    for key, statuses in sorted(grouped.items()):
        cells.append(coverage_cell(key, statuses, generated_at))
    return cells


def build_gap_map(inventory) -> dict[str, object]:
    themes_by_level: dict[str, set[str]] = {level: set() for level in CANONICAL_LEVELS}
    for row in inventory.rows:
        level = row.get("sublevel", "").strip()
        theme = row.get("theme_id", "").strip()
        if level in themes_by_level and theme:
            themes_by_level[level].add(theme)
    return {
        "levels": dict(sorted(counter_for(inventory.rows, "sublevel").items())),
        "themes": nested_level_counts(inventory.rows, "theme_id"),
        "objectives": dict(counter_for(inventory.rows, "objective_id").most_common()),
        "patterns": dict(counter_for(inventory.rows, "pattern_id").most_common()),
        "theme_count_by_level": {
            level: len(themes) for level, themes in sorted(themes_by_level.items())
        },
        "missing_canonical_levels": [
            level for level, count in counter_for(inventory.rows, "sublevel").items()
            if level not in CANONICAL_LEVELS or count == 0
        ],
    }


def build_coverage_report(inventory, generated_at: str) -> dict[str, object]:
    matrix = level_theme_matrix(inventory.rows)
    cells = coverage_cells(inventory.rows, generated_at)
    return {
        "report_type": "coverage",
        "generated_at": generated_at,
        "source": {
            "quizbank_dir": "QuizBank",
            "active_bank_files": len(inventory.active_sources),
            "active_rows": inventory.active_row_count,
        },
        "status_counts": count_by_status(inventory.rows),
        "level_counts": dict(sorted(counter_for(inventory.rows, "sublevel").items())),
        "theme_counts": dict(sorted(counter_for(inventory.rows, "theme_id").items())),
        "objective_counts": dict(counter_for(inventory.rows, "objective_id").most_common()),
        "pattern_counts": dict(counter_for(inventory.rows, "pattern_id").most_common()),
        "level_theme_matrix": matrix,
        "coverage_cells": cells,
        "gap_summary": {
            "level_theme_total_cells": len(matrix),
            "level_theme_covered_cells": len(
                [cell for cell in matrix if cell["coverage_status"] == "covered"]
            ),
            "level_theme_gap_cells": [
                {
                    "cefr_level": cell["cefr_level"],
                    "theme_id": cell["theme_id"],
                }
                for cell in matrix
                if cell["coverage_status"] == "gap"
            ],
        },
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = build_arg_parser("Report QuizBank coverage map.")
    parser.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Write reproducible coverage report artifact.",
    )
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    args = parser.parse_args()
    inventory = load_inventory(args.quizbank_dir)
    gap_map = build_gap_map(inventory)
    if args.write_artifacts:
        write_report(args.report_out, build_coverage_report(inventory, args.generated_at))

    if args.format == "json":
        print_json(gap_map)
    else:
        print("levels=" + ", ".join(f"{key}:{value}" for key, value in gap_map["levels"].items()))
        print(
            "theme_count_by_level="
            + ", ".join(
                f"{key}:{value}" for key, value in gap_map["theme_count_by_level"].items()
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
