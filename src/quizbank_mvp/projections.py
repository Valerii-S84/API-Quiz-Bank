"""Public, Telegram and admin quiz projection helpers."""

from __future__ import annotations

import re
from typing import Any

from .database import decode_json_field
from .taxonomy import objective_label, pattern_label, theme_label


INTERNAL_PROMPT_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)+$")
INTERNAL_PROMPT_WRAPPER_CHARS = "`*_~\"'()[]{}<>:;,.!?¿¡"


def build_learner_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    prompt = public_prompt(str(item["prompt"]))
    stem = str(item["stem_text"]).strip()
    level = str(item["sublevel"])
    theme_id = str(item["theme_id"])
    objective_id = str(item["objective_id"])
    pattern_id = str(item["pattern_id"])
    theme = theme_label(theme_id)
    objective = objective_label(objective_id)
    pattern = pattern_label(pattern_id)
    return {
        "id": str(item["item_id"]),
        "public_id": str(item["item_id"]),
        "language": str(item["language"]),
        "question": {
            "text": question_text(prompt, stem),
            "prompt": prompt,
            "stem": stem,
        },
        "options": public_options(decode_json_field(item["options_json"])),
        "cefr_level": level,
        "theme": theme,
        "objective": objective,
        "pattern": pattern,
        "status": str(item["status"]),
        "metadata": {
            "display": {
                "cefr_level": level,
                "theme_title": theme["title"],
                "theme_slug": theme["slug"],
                "objective_title": objective["title"],
                "pattern_title": pattern["title"],
            }
        },
    }


def build_telegram_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    prompt = public_prompt(str(item["prompt"]))
    stem = str(item["stem_text"]).strip()
    return {
        "question": question_text(prompt, stem),
        "options": [str(option) for option in decode_json_field(item["options_json"])],
        "explanation": str(item["explanation"]).strip(),
    }


def build_admin_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
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
        "options": decode_json_field(item["options_json"]),
        "source_traceability": {
            "source_id": str(item["source_id"]),
            "source_type": str(item.get("resolved_source_type", item.get("source_type", ""))),
            "provenance_note": str(
                item.get("resolved_provenance_note", item.get("provenance_note", ""))
            ),
        },
    }


def learner_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    return build_learner_quiz_projection(item)


def telegram_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    return build_telegram_quiz_projection(item)


def admin_quiz_projection(item: dict[str, Any]) -> dict[str, Any]:
    return build_admin_quiz_projection(item)


def public_prompt(prompt: str) -> str:
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return ""
    if is_internal_prompt_key(clean_prompt):
        return ""
    return clean_prompt


def is_internal_prompt_key(prompt: str) -> bool:
    candidate = prompt.lower().strip(INTERNAL_PROMPT_WRAPPER_CHARS)
    return INTERNAL_PROMPT_PATTERN.fullmatch(candidate) is not None


def question_text(prompt: str, stem: str) -> str:
    return f"{prompt}\n{stem}" if prompt else stem


def public_options(options: list[Any]) -> list[dict[str, object]]:
    return [
        {"id": f"option_{index}", "position": index, "text": str(option)}
        for index, option in enumerate(options, start=1)
    ]
