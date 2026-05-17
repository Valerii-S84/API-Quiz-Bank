"""Entitlement and quota checks for Visual Quiz Delivery."""

from __future__ import annotations

from pathlib import Path

from .database import connect, new_id, today_usage_date, utc_now
from .visual_models import (
    VisualAccessDecision,
    VisualDeliveryMode,
    VisualFallbackPolicy,
    VisualQuotaDecision,
    VisualSettings,
)


VISUAL_DELIVERY_FEATURES = {
    VisualDeliveryMode.IMAGE_STANDARD: "visual_delivery.standard",
    VisualDeliveryMode.IMAGE_BRANDED: "visual_delivery.branded",
}
VISUAL_GENERATION_FEATURES = {
    VisualDeliveryMode.IMAGE_STANDARD: "visual_generation.standard",
    VisualDeliveryMode.IMAGE_BRANDED: "visual_generation.branded",
}


def check_visual_delivery_access(
    db_path: Path | None,
    settings: VisualSettings,
) -> VisualAccessDecision:
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return allowed_text_only(settings, "TEXT_ONLY_VISUAL_MODE")
    feature = visual_delivery_feature(settings.delivery_mode)
    if has_active_entitlement(db_path, settings.consumer_id, feature):
        return VisualAccessDecision(
            True,
            settings.delivery_mode,
            settings.delivery_mode,
            "VISUAL_ACCESS_ALLOWED",
            feature,
        )
    return fallback_or_block(settings, "VISUAL_ENTITLEMENT_MISSING", feature)


def check_visual_generation_access(
    db_path: Path | None,
    settings: VisualSettings,
) -> VisualAccessDecision:
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return allowed_text_only(settings, "TEXT_ONLY_VISUAL_MODE")
    feature = visual_generation_feature(settings.delivery_mode)
    if has_active_entitlement(db_path, settings.consumer_id, feature):
        return VisualAccessDecision(
            True,
            settings.delivery_mode,
            settings.delivery_mode,
            "VISUAL_GENERATION_ALLOWED",
            feature,
        )
    return fallback_or_block(settings, "VISUAL_GENERATION_ENTITLEMENT_MISSING", feature)


def check_visual_delivery_quota(
    db_path: Path | None,
    settings: VisualSettings,
    usage_date: str | None = None,
) -> VisualQuotaDecision:
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return quota_allowed("visual_delivery.none", 0, 0, usage_date or today_usage_date())
    feature = visual_delivery_feature(settings.delivery_mode)
    return check_quota(
        db_path,
        settings.consumer_id,
        feature,
        usage_date or today_usage_date(),
        settings.daily_visual_delivery_limit,
    )


def check_visual_generation_quota(
    db_path: Path | None,
    settings: VisualSettings,
    usage_date: str | None = None,
) -> VisualQuotaDecision:
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return quota_allowed("visual_generation.none", 0, 0, usage_date or today_usage_date())
    day_key = usage_date or today_usage_date()
    feature = visual_generation_feature(settings.delivery_mode)
    daily = check_quota(db_path, settings.consumer_id, feature, day_key, settings.daily_generation_limit)
    if not daily.is_allowed:
        return daily
    month_key = day_key[:7]
    return check_quota(db_path, settings.consumer_id, feature, month_key, settings.monthly_generation_limit)


def reserve_visual_delivery_quota(
    db_path: Path | None,
    settings: VisualSettings,
    usage_date: str | None = None,
) -> VisualQuotaDecision:
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return quota_allowed("visual_delivery.none", 0, 0, usage_date or today_usage_date())
    day_key = usage_date or today_usage_date()
    feature = visual_delivery_feature(settings.delivery_mode)
    allowed = check_quota(db_path, settings.consumer_id, feature, day_key, settings.daily_visual_delivery_limit)
    if not allowed.is_allowed:
        return allowed
    return increment_quota_usage(db_path, settings.consumer_id, feature, day_key, settings.daily_visual_delivery_limit)


def reserve_visual_generation_quota(
    db_path: Path | None,
    settings: VisualSettings,
    usage_date: str | None = None,
) -> VisualQuotaDecision:
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return quota_allowed("visual_generation.none", 0, 0, usage_date or today_usage_date())
    day_key = usage_date or today_usage_date()
    month_key = day_key[:7]
    feature = visual_generation_feature(settings.delivery_mode)
    daily = check_quota(db_path, settings.consumer_id, feature, day_key, settings.daily_generation_limit)
    if not daily.is_allowed:
        return daily
    monthly = check_quota(db_path, settings.consumer_id, feature, month_key, settings.monthly_generation_limit)
    if not monthly.is_allowed:
        return monthly
    increment_quota_usage(db_path, settings.consumer_id, feature, day_key, settings.daily_generation_limit)
    return increment_quota_usage(db_path, settings.consumer_id, feature, month_key, settings.monthly_generation_limit)


def has_active_entitlement(db_path: Path | None, consumer_id: str, feature: str) -> bool:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT entitlement_id FROM entitlements
            WHERE consumer_id = ?
              AND feature = ?
              AND status = 'active'
              AND (valid_until IS NULL OR valid_until >= ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (consumer_id, feature, utc_now()),
        ).fetchone()
    return row is not None


def check_quota(
    db_path: Path | None,
    consumer_id: str,
    feature: str,
    period_key: str,
    quota_limit: int,
) -> VisualQuotaDecision:
    used_count = load_quota_used_count(db_path, consumer_id, feature, period_key)
    if used_count >= quota_limit:
        return VisualQuotaDecision(
            False,
            feature,
            used_count,
            quota_limit,
            period_key,
            "VISUAL_QUOTA_EXHAUSTED",
        )
    return quota_allowed(feature, used_count, quota_limit, period_key)


def load_quota_used_count(
    db_path: Path | None,
    consumer_id: str,
    feature: str,
    period_key: str,
) -> int:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT used_count FROM quota_usage
            WHERE consumer_id = ? AND feature = ? AND usage_date = ?
            """,
            (consumer_id, feature, period_key),
        ).fetchone()
    return 0 if row is None else int(row["used_count"])


def increment_quota_usage(
    db_path: Path | None,
    consumer_id: str,
    feature: str,
    period_key: str,
    quota_limit: int,
) -> VisualQuotaDecision:
    used_count = load_quota_used_count(db_path, consumer_id, feature, period_key)
    if used_count >= quota_limit:
        return VisualQuotaDecision(False, feature, used_count, quota_limit, period_key, "VISUAL_QUOTA_EXHAUSTED")
    next_used_count = used_count + 1
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO quota_usage (
                quota_usage_id, consumer_id, feature, usage_date, used_count,
                quota_limit, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(consumer_id, feature, usage_date) DO UPDATE SET
                used_count = excluded.used_count,
                quota_limit = excluded.quota_limit,
                updated_at = excluded.updated_at
            """,
            (
                new_id("quota"),
                consumer_id,
                feature,
                period_key,
                next_used_count,
                quota_limit,
                utc_now(),
            ),
        )
    return quota_allowed(feature, next_used_count, quota_limit, period_key)


def visual_delivery_feature(mode: VisualDeliveryMode) -> str:
    return VISUAL_DELIVERY_FEATURES[mode]


def visual_generation_feature(mode: VisualDeliveryMode) -> str:
    return VISUAL_GENERATION_FEATURES[mode]


def allowed_text_only(settings: VisualSettings, reason_code: str) -> VisualAccessDecision:
    return VisualAccessDecision(
        True,
        settings.delivery_mode,
        VisualDeliveryMode.TEXT_ONLY,
        reason_code,
        None,
    )


def fallback_or_block(
    settings: VisualSettings,
    reason_code: str,
    feature: str,
) -> VisualAccessDecision:
    if settings.fallback_policy == VisualFallbackPolicy.TEXT_ONLY:
        return VisualAccessDecision(
            True,
            settings.delivery_mode,
            VisualDeliveryMode.TEXT_ONLY,
            reason_code,
            feature,
        )
    return VisualAccessDecision(False, settings.delivery_mode, settings.delivery_mode, reason_code, feature)


def quota_allowed(feature: str, used_count: int, quota_limit: int, period_key: str) -> VisualQuotaDecision:
    return VisualQuotaDecision(True, feature, used_count, quota_limit, period_key, "VISUAL_QUOTA_ALLOWED")
