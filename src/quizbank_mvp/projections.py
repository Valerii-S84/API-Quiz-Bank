"""Public, Telegram and admin quiz projection helpers."""

from __future__ import annotations

import json
import re
from typing import Any

from .taxonomy import TOPIC_TITLES


INTERNAL_PROMPT_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)+$")


def learner_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    prompt = public_prompt(str(item["prompt"]))
    stem = str(item["stem_text"]).strip()
    theme_id = str(item["theme_id"])
    return {
        "id": str(item["item_id"]),
        "language": str(item["language"]),
        "question": {
            "text": question_text(prompt, stem),
            "prompt": prompt,
            "stem": stem,
        },
        "options": public_options(json.loads(item["options_json"])),
        "cefr_level": str(item["sublevel"]),
        "theme": {"title": TOPIC_TITLES.get(theme_id, theme_id)},
    }


def telegram_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    prompt = public_prompt(str(item["prompt"]))
    stem = str(item["stem_text"]).strip()
    return {
        "question": question_text(prompt, stem),
        "options": [str(option) for option in json.loads(item["options_json"])],
        "explanation": str(item["explanation"]).strip(),
    }


def admin_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": str(item["item_id"]),
        "language": str(item["language"]),
        "cefr_level": str(item["sublevel"]),
        "theme_id": str(item["theme_id"]),
        "objective_id": str(item["objective_id"]),
        "pattern_id": str(item["pattern_id"]),
        "status": str(item["status"]),
        "prompt": str(item["prompt"]),
        "stem_text": str(item["stem_text"]),
        "options": json.loads(item["options_json"]),
        "source_traceability": {
            "source_id": str(item["source_id"]),
            "source_type": str(item.get("resolved_source_type", item.get("source_type", ""))),
            "provenance_note": str(
                item.get("resolved_provenance_note", item.get("provenance_note", ""))
            ),
        },
    }


def public_prompt(prompt: str) -> str:
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return ""
    if INTERNAL_PROMPT_PATTERN.fullmatch(clean_prompt.lower()):
        return ""
    return clean_prompt


def question_text(prompt: str, stem: str) -> str:
    return f"{prompt}\n{stem}" if prompt else stem


def public_options(options: list[Any]) -> list[dict[str, object]]:
    return [
        {"id": f"option_{index}", "position": index, "text": str(option)}
        for index, option in enumerate(options, start=1)
    ]
