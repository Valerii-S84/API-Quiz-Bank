"""Protected beta Telegram channel enrollment and schedule."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .admin_service import upsert_consumer_profile
from .database_connection import (
    connect,
    new_id,
    utc_now,
)
from .database_seed import (
    seed_api_credential,
    seed_consumer,
    seed_entitlement,
)
from .problems import QuizBankProblem
from .protected_beta_config import (
    DEFAULT_PROTECTED_BETA_CONFIG_PATH,
    ProtectedBetaScheduleBatch,
    ProtectedBetaScheduleSlot,
    ProtectedBetaTelegramChannel,
    ProtectedBetaVisualConfig,
    load_protected_beta_channels,
    protected_beta_channel_by_id,
)
from .protected_beta_slot_runs import (
    attach_slot_run_delivery,
    mark_scheduled_slot_failed_result,
    mark_slot_run_no_item,
    scheduled_slot_id,
    sent_telegram_result_for_slot_run,
    telegram_result_for_slot_run,
    update_slot_run_result,
    upsert_pending_slot_run,
)
from .telegram_delivery import (
    TelegramAdapter,
    TelegramDeliveryRequest,
    TelegramDeliveryResult,
    prepare_telegram_delivery,
    redact_telegram_target,
    run_telegram_delivery,
    send_existing_telegram_delivery,
    send_loaded_telegram_delivery,
)
from .visual_access import visual_delivery_feature, visual_generation_feature
from .visual_cache import DEFAULT_ASSET_ROOT
from .visual_models import VisualDeliveryMode
from .visual_provider import ImageGenerationProvider
from .visual_settings import save_visual_settings


@dataclass(frozen=True)
class ProtectedBetaDeliveryOptions:
    occurrence: int = 1
    image_provider: ImageGenerationProvider | None = None
    asset_root: Path = DEFAULT_ASSET_ROOT


PROTECTED_BETA_TELEGRAM_CHANNELS = load_protected_beta_channels()
DEUTSCH_IST_EINFACH_CHANNEL = protected_beta_channel_by_id(
    PROTECTED_BETA_TELEGRAM_CHANNELS,
    "telegram_channel_deutsch_ist_einfach_quiz",
)
CORE_DEUTSCH_IST_EINFACH_CHANNEL = protected_beta_channel_by_id(
    PROTECTED_BETA_TELEGRAM_CHANNELS,
    "core_deutsch_ist_einfach_channel",
)
DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS = ProtectedBetaDeliveryOptions()


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
        content_scope=channel.seed_content_scope(),
    )
    seed_entitlement(
        db_path,
        channel.consumer_id,
        channel.allowed_cefr_levels(),
        channel.allowed_theme_ids(),
        actor=actor,
        reason=f"Protected beta Telegram channel access: {channel.display_name}",
        content_scope=channel.seed_content_scope(),
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
    seed_channel_credential_from_env(db_path, channel)
    seed_channel_visual_access(db_path, channel, actor)


def seed_channel_visual_access(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    actor: str,
) -> None:
    if channel.visual_config is None:
        return
    save_visual_settings(db_path, channel.visual_config.to_settings(channel.consumer_id))
    for feature in visual_features(channel.visual_config.delivery_mode):
        seed_channel_feature_entitlement(db_path, channel, feature, actor)


def visual_features(delivery_mode: VisualDeliveryMode) -> tuple[str, ...]:
    if delivery_mode == VisualDeliveryMode.TEXT_ONLY:
        return ()
    return (
        visual_delivery_feature(delivery_mode),
        visual_generation_feature(delivery_mode),
    )


def seed_channel_feature_entitlement(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    feature: str,
    actor: str,
) -> str:
    entitlement_id = f"ent_{channel.consumer_id}_{feature.replace('.', '_')}"
    scope = channel.seed_content_scope()
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status,
                allowed_cefr_levels_json, allowed_theme_ids_json,
                allowed_language_codes_json, allowed_content_bank_ids_json,
                allowed_bank_version_ids_json, allowed_content_types_json,
                valid_until, created_at
            ) VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, NULL, ?)
            ON CONFLICT(entitlement_id) DO UPDATE SET
                status = excluded.status,
                allowed_cefr_levels_json = excluded.allowed_cefr_levels_json,
                allowed_theme_ids_json = excluded.allowed_theme_ids_json,
                allowed_language_codes_json = excluded.allowed_language_codes_json,
                allowed_content_bank_ids_json = excluded.allowed_content_bank_ids_json,
                allowed_bank_version_ids_json = excluded.allowed_bank_version_ids_json,
                allowed_content_types_json = excluded.allowed_content_types_json,
                valid_until = excluded.valid_until
            """,
            (
                entitlement_id,
                channel.consumer_id,
                feature,
                json.dumps(channel.allowed_cefr_levels()),
                json.dumps(channel.allowed_theme_ids()),
                json.dumps(scope["allowed_language_codes"]),
                json.dumps(scope["allowed_content_bank_ids"]),
                json.dumps(scope["allowed_bank_version_ids"]),
                json.dumps([]),
                utc_now(),
            ),
        )
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_id, actor, action, entity_type, entity_id, from_status,
                to_status, reason, created_at
            ) VALUES (?, ?, 'entitlement_grant', 'entitlement', ?, '', 'active', ?, ?)
            """,
            (
                new_id("audit"),
                actor,
                entitlement_id,
                f"Protected beta visual access: {channel.display_name}",
                utc_now(),
            ),
        )
    return entitlement_id


def seed_channel_credential_from_env(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
) -> bool:
    if not channel.credential_env:
        return False
    raw_api_key = os.environ.get(channel.credential_env, "").strip()
    if not raw_api_key:
        return False
    seed_api_credential(db_path, channel.consumer_id, raw_api_key)
    return True


def due_slots(
    channel: ProtectedBetaTelegramChannel,
    now: datetime,
) -> tuple[ProtectedBetaScheduleSlot, ...]:
    local_now = now.astimezone(ZoneInfo(channel.timezone))
    current_time = local_now.strftime("%H:%M")
    return tuple(slot for slot in channel.schedule_slots if slot.local_time == current_time)


def due_batches(
    channel: ProtectedBetaTelegramChannel,
    now: datetime,
) -> tuple[ProtectedBetaScheduleBatch, ...]:
    local_now = now.astimezone(ZoneInfo(channel.timezone))
    current_time = local_now.strftime("%H:%M")
    return tuple(batch for batch in channel.schedule_batches if batch.local_time == current_time)


def run_protected_beta_slot(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    mode: str,
    adapter: TelegramAdapter | None = None,
    delivery_options: ProtectedBetaDeliveryOptions = DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
) -> list[TelegramDeliveryResult]:
    results: list[TelegramDeliveryResult] = []
    excluded_item_ids: list[str] = []
    for _ in range(slot.quiz_count):
        content_scope = channel.content_scope_for_slot(slot)
        result = run_telegram_delivery(
            db_path,
            TelegramDeliveryRequest(
                consumer_id=channel.consumer_id,
                chat_id=channel.chat_id,
                mode=mode,
                cefr_level=slot.cefr_level,
                theme_ids=(slot.theme_id,),
                excluded_item_ids=tuple(excluded_item_ids),
                language_code=content_scope.language_code,
                content_bank_id=content_scope.content_bank_id,
                bank_version_id=content_scope.bank_version_id,
            ),
            adapter=adapter,
            image_provider=delivery_options.image_provider,
            asset_root=delivery_options.asset_root,
        )
        results.append(result)
        excluded_item_ids.append(result.quiz_item_id)
    return results


def run_protected_beta_batch(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    batch: ProtectedBetaScheduleBatch,
    mode: str,
    adapter: TelegramAdapter | None = None,
    now: datetime | None = None,
    delivery_options: ProtectedBetaDeliveryOptions = DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
) -> list[TelegramDeliveryResult]:
    delivery_date = delivery_date_for_channel(channel, now)
    results: list[TelegramDeliveryResult] = []
    for slot in batch.slots:
        for index in range(slot.quiz_count):
            slot_options = delivery_options_for_occurrence(delivery_options, index + 1)
            slot_id = scheduled_slot_id(channel, slot, slot_options)
            try:
                result = run_scheduled_protected_beta_slot(
                    db_path,
                    channel,
                    slot,
                    mode,
                    adapter,
                    delivery_date,
                    slot_options,
                )
            except Exception as error:
                result = mark_scheduled_slot_failed_result(
                    db_path,
                    channel,
                    slot,
                    mode,
                    delivery_date,
                    slot_id,
                    error,
                )
            results.append(result)
    return results


def run_scheduled_protected_beta_slot(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    mode: str,
    adapter: TelegramAdapter | None,
    delivery_date: str,
    delivery_options: ProtectedBetaDeliveryOptions = DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
) -> TelegramDeliveryResult:
    slot_id = scheduled_slot_id(channel, slot, delivery_options)
    slot_run = upsert_pending_slot_run(db_path, channel, slot, delivery_date, slot_id)
    request = telegram_request_for_slot_run(channel, slot, mode, slot_run)
    if mode == "real" and slot_run["status"] == "sent":
        return telegram_result_for_slot_run(db_path, slot_run, channel, mode)
    if mode == "real" and slot_run["delivery_id"]:
        return send_slot_run_existing_delivery(
            db_path, slot_run, channel, mode, request, adapter, delivery_options
        )
    try:
        delivery, item = prepare_telegram_delivery(db_path, request)
        attach_slot_run_delivery(db_path, str(slot_run["slot_run_id"]), str(delivery["delivery_id"]))
        result = send_loaded_telegram_delivery(
            db_path,
            delivery,
            item,
            request,
            adapter=adapter,
            image_provider=delivery_options.image_provider,
            asset_root=delivery_options.asset_root,
        )
    except QuizBankProblem as error:
        if error.reason_code != "SELECTION_NO_ELIGIBLE_ITEM":
            raise
        mark_slot_run_no_item(db_path, slot_run["slot_run_id"], str(error.reason_code))
        return TelegramDeliveryResult(
            delivery_id="",
            consumer_id=channel.consumer_id,
            quiz_item_id="",
            mode=mode,
            status="no_item",
            telegram_target_ref=redact_telegram_target(channel.chat_id),
            failure_reason=error.reason_code,
            language_code=request.language_code,
            content_bank_id=request.content_bank_id,
            bank_version_id=request.bank_version_id,
        )
    update_slot_run_result(db_path, slot_run["slot_run_id"], result)
    return result


def telegram_request_for_slot_run(
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    mode: str,
    slot_run: dict[str, object],
) -> TelegramDeliveryRequest:
    return TelegramDeliveryRequest(
        consumer_id=channel.consumer_id,
        chat_id=channel.chat_id,
        mode=mode,
        cefr_level=slot.cefr_level,
        theme_ids=(slot.theme_id,),
        language_code=str(slot_run["language_code"]),
        content_bank_id=str(slot_run["content_bank_id"]),
        bank_version_id=str(slot_run["bank_version_id"]),
    )


def send_slot_run_existing_delivery(
    db_path: Path | None,
    slot_run: dict[str, object],
    channel: ProtectedBetaTelegramChannel,
    mode: str,
    request: TelegramDeliveryRequest,
    adapter: TelegramAdapter | None,
    delivery_options: ProtectedBetaDeliveryOptions,
) -> TelegramDeliveryResult:
    sent_result = sent_telegram_result_for_slot_run(db_path, slot_run, channel, mode)
    if sent_result is not None:
        update_slot_run_result(db_path, str(slot_run["slot_run_id"]), sent_result)
        return sent_result
    result = send_existing_telegram_delivery(
        db_path,
        str(slot_run["delivery_id"]),
        request,
        adapter=adapter,
        image_provider=delivery_options.image_provider,
        asset_root=delivery_options.asset_root,
    )
    update_slot_run_result(db_path, str(slot_run["slot_run_id"]), result)
    return result


def delivery_options_for_occurrence(
    delivery_options: ProtectedBetaDeliveryOptions,
    occurrence: int,
) -> ProtectedBetaDeliveryOptions:
    return ProtectedBetaDeliveryOptions(
        occurrence=occurrence,
        image_provider=delivery_options.image_provider,
        asset_root=delivery_options.asset_root,
    )


def delivery_date_for_channel(
    channel: ProtectedBetaTelegramChannel,
    now: datetime | None,
) -> str:
    resolved_now = now or datetime.now(ZoneInfo(channel.timezone))
    return resolved_now.astimezone(ZoneInfo(channel.timezone)).date().isoformat()
