"""Consumer-scoped Visual Quiz Delivery settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .database_connection import connect, row_to_dict
from .database_seed import upsert_consumer_visual_settings
from .visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings


def load_visual_settings(db_path: Path | None, consumer_id: str) -> VisualSettings:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM consumer_visual_settings WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
    if row is None:
        return VisualSettings.text_only(consumer_id)
    return visual_settings_from_mapping(row_to_dict(row))


def save_visual_settings(db_path: Path | None, settings: VisualSettings) -> None:
    upsert_consumer_visual_settings(
        db_path,
        settings.consumer_id,
        {
            "delivery_mode": settings.delivery_mode.value,
            "visual_style": settings.visual_style,
            "branding_preset": settings.branding_preset,
            "fallback_policy": settings.fallback_policy.value,
            "daily_visual_delivery_limit": settings.daily_visual_delivery_limit,
            "daily_generation_limit": settings.daily_generation_limit,
            "monthly_generation_limit": settings.monthly_generation_limit,
            "is_active": int(settings.is_active),
        },
    )


def visual_settings_from_mapping(row: dict[str, Any]) -> VisualSettings:
    return VisualSettings(
        consumer_id=str(row["consumer_id"]),
        delivery_mode=parse_delivery_mode(row["delivery_mode"]),
        visual_style=required_text(row["visual_style"], "visual_style"),
        branding_preset=required_text(row["branding_preset"], "branding_preset"),
        fallback_policy=parse_fallback_policy(row["fallback_policy"]),
        daily_visual_delivery_limit=non_negative_int(row["daily_visual_delivery_limit"]),
        daily_generation_limit=non_negative_int(row["daily_generation_limit"]),
        monthly_generation_limit=non_negative_int(row["monthly_generation_limit"]),
        is_active=bool(int(row["is_active"])),
    )


def parse_delivery_mode(value: object) -> VisualDeliveryMode:
    try:
        return VisualDeliveryMode(str(value))
    except ValueError as error:
        raise ValueError(f"invalid visual delivery mode: {value}") from error


def parse_fallback_policy(value: object) -> VisualFallbackPolicy:
    try:
        return VisualFallbackPolicy(str(value))
    except ValueError as error:
        raise ValueError(f"invalid visual fallback policy: {value}") from error


def required_text(value: object, field_name: str) -> str:
    text = str(value)
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


def non_negative_int(value: object) -> int:
    number = int(value)
    if number < 0:
        raise ValueError("visual limits must be non-negative")
    return number
