"""Visual asset integration helpers for Telegram delivery."""

from __future__ import annotations

from typing import Any

from .telegram_bot_api import TelegramDeliveryError
from .telegram_models import (
    TelegramDeliveryRequest,
    TelegramDeliveryResult,
    VisualTelegramResult,
)
from .telegram_result_repository import redact_telegram_target
from .visual_delivery import VisualDeliveryResolution
from .visual_models import VisualDeliveryMode
from .visual_provider import FakeImageProvider, ImageGenerationProvider
from .visual_provider_openai import OpenAIEnvironmentImageProvider


def default_image_provider(
    mode: str,
    image_provider: ImageGenerationProvider | None,
) -> ImageGenerationProvider:
    if image_provider is not None:
        return image_provider
    if mode == "real":
        return OpenAIEnvironmentImageProvider()
    return FakeImageProvider()


def visual_result_from_poll_delivery(
    mode: str,
    resolution: VisualDeliveryResolution,
    poll_result: TelegramDeliveryResult,
) -> VisualTelegramResult | None:
    if resolution.requested_mode == VisualDeliveryMode.TEXT_ONLY:
        return None
    if not resolution.asset_id or not resolution.image_path:
        return VisualTelegramResult("fallback_used", True, resolution.fallback_reason)
    if mode == "dry_run":
        return VisualTelegramResult("skipped", False, "dry_run_no_bot_api_call")
    return VisualTelegramResult("sent", False, telegram_image_message_id=poll_result.telegram_message_id)


def send_visual_image(
    mode: str,
    payload: dict[str, Any],
    adapter: Any,
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
    if visual_result is None:
        return None
    if poll_result.status == "skipped":
        return VisualTelegramResult("skipped", False, poll_result.failure_reason)
    if poll_result.status != "failed":
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
