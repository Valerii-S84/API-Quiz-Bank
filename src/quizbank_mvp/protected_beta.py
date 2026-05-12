"""Protected beta Telegram channel enrollment and schedule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .admin_service import upsert_consumer_profile
from .database import seed_consumer, seed_entitlement
from .telegram_delivery import (
    TelegramAdapter,
    TelegramDeliveryRequest,
    TelegramDeliveryResult,
    run_telegram_delivery,
)


@dataclass(frozen=True)
class ProtectedBetaScheduleSlot:
    local_time: str
    cefr_level: str
    theme_id: str
    quiz_count: int


@dataclass(frozen=True)
class ProtectedBetaTelegramChannel:
    consumer_id: str
    chat_id: str
    display_name: str
    timezone: str
    daily_quota_limit: int
    schedule_slots: tuple[ProtectedBetaScheduleSlot, ...]

    def allowed_cefr_levels(self) -> list[str]:
        return sorted({slot.cefr_level for slot in self.schedule_slots})

    def allowed_theme_ids(self) -> list[str]:
        return sorted({slot.theme_id for slot in self.schedule_slots})


DEUTSCH_IST_EINFACH_CHANNEL = ProtectedBetaTelegramChannel(
    consumer_id="telegram_channel_deutsch_ist_einfach_quiz",
    chat_id="-1003475144955",
    display_name="🇩🇪 Deutsch ist einfach! – Quiz",
    timezone="Europe/Berlin",
    daily_quota_limit=9,
    schedule_slots=(
        ProtectedBetaScheduleSlot("08:22", "A2", "T11", 3),
        ProtectedBetaScheduleSlot("12:47", "B1", "T03", 3),
        ProtectedBetaScheduleSlot("20:15", "B2", "T10", 3),
    ),
)

PROTECTED_BETA_TELEGRAM_CHANNELS = (DEUTSCH_IST_EINFACH_CHANNEL,)


def seed_protected_beta_channels(
    db_path: Path | None,
    actor: str = "protected_beta_seed",
) -> list[str]:
    consumer_ids = []
    for channel in PROTECTED_BETA_TELEGRAM_CHANNELS:
        seed_protected_beta_channel(db_path, channel, actor)
        consumer_ids.append(channel.consumer_id)
    return consumer_ids


def seed_protected_beta_channel(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    actor: str,
) -> None:
    seed_consumer(
        db_path,
        channel.consumer_id,
        channel.daily_quota_limit,
        channel.allowed_cefr_levels(),
        channel.allowed_theme_ids(),
    )
    seed_entitlement(
        db_path,
        channel.consumer_id,
        channel.allowed_cefr_levels(),
        channel.allowed_theme_ids(),
        actor=actor,
        reason=f"Protected beta Telegram channel access: {channel.display_name}",
    )
    upsert_consumer_profile(
        db_path,
        {
            "consumer_id": channel.consumer_id,
            "display_name": channel.display_name,
            "consumer_kind": "telegram_channel",
        },
        actor,
    )


def due_slots(
    channel: ProtectedBetaTelegramChannel,
    now: datetime,
) -> tuple[ProtectedBetaScheduleSlot, ...]:
    local_now = now.astimezone(ZoneInfo(channel.timezone))
    current_time = local_now.strftime("%H:%M")
    return tuple(slot for slot in channel.schedule_slots if slot.local_time == current_time)


def run_protected_beta_slot(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    mode: str,
    adapter: TelegramAdapter | None = None,
) -> list[TelegramDeliveryResult]:
    results: list[TelegramDeliveryResult] = []
    excluded_item_ids: list[str] = []
    for _ in range(slot.quiz_count):
        result = run_telegram_delivery(
            db_path,
            TelegramDeliveryRequest(
                consumer_id=channel.consumer_id,
                chat_id=channel.chat_id,
                mode=mode,
                cefr_level=slot.cefr_level,
                theme_ids=(slot.theme_id,),
                excluded_item_ids=tuple(excluded_item_ids),
            ),
            adapter=adapter,
        )
        results.append(result)
        excluded_item_ids.append(result.quiz_item_id)
    return results
