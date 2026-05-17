"""Contracts for Visual Quiz Delivery settings and access decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VisualDeliveryMode(StrEnum):
    TEXT_ONLY = "text_only"
    IMAGE_STANDARD = "image_standard"
    IMAGE_BRANDED = "image_branded"


class VisualFallbackPolicy(StrEnum):
    TEXT_ONLY = "text_only"
    CACHE_ONLY = "cache_only"
    BLOCK_VISUAL_DELIVERY = "block_visual_delivery"


@dataclass(frozen=True)
class VisualSettings:
    consumer_id: str
    delivery_mode: VisualDeliveryMode
    visual_style: str
    branding_preset: str
    fallback_policy: VisualFallbackPolicy
    daily_visual_delivery_limit: int
    daily_generation_limit: int
    monthly_generation_limit: int
    is_active: bool

    @classmethod
    def text_only(cls, consumer_id: str) -> "VisualSettings":
        return cls(
            consumer_id=consumer_id,
            delivery_mode=VisualDeliveryMode.TEXT_ONLY,
            visual_style="standard_illustration",
            branding_preset="none",
            fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
            daily_visual_delivery_limit=0,
            daily_generation_limit=0,
            monthly_generation_limit=0,
            is_active=False,
        )


@dataclass(frozen=True)
class VisualAccessDecision:
    is_allowed: bool
    requested_mode: VisualDeliveryMode
    resolved_mode: VisualDeliveryMode
    reason_code: str
    feature: str | None = None


@dataclass(frozen=True)
class VisualQuotaDecision:
    is_allowed: bool
    feature: str
    used_count: int
    quota_limit: int
    period_key: str
    reason_code: str
