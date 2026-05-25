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
    row_to_dict,
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
from .telegram_delivery import (
    TelegramAdapter,
    TelegramDeliveryRequest,
    TelegramDeliveryResult,
    redact_telegram_target,
    run_telegram_delivery,
    send_existing_telegram_delivery,
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
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status,
                allowed_cefr_levels_json, allowed_theme_ids_json,
                valid_until, created_at
            ) VALUES (?, ?, ?, 'active', ?, ?, NULL, ?)
            ON CONFLICT(entitlement_id) DO UPDATE SET
                status = excluded.status,
                allowed_cefr_levels_json = excluded.allowed_cefr_levels_json,
                allowed_theme_ids_json = excluded.allowed_theme_ids_json,
                valid_until = excluded.valid_until
            """,
            (
                entitlement_id,
                channel.consumer_id,
                feature,
                json.dumps(channel.allowed_cefr_levels()),
                json.dumps(channel.allowed_theme_ids()),
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
            results.append(
                run_scheduled_protected_beta_slot(
                    db_path,
                    channel,
                    slot,
                    mode,
                    adapter,
                    delivery_date,
                    delivery_options_for_occurrence(delivery_options, index + 1),
                )
            )
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
    slot_id = slot.stable_slot_id(channel.consumer_id)
    if slot.quiz_count > 1:
        slot_id = f"{slot_id}:{delivery_options.occurrence}"
    request = TelegramDeliveryRequest(
        consumer_id=channel.consumer_id,
        chat_id=channel.chat_id,
        mode=mode,
        cefr_level=slot.cefr_level,
        theme_ids=(slot.theme_id,),
    )
    slot_run = upsert_pending_slot_run(db_path, channel, slot, delivery_date, slot_id)
    if mode == "real" and slot_run["status"] == "sent":
        return telegram_result_for_slot_run(db_path, slot_run, channel, mode)
    if mode == "real" and slot_run["delivery_id"]:
        result = send_existing_telegram_delivery(
            db_path,
            str(slot_run["delivery_id"]),
            request,
            adapter=adapter,
            image_provider=delivery_options.image_provider,
            asset_root=delivery_options.asset_root,
        )
        update_slot_run_result(db_path, slot_run["slot_run_id"], result)
        return result
    try:
        result = run_telegram_delivery(
            db_path,
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
        )
    update_slot_run_result(db_path, slot_run["slot_run_id"], result)
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


def upsert_pending_slot_run(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    delivery_date: str,
    slot_id: str,
) -> dict[str, object]:
    idempotency_key = scheduled_slot_idempotency_key(
        channel.consumer_id,
        channel.chat_id,
        delivery_date,
        slot_id,
        slot.cefr_level,
        slot.theme_id,
    )
    with connect(db_path) as connection:
        now = utc_now()
        slot_run_id = new_id("slotrun")
        connection.execute(
            """
            INSERT INTO scheduled_delivery_slots (
                slot_run_id, idempotency_key, consumer_id, channel_id,
                delivery_date, slot_id, cefr_level, theme_id, delivery_id,
                status, failure_reason, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 'pending', NULL, ?, ?)
            ON CONFLICT(idempotency_key) DO NOTHING
            """,
            (
                slot_run_id,
                idempotency_key,
                channel.consumer_id,
                channel.chat_id,
                delivery_date,
                slot_id,
                slot.cefr_level,
                slot.theme_id,
                now,
                now,
            ),
        )
        row = connection.execute(
            "SELECT * FROM scheduled_delivery_slots WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
    return row_to_dict(row)


def scheduled_slot_idempotency_key(
    consumer_id: str,
    channel_id: str,
    delivery_date: str,
    slot_id: str,
    cefr_level: str,
    theme_id: str,
) -> str:
    return "|".join((consumer_id, channel_id, delivery_date, slot_id, cefr_level, theme_id))


def update_slot_run_result(
    db_path: Path | None,
    slot_run_id: str,
    result: TelegramDeliveryResult,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE scheduled_delivery_slots
            SET delivery_id = ?, status = ?, failure_reason = ?, updated_at = ?
            WHERE slot_run_id = ?
            """,
            (
                result.delivery_id,
                result.status,
                result.failure_reason,
                utc_now(),
                slot_run_id,
            ),
        )


def mark_slot_run_no_item(
    db_path: Path | None,
    slot_run_id: str,
    failure_reason: str,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE scheduled_delivery_slots
            SET status = 'no_item', failure_reason = ?, updated_at = ?
            WHERE slot_run_id = ?
            """,
            (failure_reason, utc_now(), slot_run_id),
        )


def telegram_result_for_slot_run(
    db_path: Path | None,
    slot_run: dict[str, object],
    channel: ProtectedBetaTelegramChannel,
    mode: str,
) -> TelegramDeliveryResult:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT d.delivery_id, d.consumer_id, d.quiz_item_id,
                   t.status, t.telegram_target_ref, t.telegram_message_id,
                   t.telegram_poll_id, t.failure_reason
            FROM deliveries d
            LEFT JOIN telegram_delivery_results t ON t.delivery_id = d.delivery_id
            WHERE d.delivery_id = ? AND d.consumer_id = ?
            """,
            (slot_run["delivery_id"], channel.consumer_id),
        ).fetchone()
    if row is None:
        return TelegramDeliveryResult(
            delivery_id=str(slot_run["delivery_id"] or ""),
            consumer_id=channel.consumer_id,
            quiz_item_id="",
            mode=mode,
            status="sent",
            telegram_target_ref=redact_telegram_target(channel.chat_id),
            failure_reason="sent_slot_delivery_missing",
        )
    record = row_to_dict(row)
    return TelegramDeliveryResult(
        delivery_id=str(record["delivery_id"]),
        consumer_id=str(record["consumer_id"]),
        quiz_item_id=str(record["quiz_item_id"]),
        mode=mode,
        status=str(record["status"] or "sent"),
        telegram_target_ref=str(
            record["telegram_target_ref"] or redact_telegram_target(channel.chat_id)
        ),
        telegram_message_id=record["telegram_message_id"],
        telegram_poll_id=record["telegram_poll_id"],
        failure_reason=record["failure_reason"],
    )
