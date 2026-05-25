"""Shared Telegram delivery request and result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .telegram_bot_api import TelegramSendResult


class TelegramAdapter(Protocol):
    def send_quiz_poll(self, payload: dict[str, Any]) -> TelegramSendResult:
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
