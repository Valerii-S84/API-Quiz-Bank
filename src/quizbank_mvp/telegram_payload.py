"""Telegram quiz poll payload construction."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from .database_runtime import DEFAULT_BANK_VERSION_ID, DEFAULT_CONTENT_BANK_ID, DEFAULT_LANGUAGE_CODE
from .projections import build_telegram_quiz_projection
from .telegram_bot_api import TelegramDeliveryError
from .telegram_poll_validation import parse_correct_option_ids, validate_telegram_poll
from .visual_delivery import VisualDeliveryResolution
from .visual_models import VisualDeliveryMode


def build_telegram_poll_payload(
    chat_id: str,
    item: dict[str, Any],
    visual_resolution: VisualDeliveryResolution | None = None,
) -> dict[str, Any]:
    telegram_quiz = build_telegram_quiz_projection(item)
    question = str(telegram_quiz["question"])
    options, correct_option_ids = shuffled_telegram_options(
        list(telegram_quiz["options"]),
        str(item["answer_key"]),
        str(item["delivery_id"]),
    )
    explanation = build_explanation(item)
    validate_telegram_poll(question, options, correct_option_ids, explanation)
    payload = {
        "delivery_id": item["delivery_id"],
        "consumer_id": item["consumer_id"],
        "quiz_item_id": item["item_id"],
        "language_code": item.get("language_code") or item.get("language") or DEFAULT_LANGUAGE_CODE,
        "content_bank_id": item.get("content_bank_id") or DEFAULT_CONTENT_BANK_ID,
        "bank_version_id": item.get("bank_version_id") or DEFAULT_BANK_VERSION_ID,
        "chat_id": chat_id,
        "question": question,
        "options": options,
        "type": "quiz",
        "correct_option_ids": correct_option_ids,
        "explanation": explanation,
        "is_anonymous": True,
    }
    attach_visual_poll_media(payload, visual_resolution)
    return payload


def attach_visual_poll_media(
    payload: dict[str, Any],
    visual_resolution: VisualDeliveryResolution | None,
) -> None:
    if visual_resolution is None:
        return
    if visual_resolution.requested_mode == VisualDeliveryMode.TEXT_ONLY:
        return
    if not visual_resolution.asset_id or not visual_resolution.image_path:
        return
    payload["poll_media_path"] = visual_resolution.image_path


def build_explanation(item: dict[str, Any]) -> str:
    explanation = str(item["explanation"]).strip()
    if not explanation:
        raise TelegramDeliveryError("telegram_explanation_empty")
    return explanation


def shuffled_telegram_options(
    options: list[str],
    answer_key: str,
    salt: str,
) -> tuple[list[str], list[int]]:
    correct_option_id = parse_correct_option_ids(answer_key, len(options))[0]
    indexed_options = list(enumerate(options))
    rng = random.Random(stable_shuffle_seed(options, answer_key, salt))
    rng.shuffle(indexed_options)
    indexed_options = move_correct_option_from_first_position(
        indexed_options,
        correct_option_id,
        salt,
    )
    shuffled_options = [option for _, option in indexed_options]
    shuffled_correct_id = next(
        index for index, (source_index, _) in enumerate(indexed_options)
        if source_index == correct_option_id
    )
    return shuffled_options, [shuffled_correct_id]


def move_correct_option_from_first_position(
    indexed_options: list[tuple[int, str]],
    correct_option_id: int,
    salt: str,
) -> list[tuple[int, str]]:
    if len(indexed_options) <= 1 or indexed_options[0][0] != correct_option_id:
        return indexed_options
    swap_index = 1 + stable_index(salt, len(indexed_options) - 1)
    moved_options = list(indexed_options)
    moved_options[0], moved_options[swap_index] = moved_options[swap_index], moved_options[0]
    return moved_options


def stable_index(salt: str, modulo: int) -> int:
    digest = hashlib.sha256(salt.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulo


def stable_shuffle_seed(options: list[str], answer_key: str, salt: str) -> int:
    serialized = json.dumps(
        {"answer_key": answer_key, "options": options, "salt": salt},
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(serialized.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")
