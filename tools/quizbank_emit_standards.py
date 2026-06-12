#!/usr/bin/env python3
"""Emit seed schema, taxonomy and OpenAPI artifacts from the current corpus."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from quizbank_common import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    SUPPORTED_LANGUAGE_CODES,
    THEME_TITLES,
    counter_for,
    load_inventory,
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, object]],
    lineterminator: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer_options = {}
    if lineterminator is not None:
        writer_options["lineterminator"] = lineterminator
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, **writer_options)
        writer.writeheader()
        writer.writerows(rows)


def canonical_schema() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://api-quiz-bank.local/schemas/canonical_quiz_item.schema.json",
        "title": "API Quiz Bank Canonical Quiz Item",
        "type": "object",
        "additionalProperties": False,
        "required": EXPECTED_HEADER,
        "properties": {
            "item_id": {"type": "string", "minLength": 1},
            "language": {"type": "string", "enum": list(SUPPORTED_LANGUAGE_CODES)},
            "level_band": {"type": "string", "minLength": 1},
            "sublevel": {"type": "string", "enum": list(CANONICAL_LEVELS)},
            "theme_id": {"type": "string", "pattern": "^T(0[1-9]|1[0-8])$"},
            "subtheme_id": {"type": "string"},
            "objective_id": {"type": "string", "pattern": "^O(0[1-9]|1[0-6])$"},
            "pattern_id": {"type": "string", "pattern": "^P(0[1-9]|1[0-2])$"},
            "difficulty_band": {"type": "string"},
            "register": {"type": "string"},
            "prompt": {"type": "string", "minLength": 1},
            "stem_text": {"type": "string", "minLength": 1},
            "options": {"type": "string", "minLength": 1},
            "answer_key": {"type": "string", "minLength": 1},
            "explanation": {"type": "string"},
            "tags": {"type": "string"},
            "coverage_cell_id": {"type": "string"},
            "status": {"type": "string", "enum": list(ITEM_STATUSES)},
            "version": {"type": "string"},
            "source_type": {"type": "string"},
            "provenance_note": {"type": "string"},
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "reviewed_at": {"type": "string"},
            "level_locked": {"type": "string"},
            "locked_at": {"type": "string"},
        },
    }


def write_taxonomy(inventory) -> None:
    level_counts = counter_for(inventory.rows, "sublevel")
    theme_counts = counter_for(inventory.rows, "theme_id")
    objective_counts = counter_for(inventory.rows, "objective_id")
    pattern_counts = counter_for(inventory.rows, "pattern_id")
    write_cefr_levels(level_counts)
    write_themes(theme_counts)
    write_objectives(objective_counts)
    write_patterns(pattern_counts)


def write_cefr_levels(level_counts) -> None:
    write_csv(
        Path("data/taxonomy/cefr_levels.csv"),
        ["cefr_level", "order_index", "observed_item_count", "status"],
        [
            {
                "cefr_level": level,
                "order_index": index,
                "observed_item_count": level_counts[level],
                "status": "active",
            }
            for index, level in enumerate(CANONICAL_LEVELS, start=1)
        ],
    )


def write_themes(theme_counts) -> None:
    write_csv(
        Path("data/taxonomy/themes.csv"),
        ["theme_id", "title", "observed_item_count", "status", "label_status"],
        [
            {
                "theme_id": theme_id,
                "title": title,
                "observed_item_count": theme_counts[theme_id],
                "status": "active",
                "label_status": "canonical",
            }
            for theme_id, title in THEME_TITLES.items()
        ],
        lineterminator="\n",
    )


def write_objectives(objective_counts) -> None:
    write_csv(
        Path("data/taxonomy/objectives.csv"),
        ["objective_id", "title", "observed_item_count", "status", "label_status"],
        [
            {
                "objective_id": f"O{index:02d}",
                "title": f"Objective O{index:02d}",
                "observed_item_count": objective_counts[f"O{index:02d}"],
                "status": "active",
                "label_status": "seed",
            }
            for index in range(1, 17)
        ],
    )


def write_patterns(pattern_counts) -> None:
    write_csv(
        Path("data/taxonomy/patterns.csv"),
        ["pattern_id", "title", "observed_item_count", "status", "label_status"],
        [
            {
                "pattern_id": f"P{index:02d}",
                "title": f"Pattern P{index:02d}",
                "observed_item_count": pattern_counts[f"P{index:02d}"],
                "status": "active",
                "label_status": "seed",
            }
            for index in range(1, 13)
        ],
    )


def openapi_seed() -> str:
    return Path("api/openapi.template.yaml").read_text(encoding="utf-8")


def main() -> int:
    inventory = load_inventory(Path("QuizBank"))
    write_taxonomy(inventory)
    write_text(
        Path("schemas/canonical_quiz_item.schema.json"),
        json.dumps(canonical_schema(), ensure_ascii=False, indent=2) + "\n",
    )
    write_text(Path("api/openapi.yaml"), openapi_seed())
    print("wrote schema, taxonomy and OpenAPI seed artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
