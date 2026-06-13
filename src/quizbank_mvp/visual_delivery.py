"""Orchestration for resolving visual delivery assets without network calls."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database_connection import connect, new_id, utc_now
from .image_quality_policy import ALLOWED_IMAGE_QUALITIES
from .visual_access import (
    check_visual_delivery_access,
    check_visual_generation_access,
    reserve_visual_delivery_quota,
    reserve_visual_generation_quota,
)
from .visual_cache import (
    DEFAULT_ASSET_ROOT,
    VisualAssetRecord,
    compute_visual_cache_key,
    find_approved_asset,
    mark_visual_asset_qa_status,
    store_visual_asset_candidate,
)
from .visual_image_transform import normalize_visual_image
from .visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings
from .visual_prompt_builder import VisualPrompt, build_visual_prompt
from .visual_provider import (
    ImageGenerationError,
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResult,
)
from .visual_qa import SUPPORTED_MIME_TYPES, VisualQADecision, evaluate_visual_qa
from .visual_settings import load_visual_settings


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VisualDeliveryResolution:
    state: str
    requested_mode: VisualDeliveryMode
    resolved_mode: VisualDeliveryMode
    fallback_used: bool
    fallback_reason: str | None = None
    asset_id: str | None = None
    image_path: str | None = None


def resolve_visual_delivery(
    db_path: Path | None,
    delivery: dict[str, Any],
    quiz_item: dict[str, Any],
    consumer_id: str,
    provider: ImageGenerationProvider,
    asset_root: Path = DEFAULT_ASSET_ROOT,
) -> VisualDeliveryResolution:
    settings = load_visual_settings(db_path, consumer_id)
    if not settings.is_active or settings.delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return text_only_resolution(settings)
    content_scope = delivery_content_scope(delivery, quiz_item)
    access = check_visual_delivery_access(db_path, settings, content_scope)
    if access.resolved_mode == VisualDeliveryMode.TEXT_ONLY or not access.is_allowed:
        return fallback_with_usage(db_path, delivery, settings, access.reason_code, access.feature)
    delivery_quota = reserve_visual_delivery_quota(db_path, settings, content_scope=content_scope)
    if not delivery_quota.is_allowed:
        return fallback_with_usage(db_path, delivery, settings, delivery_quota.reason_code, delivery_quota.feature)
    cache_key = compute_visual_cache_key(quiz_item, settings)
    cached_asset = find_approved_asset(db_path, cache_key, asset_root)
    if cached_asset is not None:
        record_usage(db_path, delivery, consumer_id, cached_asset, "cache_hit", delivery_quota.feature)
        return asset_resolution("cache_hit", settings, cached_asset)
    record_usage(db_path, delivery, consumer_id, None, "cache_miss", delivery_quota.feature)
    return generate_or_fallback(db_path, delivery, quiz_item, settings, provider, asset_root, cache_key)


def generate_or_fallback(
    db_path: Path | None,
    delivery: dict[str, Any],
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    provider: ImageGenerationProvider,
    asset_root: Path,
    cache_key: str,
) -> VisualDeliveryResolution:
    if settings.fallback_policy == VisualFallbackPolicy.CACHE_ONLY:
        return fallback_with_usage(db_path, delivery, settings, "CACHE_ONLY_MISS", "visual_delivery.cache_only")
    content_scope = delivery_content_scope(delivery, quiz_item)
    generation_access = check_visual_generation_access(db_path, settings, content_scope)
    if not generation_access.is_allowed or generation_access.resolved_mode == VisualDeliveryMode.TEXT_ONLY:
        return fallback_with_usage(db_path, delivery, settings, generation_access.reason_code, generation_access.feature)
    generation_quota = reserve_visual_generation_quota(db_path, settings, content_scope=content_scope)
    if not generation_quota.is_allowed:
        return fallback_with_usage(db_path, delivery, settings, generation_quota.reason_code, generation_quota.feature)
    prompt = build_visual_prompt(quiz_item, settings)
    record_usage(db_path, delivery, settings.consumer_id, None, "generation_requested", generation_quota.feature)
    try:
        result = provider.generate(provider_request(prompt, settings, quiz_item, cache_key))
    except ImageGenerationError:
        record_usage(db_path, delivery, settings.consumer_id, None, "generation_failed", generation_quota.feature)
        return fallback_with_usage(db_path, delivery, settings, "GENERATION_FAILED", generation_quota.feature)
    return qa_store_and_resolve(db_path, delivery, quiz_item, settings, asset_root, cache_key, prompt, result)


def qa_store_and_resolve(
    db_path: Path | None,
    delivery: dict[str, Any],
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    asset_root: Path,
    cache_key: str,
    prompt: VisualPrompt,
    result: ImageGenerationResult,
) -> VisualDeliveryResolution:
    feature = f"visual_generation.{settings.delivery_mode.value.removeprefix('image_')}"
    try:
        result = normalize_visual_image(result)
    except ImageGenerationError:
        record_usage(db_path, delivery, settings.consumer_id, None, "generation_failed", feature)
        return fallback_with_usage(db_path, delivery, settings, "IMAGE_POSTPROCESS_FAILED", feature)
    qa_decision = evaluate_visual_qa(prompt, result, quiz_item, settings)
    asset = store_after_basic_validation(db_path, quiz_item, settings, cache_key, result, asset_root, prompt)
    if asset is not None:
        insert_prompt_audit(db_path, asset, quiz_item, settings, prompt, result)
        mark_visual_asset_qa_status(db_path, asset.asset_id, qa_decision.qa_status)
    if qa_decision.qa_status == "approved" and asset is not None:
        record_usage(db_path, delivery, settings.consumer_id, asset, "generation_succeeded", feature)
        record_usage(db_path, delivery, settings.consumer_id, asset, "qa_approved", feature)
        return asset_resolution("generated_approved", settings, asset)
    record_usage(db_path, delivery, settings.consumer_id, asset, "qa_rejected", feature)
    return fallback_with_usage(db_path, delivery, settings, qa_decision.reason_code, feature, qa_decision)


def store_after_basic_validation(
    db_path: Path | None,
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    cache_key: str,
    result: ImageGenerationResult,
    asset_root: Path,
    prompt: VisualPrompt,
) -> VisualAssetRecord | None:
    if not result.image_bytes or result.mime_type not in SUPPORTED_MIME_TYPES:
        return None
    return store_visual_asset_candidate(
        db_path,
        quiz_item,
        settings,
        cache_key,
        result,
        asset_root,
        visual_metadata=visual_metadata(prompt),
    )


def visual_metadata(prompt: VisualPrompt) -> dict[str, str]:
    return {
        "visual_mode": prompt.visual_mode,
        "visual_target": prompt.visual_target,
        "visual_context_hint": prompt.visual_context_hint,
        "visual_prompt_policy_version": prompt.visual_prompt_policy_version,
    }


def delivery_content_scope(delivery: dict[str, Any], quiz_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "language_code": delivery.get("language_code") or quiz_item.get("language_code"),
        "content_bank_id": delivery.get("content_bank_id") or quiz_item.get("content_bank_id"),
        "bank_version_id": delivery.get("bank_version_id") or quiz_item.get("bank_version_id"),
    }


def provider_request(
    prompt: VisualPrompt,
    settings: VisualSettings,
    quiz_item: dict[str, Any],
    cache_key: str,
) -> ImageGenerationRequest:
    return ImageGenerationRequest(
        prompt=prompt.generated_prompt,
        negative_prompt=prompt.negative_prompt,
        quality=image_quality_for_generation(quiz_item),
        style_context=f"{settings.visual_style}:{settings.branding_preset}",
        idempotency_key=cache_key,
    )


def image_quality_for_generation(quiz_item: dict[str, Any]) -> str:
    quality = str(quiz_item.get("image_quality_recommended") or "").strip()
    if quality in ALLOWED_IMAGE_QUALITIES:
        return quality
    LOGGER.warning(
        "image_quality_recommended missing or invalid; falling back to low",
        extra={"quiz_item_id": str(quiz_item.get("item_id", ""))},
    )
    return "low"


def insert_prompt_audit(
    db_path: Path | None,
    asset: VisualAssetRecord,
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    prompt: VisualPrompt,
    result: ImageGenerationResult,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO visual_prompt_audit (
                prompt_id, asset_id, quiz_item_id, consumer_id, prompt_type,
                visual_mode, visual_target, visual_context_hint,
                generated_prompt, negative_prompt, prompt_policy_version,
                visual_prompt_policy_version,
                provider_name, provider_model, provider_response_id,
                provider_revised_prompt, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("vprompt"),
                asset.asset_id,
                quiz_item["item_id"],
                settings.consumer_id,
                prompt.visual_mode,
                prompt.visual_mode,
                prompt.visual_target,
                prompt.visual_context_hint,
                prompt.generated_prompt,
                prompt.negative_prompt,
                prompt.prompt_policy_version,
                prompt.visual_prompt_policy_version,
                result.provider_name,
                result.provider_model,
                result.provider_response_id,
                result.revised_prompt,
                utc_now(),
            ),
        )


def record_usage(
    db_path: Path | None,
    delivery: dict[str, Any],
    consumer_id: str,
    asset: VisualAssetRecord | None,
    event_type: str,
    feature: str,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO visual_usage_events (
                usage_event_id, consumer_id, delivery_id, asset_id, event_type,
                feature, quantity, estimated_cost_minor, provider_name, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
            """,
            (
                new_id("vusage"),
                consumer_id,
                delivery.get("delivery_id"),
                asset.asset_id if asset else None,
                event_type,
                feature,
                asset.provider_name if asset else "local",
                utc_now(),
            ),
        )


def text_only_resolution(settings: VisualSettings) -> VisualDeliveryResolution:
    return VisualDeliveryResolution(
        "text_only",
        settings.delivery_mode,
        VisualDeliveryMode.TEXT_ONLY,
        False,
    )


def fallback_resolution(
    settings: VisualSettings,
    reason_code: str,
    _qa_decision: VisualQADecision | None = None,
) -> VisualDeliveryResolution:
    if settings.fallback_policy == VisualFallbackPolicy.BLOCK_VISUAL_DELIVERY:
        return VisualDeliveryResolution("blocked", settings.delivery_mode, settings.delivery_mode, False, reason_code)
    return VisualDeliveryResolution("fallback_used", settings.delivery_mode, VisualDeliveryMode.TEXT_ONLY, True, reason_code)


def fallback_with_usage(
    db_path: Path | None,
    delivery: dict[str, Any],
    settings: VisualSettings,
    reason_code: str,
    feature: str | None,
    qa_decision: VisualQADecision | None = None,
) -> VisualDeliveryResolution:
    resolution = fallback_resolution(settings, reason_code, qa_decision)
    if resolution.fallback_used and feature:
        record_usage(db_path, delivery, settings.consumer_id, None, "fallback_used", feature)
    return resolution


def asset_resolution(
    state: str,
    settings: VisualSettings,
    asset: VisualAssetRecord,
) -> VisualDeliveryResolution:
    return VisualDeliveryResolution(
        state,
        settings.delivery_mode,
        settings.delivery_mode,
        False,
        asset_id=asset.asset_id,
        image_path=str(asset.image_path),
    )
