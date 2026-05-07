#!/usr/bin/env python3
"""Report corpus coverage by level, theme, objective and pattern."""

from __future__ import annotations

from quizbank_common import (
    CANONICAL_LEVELS,
    build_arg_parser,
    counter_for,
    load_inventory,
    nested_level_counts,
    print_json,
)


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


def main() -> int:
    parser = build_arg_parser("Report QuizBank coverage map.")
    args = parser.parse_args()
    inventory = load_inventory(args.quizbank_dir)
    gap_map = build_gap_map(inventory)
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

