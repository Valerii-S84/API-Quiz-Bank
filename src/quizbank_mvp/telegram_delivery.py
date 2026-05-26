"""Telegram delivery orchestration for the MVP runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
from .telegram_models import (
    TelegramAdapter,
    TelegramDeliveryRequest,
    TelegramDeliveryResult,
    VisualTelegramResult,
)
from .telegram_payload import (
    attach_visual_poll_media,
    build_explanation,
    build_telegram_poll_payload,
    move_correct_option_from_first_position,
    shuffled_telegram_options,
    stable_index,
    stable_shuffle_seed,
)
from .telegram_poll_validation import (
    TELEGRAM_EXPLANATION_LIMIT,
    TELEGRAM_MAX_OPTIONS,
    TELEGRAM_MIN_OPTIONS,
    TELEGRAM_OPTION_LIMIT,
    TELEGRAM_QUESTION_LIMIT,
    parse_correct_option_ids,
    validate_correct_option_ids,
    validate_delivery_mode,
    validate_telegram_poll,
)
from .telegram_result_repository import (
    load_delivery_item,
    record_telegram_result,
    record_visual_result,
    redact_telegram_target,
    sent_item_ids_for_target,
    telegram_excluded_item_ids,
)
from .telegram_visual_integration import (
    blocked_visual_delivery_result,
    blocked_visual_telegram_result,
    build_telegram_image_payload,
    default_image_provider,
    send_visual_image,
    visual_result_after_poll,
    visual_result_from_poll_delivery,
)
from .visual_cache import DEFAULT_ASSET_ROOT
from .visual_delivery import resolve_visual_delivery
from .visual_provider import ImageGenerationProvider


def run_telegram_delivery(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
    adapter: TelegramAdapter | None = None,
    image_provider: ImageGenerationProvider | None = None,
    asset_root: Path = DEFAULT_ASSET_ROOT,
) -> TelegramDeliveryResult:
    delivery, item = prepare_telegram_delivery(db_path, request)
    return send_loaded_telegram_delivery(db_path, delivery, item, request, adapter, image_provider, asset_root)


def prepare_telegram_delivery(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_delivery_mode(request.mode)
    selection = select_next_item(db_path, selection_request_from_telegram(db_path, request))
    delivery = selection["delivery"]
    delivery_id = str(delivery["delivery_id"])
    item = load_delivery_item(db_path, delivery_id, request.consumer_id)
    return delivery, item


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
    try:
        payload = build_telegram_poll_payload(request.chat_id, item, visual_resolution)
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
    visual_result = visual_result_from_poll_delivery(request.mode, visual_resolution, result)
    visual_result = visual_result_after_poll(visual_result, result)
    record_visual_result(db_path, delivery_id, request.consumer_id, visual_resolution, visual_result)
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
