"""Telegram quiz poll validation rules."""

from __future__ import annotations

from .telegram_bot_api import TelegramDeliveryError


TELEGRAM_QUESTION_LIMIT = 300
TELEGRAM_OPTION_LIMIT = 100
TELEGRAM_EXPLANATION_LIMIT = 200
TELEGRAM_MIN_OPTIONS = 2
TELEGRAM_MAX_OPTIONS = 12


def validate_delivery_mode(mode: str) -> None:
    if mode not in {"dry_run", "real"}:
        raise ValueError("mode must be dry_run or real")


def validate_telegram_poll(
    question: str,
    options: list[str],
    correct_option_ids: list[int],
    explanation: str,
) -> None:
    if not question:
        raise TelegramDeliveryError("telegram_question_empty")
    if len(question) > TELEGRAM_QUESTION_LIMIT:
        raise TelegramDeliveryError("telegram_question_too_long")
    if len(explanation) > TELEGRAM_EXPLANATION_LIMIT:
        raise TelegramDeliveryError("telegram_explanation_too_long")
    if not TELEGRAM_MIN_OPTIONS <= len(options) <= TELEGRAM_MAX_OPTIONS:
        raise TelegramDeliveryError("telegram_option_count_invalid")
    for option in options:
        if not option or len(option) > TELEGRAM_OPTION_LIMIT:
            raise TelegramDeliveryError("telegram_option_invalid")
    validate_correct_option_ids(correct_option_ids, len(options))


def validate_correct_option_ids(correct_option_ids: list[int], option_count: int) -> None:
    if not correct_option_ids:
        raise TelegramDeliveryError("telegram_correct_option_ids_empty")
    previous = -1
    for option_id in correct_option_ids:
        if option_id <= previous or option_id < 0 or option_id >= option_count:
            raise TelegramDeliveryError("telegram_correct_option_ids_invalid")
        previous = option_id


def parse_correct_option_ids(answer_key: str, option_count: int) -> list[int]:
    try:
        correct_option_id = int(answer_key)
    except ValueError as error:
        raise TelegramDeliveryError("telegram_answer_key_not_numeric") from error
    if correct_option_id < 0 or correct_option_id >= option_count:
        raise TelegramDeliveryError("telegram_answer_key_out_of_range")
    return [correct_option_id]
