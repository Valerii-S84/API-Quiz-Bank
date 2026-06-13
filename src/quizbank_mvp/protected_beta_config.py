"""Typed protected beta channel configuration loader."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .database_runtime import DEFAULT_CONTENT_BANK_ID, DEFAULT_LANGUAGE_CODE
from .selection_models import ContentScope
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
    language_code: str | None = None
    content_bank_slug: str | None = None
    bank_version_id: str | None = None

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
    default_language_code: str = DEFAULT_LANGUAGE_CODE
    default_content_bank_slug: str = DEFAULT_CONTENT_BANK_ID
    default_bank_version_id: str | None = None
    allowed_language_codes: tuple[str, ...] = (DEFAULT_LANGUAGE_CODE,)
    allowed_content_bank_slugs: tuple[str, ...] = (DEFAULT_CONTENT_BANK_ID,)
    allowed_bank_version_ids: tuple[str, ...] = ()
    visual_config: ProtectedBetaVisualConfig | None = None
    credential_env: str | None = None

    @property
    def schedule_slots(self) -> tuple[ProtectedBetaScheduleSlot, ...]:
        return tuple(slot for batch in self.schedule_batches for slot in batch.slots)

    def allowed_cefr_levels(self) -> list[str]:
        return sorted({slot.cefr_level for slot in self.schedule_slots})

    def allowed_theme_ids(self) -> list[str]:
        return sorted({slot.theme_id for slot in self.schedule_slots})

    def content_scope_for_slot(self, slot: ProtectedBetaScheduleSlot) -> ContentScope:
        return ContentScope(
            language_code=slot.language_code or self.default_language_code,
            content_bank_id=slot.content_bank_slug or self.default_content_bank_slug,
            bank_version_id=slot.bank_version_id or self.default_bank_version_id,
        )

    def seed_content_scope(self) -> dict[str, object]:
        return {
            "default_language_code": self.default_language_code,
            "default_content_bank_id": self.default_content_bank_slug,
            "default_bank_version_id": self.default_bank_version_id or "",
            "allowed_language_codes": list(self.allowed_language_codes),
            "allowed_content_bank_ids": list(self.allowed_content_bank_slugs),
            "allowed_bank_version_ids": list(self.allowed_bank_version_ids),
        }


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
    default_language = optional_str(channel, "default_language_code", context) or DEFAULT_LANGUAGE_CODE
    default_bank = optional_str(channel, "default_content_bank_slug", context) or DEFAULT_CONTENT_BANK_ID
    parsed_channel = ProtectedBetaTelegramChannel(
        consumer_id=require_str(channel, "consumer_id", context),
        chat_id=require_str(channel, "chat_id", context),
        display_name=require_str(channel, "display_name", context),
        timezone=timezone,
        daily_quota_limit=require_int(channel, "daily_quota_limit", context, minimum=1),
        schedule_batches=parse_batches(channel.get("schedule_batches"), context),
        default_language_code=normalized_language(default_language, f"{context}.default_language_code"),
        default_content_bank_slug=default_bank,
        default_bank_version_id=optional_str(channel, "default_bank_version_id", context),
        allowed_language_codes=parse_string_list(
            channel,
            "allowed_language_codes",
            context,
            (normalized_language(default_language, f"{context}.default_language_code"),),
        ),
        allowed_content_bank_slugs=parse_string_list(
            channel,
            "allowed_content_bank_slugs",
            context,
            (default_bank,),
        ),
        allowed_bank_version_ids=parse_string_list(
            channel,
            "allowed_bank_version_ids",
            context,
            (),
            allow_empty=True,
        ),
        visual_config=parse_visual_config(channel.get("visual_config"), context),
        credential_env=optional_str(channel, "credential_env", context),
    )
    ensure_channel_content_scope_allowed(parsed_channel, context)
    return parsed_channel


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
        language_code=optional_language(slot, "language_code", context),
        content_bank_slug=optional_str(slot, "content_bank_slug", context),
        bank_version_id=optional_str(slot, "bank_version_id", context),
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


def ensure_channel_content_scope_allowed(
    channel: ProtectedBetaTelegramChannel,
    context: str,
) -> None:
    ensure_allowed_value(
        channel.default_language_code,
        channel.allowed_language_codes,
        f"{context}.default_language_code",
        "allowed_language_codes",
    )
    ensure_allowed_value(
        channel.default_content_bank_slug,
        channel.allowed_content_bank_slugs,
        f"{context}.default_content_bank_slug",
        "allowed_content_bank_slugs",
    )
    ensure_optional_allowed_value(
        channel.default_bank_version_id,
        channel.allowed_bank_version_ids,
        f"{context}.default_bank_version_id",
        "allowed_bank_version_ids",
    )
    for index, slot in enumerate(channel.schedule_slots):
        slot_context = f"{context}.schedule_slots[{index}]"
        ensure_optional_allowed_value(
            slot.language_code,
            channel.allowed_language_codes,
            f"{slot_context}.language_code",
            "allowed_language_codes",
        )
        ensure_optional_allowed_value(
            slot.content_bank_slug,
            channel.allowed_content_bank_slugs,
            f"{slot_context}.content_bank_slug",
            "allowed_content_bank_slugs",
        )
        ensure_optional_allowed_value(
            slot.bank_version_id,
            channel.allowed_bank_version_ids,
            f"{slot_context}.bank_version_id",
            "allowed_bank_version_ids",
        )


def ensure_allowed_value(value: str, allowed: tuple[str, ...], context: str, allowed_name: str) -> None:
    if value not in allowed:
        raise ValueError(f"{context} must be listed in {allowed_name}")


def ensure_optional_allowed_value(
    value: str | None,
    allowed: tuple[str, ...],
    context: str,
    allowed_name: str,
) -> None:
    if value is None or not allowed:
        return
    ensure_allowed_value(value, allowed, context, allowed_name)


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


def optional_language(raw: Mapping[str, Any], key: str, context: str) -> str | None:
    value = optional_str(raw, key, context)
    if value is None:
        return None
    return normalized_language(value, f"{context}.{key}")


def parse_string_list(
    raw: Mapping[str, Any],
    key: str,
    context: str,
    default: tuple[str, ...],
    allow_empty: bool = False,
) -> tuple[str, ...]:
    value = raw.get(key)
    if value is None:
        return default
    values = require_sequence(value, f"{context}.{key}")
    if not values and not allow_empty:
        raise ValueError(f"{context}.{key} must not be empty")
    parsed = tuple(parse_list_string(item, key, context, index) for index, item in enumerate(values))
    if not parsed and not allow_empty:
        raise ValueError(f"{context}.{key} must not be empty")
    return parsed


def parse_list_string(value: object, key: str, context: str, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key}[{index}] must be a non-empty string")
    parsed = value.strip()
    if key == "allowed_language_codes":
        return normalized_language(parsed, f"{context}.{key}[{index}]")
    return parsed


def normalized_language(value: str, context: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"{context} must be a non-empty string")
    return normalized


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
