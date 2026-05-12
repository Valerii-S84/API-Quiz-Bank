"""Telegram delivery worker path for the MVP runtime."""

from __future__ import annotations

import hashlib
import json
import random
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .database import connect, row_to_dict, utc_now
from .projections import build_telegram_quiz_projection
from .selection import SelectionFilters, SelectionRequest, select_next_item


TELEGRAM_API_BASE = "https://api.telegram.org"
TELEGRAM_QUESTION_LIMIT = 300
TELEGRAM_OPTION_LIMIT = 100
TELEGRAM_EXPLANATION_LIMIT = 200
TELEGRAM_MIN_OPTIONS = 2
TELEGRAM_MAX_OPTIONS = 12


class TelegramDeliveryError(Exception):
    """Raised when a Telegram payload cannot be delivered or validated."""


class TelegramAdapter(Protocol):
    def send_quiz_poll(self, payload: dict[str, Any]) -> "TelegramSendResult":
        """Send a validated Telegram quiz poll payload."""


@dataclass(frozen=True)
class TelegramDeliveryRequest:
    consumer_id: str
    chat_id: str
    mode: str = "dry_run"
    cefr_level: str | None = None
    theme_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    excluded_item_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TelegramSendResult:
    message_id: str
    poll_id: str | None = None


@dataclass(frozen=True)
class TelegramDeliveryResult:
    delivery_id: str
    consumer_id: str
    quiz_item_id: str
    mode: str
    status: str
    telegram_target_ref: str
    telegram_message_id: str | None = None
    telegram_poll_id: str | None = None
    failure_reason: str | None = None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "delivery_id": self.delivery_id,
            "consumer_id": self.consumer_id,
            "quiz_item_id": self.quiz_item_id,
            "mode": self.mode,
            "status": self.status,
            "telegram_target_ref": self.telegram_target_ref,
            "telegram_message_id": self.telegram_message_id,
            "telegram_poll_id": self.telegram_poll_id,
            "failure_reason": self.failure_reason,
        }


class TelegramBotApiAdapter:
    def __init__(self, bot_token: str, api_base: str = TELEGRAM_API_BASE) -> None:
        if not bot_token.strip():
            raise ValueError("Telegram bot token must not be empty")
        self.bot_token = bot_token.strip()
        self.api_base = api_base.rstrip("/")

    def send_quiz_poll(self, payload: dict[str, Any]) -> TelegramSendResult:
        url = f"{self.api_base}/bot{self.bot_token}/sendPoll"
        request = urllib.request.Request(
            url,
            data=json.dumps(telegram_api_payload(payload)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise TelegramDeliveryError(read_http_error_description(error)) from error
        except urllib.error.URLError as error:
            raise TelegramDeliveryError(f"telegram_request_failed:{error.reason}") from error
        if not body.get("ok"):
            description = str(body.get("description", "telegram_send_rejected"))
            raise TelegramDeliveryError(description[:180])
        result = body.get("result", {})
        return TelegramSendResult(
            message_id=str(result.get("message_id", "")),
            poll_id=poll_id_from_result(result),
        )


def run_telegram_delivery(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
    adapter: TelegramAdapter | None = None,
) -> TelegramDeliveryResult:
    validate_delivery_mode(request.mode)
    selection = select_next_item(db_path, selection_request_from_telegram(db_path, request))
    delivery = selection["delivery"]
    delivery_id = str(delivery["delivery_id"])
    item = load_delivery_item(db_path, delivery_id, request.consumer_id)
    try:
        payload = build_telegram_poll_payload(request.chat_id, item)
        result = handle_telegram_send(request.mode, payload, adapter)
    except TelegramDeliveryError as error:
        result = TelegramDeliveryResult(
            delivery_id=delivery_id,
            consumer_id=request.consumer_id,
            quiz_item_id=item["item_id"],
            mode=request.mode,
            status="failed",
            telegram_target_ref=redact_telegram_target(request.chat_id),
            failure_reason=str(error),
        )
    record_telegram_result(db_path, result)
    return result


def selection_request_from_telegram(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
) -> SelectionRequest:
    return SelectionRequest(
        consumer_id=request.consumer_id,
        filters=SelectionFilters(
            cefr_level=request.cefr_level,
            theme_ids=request.theme_ids,
            objective_ids=request.objective_ids,
            pattern_ids=request.pattern_ids,
            excluded_item_ids=telegram_excluded_item_ids(db_path, request),
        ),
        delivery_mode="telegram",
    )


def validate_delivery_mode(mode: str) -> None:
    if mode not in {"dry_run", "real"}:
        raise ValueError("mode must be dry_run or real")


def handle_telegram_send(
    mode: str,
    payload: dict[str, Any],
    adapter: TelegramAdapter | None,
) -> TelegramDeliveryResult:
    delivery_id = str(payload["delivery_id"])
    consumer_id = str(payload["consumer_id"])
    quiz_item_id = str(payload["quiz_item_id"])
    target_ref = redact_telegram_target(str(payload["chat_id"]))
    if mode == "dry_run":
        return TelegramDeliveryResult(
            delivery_id=delivery_id,
            consumer_id=consumer_id,
            quiz_item_id=quiz_item_id,
            mode=mode,
            status="skipped",
            telegram_target_ref=target_ref,
            failure_reason="dry_run_no_bot_api_call",
        )
    if adapter is None:
        raise TelegramDeliveryError("real_send_requires_adapter")
    send_result = adapter.send_quiz_poll(payload)
    return TelegramDeliveryResult(
        delivery_id=delivery_id,
        consumer_id=consumer_id,
        quiz_item_id=quiz_item_id,
        mode=mode,
        status="sent",
        telegram_target_ref=target_ref,
        telegram_message_id=send_result.message_id,
        telegram_poll_id=send_result.poll_id,
    )


def load_delivery_item(
    db_path: Path | None,
    delivery_id: str,
    consumer_id: str,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT qi.*, d.delivery_id, d.consumer_id
            FROM deliveries d
            JOIN quiz_items qi ON qi.item_id = d.quiz_item_id
            WHERE d.delivery_id = ? AND d.consumer_id = ?
            """,
            (delivery_id, consumer_id),
        ).fetchone()
    if row is None:
        raise TelegramDeliveryError("delivery_item_not_found")
    return row_to_dict(row)


def build_telegram_poll_payload(chat_id: str, item: dict[str, Any]) -> dict[str, Any]:
    telegram_quiz = build_telegram_quiz_projection(item)
    question = str(telegram_quiz["question"])
    options, correct_option_ids = shuffled_telegram_options(
        list(telegram_quiz["options"]),
        str(item["answer_key"]),
        str(item["delivery_id"]),
    )
    explanation = build_explanation(item)
    validate_telegram_poll(question, options, correct_option_ids, explanation)
    return {
        "delivery_id": item["delivery_id"],
        "consumer_id": item["consumer_id"],
        "quiz_item_id": item["item_id"],
        "chat_id": chat_id,
        "question": question,
        "options": options,
        "type": "quiz",
        "correct_option_ids": correct_option_ids,
        "explanation": explanation,
        "is_anonymous": True,
    }


def build_explanation(item: dict[str, Any]) -> str:
    explanation = str(item["explanation"]).strip()
    if not explanation:
        raise TelegramDeliveryError("telegram_explanation_empty")
    return explanation


def parse_correct_option_ids(answer_key: str, option_count: int) -> list[int]:
    try:
        correct_option_id = int(answer_key)
    except ValueError as error:
        raise TelegramDeliveryError("telegram_answer_key_not_numeric") from error
    if correct_option_id < 0 or correct_option_id >= option_count:
        raise TelegramDeliveryError("telegram_answer_key_out_of_range")
    return [correct_option_id]


def shuffled_telegram_options(
    options: list[str],
    answer_key: str,
    salt: str,
) -> tuple[list[str], list[int]]:
    correct_option_id = parse_correct_option_ids(answer_key, len(options))[0]
    indexed_options = list(enumerate(options))
    rng = random.Random(stable_shuffle_seed(options, answer_key, salt))
    rng.shuffle(indexed_options)
    shuffled_options = [option for _, option in indexed_options]
    shuffled_correct_id = next(
        index for index, (source_index, _) in enumerate(indexed_options)
        if source_index == correct_option_id
    )
    return shuffled_options, [shuffled_correct_id]


def stable_shuffle_seed(options: list[str], answer_key: str, salt: str) -> int:
    serialized = json.dumps(
        {"answer_key": answer_key, "options": options, "salt": salt},
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(serialized.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


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


def telegram_api_payload(payload: dict[str, Any]) -> dict[str, Any]:
    correct_option_ids = payload["correct_option_ids"]
    if not isinstance(correct_option_ids, list) or len(correct_option_ids) != 1:
        raise TelegramDeliveryError("telegram_bot_api_requires_single_correct_option")
    return {
        "chat_id": payload["chat_id"],
        "question": payload["question"],
        "options": payload["options"],
        "type": payload["type"],
        "correct_option_id": correct_option_ids[0],
        "explanation": payload["explanation"],
        "is_anonymous": payload["is_anonymous"],
    }


def telegram_excluded_item_ids(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
) -> tuple[str, ...]:
    excluded = [*sent_item_ids_for_target(db_path, request.chat_id), *request.excluded_item_ids]
    return tuple(dict.fromkeys(excluded))


def sent_item_ids_for_target(db_path: Path | None, chat_id: str) -> tuple[str, ...]:
    target_ref = redact_telegram_target(chat_id)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT d.quiz_item_id
            FROM telegram_delivery_results t
            JOIN deliveries d ON d.delivery_id = t.delivery_id
            WHERE t.telegram_target_ref = ?
              AND t.status = 'sent'
            ORDER BY t.recorded_at DESC
            """,
            (target_ref,),
        ).fetchall()
    return tuple(str(row["quiz_item_id"]) for row in rows)


def record_telegram_result(db_path: Path | None, result: TelegramDeliveryResult) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO telegram_delivery_results (
                delivery_id, consumer_id, mode, status, telegram_target_ref,
                telegram_message_id, telegram_poll_id, failure_reason, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(delivery_id) DO UPDATE SET
                mode = excluded.mode,
                status = excluded.status,
                telegram_target_ref = excluded.telegram_target_ref,
                telegram_message_id = excluded.telegram_message_id,
                telegram_poll_id = excluded.telegram_poll_id,
                failure_reason = excluded.failure_reason,
                recorded_at = excluded.recorded_at
            """,
            (
                result.delivery_id,
                result.consumer_id,
                result.mode,
                result.status,
                result.telegram_target_ref,
                result.telegram_message_id,
                result.telegram_poll_id,
                result.failure_reason,
                utc_now(),
            ),
        )
        connection.execute(
            """
            UPDATE deliveries
            SET delivery_status = ?
            WHERE delivery_id = ? AND consumer_id = ?
            """,
            (result.status, result.delivery_id, result.consumer_id),
        )


def poll_id_from_result(result: dict[str, Any]) -> str | None:
    poll = result.get("poll")
    if not isinstance(poll, dict):
        return None
    poll_id = poll.get("id")
    return None if poll_id is None else str(poll_id)


def read_http_error_description(error: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(error.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return f"telegram_http_error:{error.code}"
    description = str(body.get("description", f"telegram_http_error:{error.code}"))
    return description[:180]


def redact_telegram_target(chat_id: str) -> str:
    stripped = chat_id.strip()
    if len(stripped) <= 4:
        return "***"
    return f"***{stripped[-4:]}"
