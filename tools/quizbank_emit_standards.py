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
            "language": {"type": "string", "const": "de"},
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
    return """openapi: 3.1.0
info:
  title: API Quiz Bank
  version: 0.1.0
  summary: Seed API contract for governed quiz delivery.
servers:
  - url: https://api-quiz-bank.local
    description: Placeholder local/demo API endpoint.
paths:
  /v1/quiz-items/next:
    post:
      operationId: getNextQuizItem
      summary: Select the next eligible quiz item for a governed consumer.
      tags:
        - quiz-delivery
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NextQuizRequest'
      responses:
        '200':
          description: Eligible quiz item projection without public answer leakage.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuizItemPublicProjection'
        '404':
          description: No eligible quiz item is available.
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetails'
        '403':
          description: Consumer is not authorized or entitled.
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetails'
components:
  schemas:
    NextQuizRequest:
      type: object
      additionalProperties: false
      required:
        - consumer_id
      properties:
        consumer_id:
          type: string
          minLength: 1
        cefr_level:
          type: string
          enum: [A1, A2, B1, B2, C1, C2]
        theme_ids:
          type: array
          items:
            type: string
            pattern: '^T(0[1-9]|1[0-8])$'
        objective_ids:
          type: array
          items:
            type: string
            pattern: '^O(0[1-9]|1[0-6])$'
    QuizItemPublicProjection:
      type: object
      additionalProperties: false
      required:
        - item_id
        - language
        - cefr_level
        - theme_id
        - prompt
        - stem_text
        - options
      properties:
        item_id:
          type: string
        language:
          type: string
          const: de
        cefr_level:
          type: string
          enum: [A1, A2, B1, B2, C1, C2]
        theme_id:
          type: string
          pattern: '^T(0[1-9]|1[0-8])$'
        objective_id:
          type: string
          pattern: '^O(0[1-9]|1[0-6])$'
        pattern_id:
          type: string
          pattern: '^P(0[1-9]|1[0-2])$'
        prompt:
          type: string
        stem_text:
          type: string
        options:
          type: array
          minItems: 2
          maxItems: 10
          items:
            type: string
    ProblemDetails:
      type: object
      additionalProperties: true
      required: [type, title, status]
      properties:
        type:
          type: string
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        code:
          type: string
"""


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
