"""Typed protected beta channel configuration loader."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTECTED_BETA_CONFIG_PATH = ROOT / "data" / "config" / "protected_beta_channels.json"


@dataclass(frozen=True)
class ProtectedBetaScheduleSlot:
    local_time: str
    cefr_level: str
    theme_id: str
    quiz_count: int
    slot_id: str | None = None

    def stable_slot_id(self, consumer_id: str) -> str:
        if self.slot_id:
            return self.slot_id
        normalized_time = self.local_time.replace(":", "_")
        return f"{consumer_id}:{self.theme_id}:{normalized_time}"


@dataclass(frozen=True)
class ProtectedBetaScheduleBatch:
    local_time: str
    slots: tuple[ProtectedBetaScheduleSlot, ...]


@dataclass(frozen=True)
class ProtectedBetaVisualConfig:
    delivery_mode: VisualDeliveryMode
    visual_style: str = "standard_illustration"
    branding_preset: str = "none"
    fallback_policy: VisualFallbackPolicy = VisualFallbackPolicy.BLOCK_VISUAL_DELIVERY
    daily_visual_delivery_limit: int = 5
    daily_generation_limit: int = 5
    monthly_generation_limit: int = 70

    def to_settings(self, consumer_id: str) -> VisualSettings:
        return VisualSettings(
            consumer_id=consumer_id,
            delivery_mode=self.delivery_mode,
            visual_style=self.visual_style,
            branding_preset=self.branding_preset,
            fallback_policy=self.fallback_policy,
            daily_visual_delivery_limit=self.daily_visual_delivery_limit,
            daily_generation_limit=self.daily_generation_limit,
            monthly_generation_limit=self.monthly_generation_limit,
            is_active=True,
        )


@dataclass(frozen=True)
class ProtectedBetaTelegramChannel:
    consumer_id: str
    chat_id: str
    display_name: str
    timezone: str
    daily_quota_limit: int
    schedule_batches: tuple[ProtectedBetaScheduleBatch, ...]
    visual_config: ProtectedBetaVisualConfig | None = None
    credential_env: str | None = None

    @property
    def schedule_slots(self) -> tuple[ProtectedBetaScheduleSlot, ...]:
        return tuple(slot for batch in self.schedule_batches for slot in batch.slots)

    def allowed_cefr_levels(self) -> list[str]:
        return sorted({slot.cefr_level for slot in self.schedule_slots})

    def allowed_theme_ids(self) -> list[str]:
        return sorted({slot.theme_id for slot in self.schedule_slots})


def load_protected_beta_channels(
    path: Path = DEFAULT_PROTECTED_BETA_CONFIG_PATH,
) -> tuple[ProtectedBetaTelegramChannel, ...]:
    raw_config = json.loads(path.read_text(encoding="utf-8"))
    return parse_protected_beta_channels(raw_config)


def parse_protected_beta_channels(raw_config: object) -> tuple[ProtectedBetaTelegramChannel, ...]:
    config = require_mapping(raw_config, "protected beta config")
    raw_channels = require_sequence(config.get("channels"), "channels")
    if not raw_channels:
        raise ValueError("protected beta config must define at least one channel")
    channels = tuple(parse_channel(raw, f"channels[{index}]") for index, raw in enumerate(raw_channels))
    ensure_unique_consumer_ids(channels)
    return channels


def protected_beta_channel_by_id(
    channels: tuple[ProtectedBetaTelegramChannel, ...],
    consumer_id: str,
) -> ProtectedBetaTelegramChannel:
    for channel in channels:
        if channel.consumer_id == consumer_id:
            return channel
    raise ValueError(f"protected beta channel missing from config: {consumer_id}")


def parse_channel(raw_channel: object, context: str) -> ProtectedBetaTelegramChannel:
    channel = require_mapping(raw_channel, context)
    timezone = require_timezone(require_str(channel, "timezone", context), context)
    return ProtectedBetaTelegramChannel(
        consumer_id=require_str(channel, "consumer_id", context),
        chat_id=require_str(channel, "chat_id", context),
        display_name=require_str(channel, "display_name", context),
        timezone=timezone,
        daily_quota_limit=require_int(channel, "daily_quota_limit", context, minimum=1),
        schedule_batches=parse_batches(channel.get("schedule_batches"), context),
        visual_config=parse_visual_config(channel.get("visual_config"), context),
        credential_env=optional_str(channel, "credential_env", context),
    )


def parse_batches(raw_batches: object, context: str) -> tuple[ProtectedBetaScheduleBatch, ...]:
    batches = require_sequence(raw_batches, f"{context}.schedule_batches")
    if not batches:
        raise ValueError(f"{context}.schedule_batches must not be empty")
    return tuple(parse_batch(raw, f"{context}.schedule_batches[{index}]") for index, raw in enumerate(batches))


def parse_batch(raw_batch: object, context: str) -> ProtectedBetaScheduleBatch:
    batch = require_mapping(raw_batch, context)
    local_time = require_time(require_str(batch, "local_time", context), f"{context}.local_time")
    slots = require_sequence(batch.get("slots"), f"{context}.slots")
    if not slots:
        raise ValueError(f"{context}.slots must not be empty")
    return ProtectedBetaScheduleBatch(
        local_time=local_time,
        slots=tuple(parse_slot(raw, f"{context}.slots[{index}]") for index, raw in enumerate(slots)),
    )


def parse_slot(raw_slot: object, context: str) -> ProtectedBetaScheduleSlot:
    slot = require_mapping(raw_slot, context)
    return ProtectedBetaScheduleSlot(
        local_time=require_time(require_str(slot, "local_time", context), f"{context}.local_time"),
        cefr_level=require_str(slot, "cefr_level", context),
        theme_id=require_str(slot, "theme_id", context),
        quiz_count=require_int(slot, "quiz_count", context, minimum=1),
        slot_id=optional_str(slot, "slot_id", context),
    )


def parse_visual_config(raw_visual: object, context: str) -> ProtectedBetaVisualConfig | None:
    if raw_visual is None:
        return None
    visual = require_mapping(raw_visual, f"{context}.visual_config")
    return ProtectedBetaVisualConfig(
        delivery_mode=visual_delivery_mode(require_str(visual, "delivery_mode", context)),
        visual_style=optional_str(visual, "visual_style", context) or "standard_illustration",
        branding_preset=optional_str(visual, "branding_preset", context) or "none",
        fallback_policy=visual_fallback_policy(
            optional_str(visual, "fallback_policy", context) or "block_visual_delivery"
        ),
        daily_visual_delivery_limit=require_int(
            visual,
            "daily_visual_delivery_limit",
            context,
            minimum=0,
            default=5,
        ),
        daily_generation_limit=require_int(
            visual,
            "daily_generation_limit",
            context,
            minimum=0,
            default=5,
        ),
        monthly_generation_limit=require_int(
            visual,
            "monthly_generation_limit",
            context,
            minimum=0,
            default=70,
        ),
    )


def ensure_unique_consumer_ids(channels: tuple[ProtectedBetaTelegramChannel, ...]) -> None:
    seen: set[str] = set()
    for channel in channels:
        if channel.consumer_id in seen:
            raise ValueError(f"duplicate protected beta channel consumer_id: {channel.consumer_id}")
        seen.add(channel.consumer_id)


def require_mapping(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be an object")
    return value


def require_sequence(value: object, context: str) -> Sequence[object]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{context} must be a list")
    return value


def require_str(raw: Mapping[str, Any], key: str, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def optional_str(raw: Mapping[str, Any], key: str, context: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string when set")
    return value.strip()


def require_int(
    raw: Mapping[str, Any],
    key: str,
    context: str,
    minimum: int,
    default: int | None = None,
) -> int:
    value = raw.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context}.{key} must be an integer")
    if value < minimum:
        raise ValueError(f"{context}.{key} must be at least {minimum}")
    return value


def require_time(value: str, context: str) -> str:
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() and len(part) == 2 for part in parts):
        raise ValueError(f"{context} must use HH:MM")
    hour, minute = (int(part) for part in parts)
    if hour > 23 or minute > 59:
        raise ValueError(f"{context} must use HH:MM")
    return value


def require_timezone(value: str, context: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"{context}.timezone is not a valid IANA timezone") from error
    return value


def visual_delivery_mode(value: str) -> VisualDeliveryMode:
    try:
        return VisualDeliveryMode(value)
    except ValueError as error:
        raise ValueError(f"unknown visual delivery mode: {value}") from error


def visual_fallback_policy(value: str) -> VisualFallbackPolicy:
    try:
        return VisualFallbackPolicy(value)
    except ValueError as error:
        raise ValueError(f"unknown visual fallback policy: {value}") from error
