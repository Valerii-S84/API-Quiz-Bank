"""Telegram delivery worker path for the MVP runtime."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .database import connect, row_to_dict, utc_now
from .projections import build_telegram_quiz_projection
from .selection import SelectionFilters, SelectionRequest, select_next_item
from .telegram_bot_api import (
    TELEGRAM_API_BASE,
    TelegramBotApiAdapter,
    TelegramDeliveryError,
    TelegramImageSendResult,
    TelegramSendResult,
    poll_id_from_result,
    read_http_error_description,
    telegram_api_payload,
)
from .visual_cache import DEFAULT_ASSET_ROOT
from .visual_delivery import VisualDeliveryResolution, resolve_visual_delivery
from .visual_models import VisualDeliveryMode
from .visual_provider import FakeImageProvider, ImageGenerationProvider
from .visual_provider_openai import OpenAIEnvironmentImageProvider


TELEGRAM_QUESTION_LIMIT = 300
TELEGRAM_OPTION_LIMIT = 100
TELEGRAM_EXPLANATION_LIMIT = 200
TELEGRAM_MIN_OPTIONS = 2
TELEGRAM_MAX_OPTIONS = 12


class TelegramAdapter(Protocol):
    def send_quiz_poll(self, payload: dict[str, Any]) -> "TelegramSendResult":
        """Send a validated Telegram quiz poll payload."""

    def send_photo(self, payload: dict[str, Any]) -> "TelegramImageSendResult":
        """Send a Telegram photo payload."""


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
class VisualTelegramResult:
    visual_status: str
    fallback_used: bool
    fallback_reason: str | None = None
    telegram_image_message_id: str | None = None


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


def run_telegram_delivery(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
    adapter: TelegramAdapter | None = None,
    image_provider: ImageGenerationProvider | None = None,
    asset_root: Path = DEFAULT_ASSET_ROOT,
) -> TelegramDeliveryResult:
    validate_delivery_mode(request.mode)
    selection = select_next_item(db_path, selection_request_from_telegram(db_path, request))
    delivery = selection["delivery"]
    delivery_id = str(delivery["delivery_id"])
    item = load_delivery_item(db_path, delivery_id, request.consumer_id)
    return send_loaded_telegram_delivery(db_path, delivery, item, request, adapter, image_provider, asset_root)


def send_existing_telegram_delivery(
    db_path: Path | None,
    delivery_id: str,
    request: TelegramDeliveryRequest,
    adapter: TelegramAdapter | None = None,
    image_provider: ImageGenerationProvider | None = None,
    asset_root: Path = DEFAULT_ASSET_ROOT,
) -> TelegramDeliveryResult:
    validate_delivery_mode(request.mode)
    item = load_delivery_item(db_path, delivery_id, request.consumer_id)
    return send_loaded_telegram_delivery(db_path, item, item, request, adapter, image_provider, asset_root)


def send_loaded_telegram_delivery(
    db_path: Path | None,
    delivery: dict[str, Any],
    item: dict[str, Any],
    request: TelegramDeliveryRequest,
    adapter: TelegramAdapter | None,
    image_provider: ImageGenerationProvider | None,
    asset_root: Path,
) -> TelegramDeliveryResult:
    delivery_id = str(delivery["delivery_id"])
    visual_resolution = resolve_visual_delivery(
        db_path,
        delivery,
        item,
        request.consumer_id,
        default_image_provider(request.mode, image_provider),
        asset_root,
    )
    if visual_resolution.state == "blocked":
        result = blocked_visual_delivery_result(request, item, visual_resolution)
        record_visual_result(
            db_path,
            delivery_id,
            request.consumer_id,
            visual_resolution,
            blocked_visual_telegram_result(visual_resolution),
        )
        record_telegram_result(db_path, result)
        return result
    visual_result = handle_visual_telegram_send(request, item, visual_resolution, adapter)
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
    visual_result = visual_result_after_poll(visual_result, result)
    record_visual_result(db_path, delivery_id, request.consumer_id, visual_resolution, visual_result)
    record_telegram_result(db_path, result)
    return result


def default_image_provider(
    mode: str,
    image_provider: ImageGenerationProvider | None,
) -> ImageGenerationProvider:
    if image_provider is not None:
        return image_provider
    if mode == "real":
        return OpenAIEnvironmentImageProvider()
    return FakeImageProvider()


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


def handle_visual_telegram_send(
    request: TelegramDeliveryRequest,
    item: dict[str, Any],
    resolution: VisualDeliveryResolution,
    adapter: TelegramAdapter | None,
) -> VisualTelegramResult | None:
    if resolution.requested_mode == VisualDeliveryMode.TEXT_ONLY:
        return None
    if not resolution.asset_id or not resolution.image_path:
        return VisualTelegramResult("fallback_used", True, resolution.fallback_reason)
    payload = build_telegram_image_payload(request.chat_id, item, resolution)
    try:
        return send_visual_image(request.mode, payload, adapter)
    except TelegramDeliveryError as error:
        return VisualTelegramResult("failed", True, f"image_send_failed:{error}")


def send_visual_image(
    mode: str,
    payload: dict[str, Any],
    adapter: TelegramAdapter | None,
) -> VisualTelegramResult:
    if mode == "dry_run":
        return VisualTelegramResult("skipped", False, "dry_run_no_bot_api_call")
    if adapter is None or not hasattr(adapter, "send_photo"):
        raise TelegramDeliveryError("real_image_send_requires_adapter")
    send_result = adapter.send_photo(payload)
    return VisualTelegramResult("sent", False, telegram_image_message_id=send_result.message_id)


def blocked_visual_delivery_result(
    request: TelegramDeliveryRequest,
    item: dict[str, Any],
    resolution: VisualDeliveryResolution,
) -> TelegramDeliveryResult:
    reason = resolution.fallback_reason or "VISUAL_DELIVERY_BLOCKED"
    return TelegramDeliveryResult(
        delivery_id=str(item["delivery_id"]),
        consumer_id=request.consumer_id,
        quiz_item_id=str(item["item_id"]),
        mode=request.mode,
        status="failed",
        telegram_target_ref=redact_telegram_target(request.chat_id),
        failure_reason=f"visual_delivery_blocked:{reason}",
    )


def blocked_visual_telegram_result(resolution: VisualDeliveryResolution) -> VisualTelegramResult:
    reason = resolution.fallback_reason or "VISUAL_DELIVERY_BLOCKED"
    return VisualTelegramResult("failed", False, f"visual_delivery_blocked:{reason}")


def visual_result_after_poll(
    visual_result: VisualTelegramResult | None,
    poll_result: TelegramDeliveryResult,
) -> VisualTelegramResult | None:
    if visual_result is None or poll_result.status != "failed":
        return visual_result
    return VisualTelegramResult(
        "failed",
        True,
        f"poll_send_failed:{poll_result.failure_reason}",
        visual_result.telegram_image_message_id,
    )


def build_telegram_image_payload(
    chat_id: str,
    item: dict[str, Any],
    resolution: VisualDeliveryResolution,
) -> dict[str, Any]:
    return {
        "delivery_id": item["delivery_id"],
        "consumer_id": item["consumer_id"],
        "quiz_item_id": item["item_id"],
        "chat_id": chat_id,
        "photo_path": resolution.image_path,
    }


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


def record_visual_result(
    db_path: Path | None,
    delivery_id: str,
    consumer_id: str,
    resolution: VisualDeliveryResolution,
    visual_result: VisualTelegramResult | None,
) -> None:
    if visual_result is None:
        return
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO visual_delivery_results (
                delivery_id, consumer_id, asset_id, requested_delivery_mode,
                resolved_delivery_mode, visual_status, fallback_used,
                fallback_reason, telegram_image_message_id, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(delivery_id) DO UPDATE SET
                asset_id = excluded.asset_id,
                resolved_delivery_mode = excluded.resolved_delivery_mode,
                visual_status = excluded.visual_status,
                fallback_used = excluded.fallback_used,
                fallback_reason = excluded.fallback_reason,
                telegram_image_message_id = excluded.telegram_image_message_id,
                recorded_at = excluded.recorded_at
            """,
            (
                delivery_id,
                consumer_id,
                resolution.asset_id,
                resolution.requested_mode.value,
                resolution.resolved_mode.value,
                visual_result.visual_status,
                int(visual_result.fallback_used),
                visual_result.fallback_reason,
                visual_result.telegram_image_message_id,
                utc_now(),
            ),
        )


def redact_telegram_target(chat_id: str) -> str:
    stripped = chat_id.strip()
    if len(stripped) <= 4:
        return "***"
    return f"***{stripped[-4:]}"
