"""Safe recovery helpers for protected beta scheduled Telegram slots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .database_connection import connect, row_to_dict
from .protected_beta import (
    DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
    PROTECTED_BETA_TELEGRAM_CHANNELS,
    ProtectedBetaDeliveryOptions,
    ProtectedBetaScheduleSlot,
    ProtectedBetaTelegramChannel,
    run_scheduled_protected_beta_slot,
)
from .protected_beta_slot_runs import attach_slot_run_delivery, scheduled_slot_id
from .telegram_models import TelegramAdapter, TelegramDeliveryResult


@dataclass(frozen=True)
class RecoveryAction:
    slot_id: str
    theme_id: str
    action: str
    delivery_id: str
    status: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "slot_id": self.slot_id,
            "theme_id": self.theme_id,
            "action": self.action,
            "delivery_id": self.delivery_id,
            "status": self.status,
            "detail": self.detail,
        }


def recover_slots(
    db_path: Path | None,
    delivery_date: str,
    channel_id: str,
    slot_codes: tuple[str, ...],
    mode: str,
    dry_run: bool,
    no_duplicate_send: bool,
    resume_created_delivery: bool,
    adapter: TelegramAdapter | None = None,
    delivery_options: ProtectedBetaDeliveryOptions = DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
) -> list[RecoveryAction]:
    channel = channel_by_chat_id(channel_id)
    actions: list[RecoveryAction] = []
    for slot in slots_for_codes(channel, slot_codes):
        slot_id = scheduled_slot_id(channel, slot, delivery_options)
        actions.append(
            recover_slot(
                db_path,
                channel,
                slot,
                slot_id,
                delivery_date,
                mode,
                dry_run,
                no_duplicate_send,
                resume_created_delivery,
                adapter,
                delivery_options,
            )
        )
    return actions


def recover_slot(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    slot_id: str,
    delivery_date: str,
    mode: str,
    dry_run: bool,
    no_duplicate_send: bool,
    resume_created_delivery: bool,
    adapter: TelegramAdapter | None,
    delivery_options: ProtectedBetaDeliveryOptions,
) -> RecoveryAction:
    slot_run = load_slot_run(db_path, channel, delivery_date, slot_id)
    if slot_run and no_duplicate_send and slot_run["delivery_id"]:
        if delivery_has_sent_result(db_path, str(slot_run["delivery_id"]), channel.consumer_id):
            return already_sent_action(slot, slot_id, str(slot_run["delivery_id"]))
    if slot_run is None:
        return create_or_run_missing_slot(
            db_path, channel, slot, slot_id, delivery_date, mode, dry_run, adapter, delivery_options
        )
    if not slot_run["delivery_id"] and resume_created_delivery:
        orphan_delivery_id = find_resume_delivery(db_path, channel, slot, delivery_date)
        if orphan_delivery_id:
            return link_or_run_resume_delivery(
                db_path,
                channel,
                slot,
                slot_run,
                slot_id,
                delivery_date,
                orphan_delivery_id,
                mode,
                dry_run,
                adapter,
                delivery_options,
            )
    if dry_run:
        return RecoveryAction(
            slot_id,
            slot.theme_id,
            "would_retry_slot",
            str(slot_run["delivery_id"] or ""),
            str(slot_run["status"]),
        )
    result = run_scheduled_protected_beta_slot(
        db_path, channel, slot, mode, adapter, delivery_date, delivery_options
    )
    return action_from_result(slot, slot_id, "retried_slot", result)


def create_or_run_missing_slot(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    slot_id: str,
    delivery_date: str,
    mode: str,
    dry_run: bool,
    adapter: TelegramAdapter | None,
    delivery_options: ProtectedBetaDeliveryOptions,
) -> RecoveryAction:
    if dry_run:
        return RecoveryAction(slot_id, slot.theme_id, "would_create_missing_slot", "", "missing")
    result = run_scheduled_protected_beta_slot(
        db_path, channel, slot, mode, adapter, delivery_date, delivery_options
    )
    return action_from_result(slot, slot_id, "created_missing_slot", result)


def link_or_run_resume_delivery(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    slot_run: dict[str, object],
    slot_id: str,
    delivery_date: str,
    orphan_delivery_id: str,
    mode: str,
    dry_run: bool,
    adapter: TelegramAdapter | None,
    delivery_options: ProtectedBetaDeliveryOptions,
) -> RecoveryAction:
    if dry_run:
        return RecoveryAction(
            slot_id,
            slot.theme_id,
            "would_link_created_delivery",
            orphan_delivery_id,
            str(slot_run["status"]),
        )
    attach_slot_run_delivery(db_path, str(slot_run["slot_run_id"]), orphan_delivery_id)
    result = run_scheduled_protected_beta_slot(
        db_path, channel, slot, mode, adapter, delivery_date, delivery_options
    )
    return action_from_result(slot, slot_id, "resumed_created_delivery", result)


def action_from_result(
    slot: ProtectedBetaScheduleSlot,
    slot_id: str,
    action: str,
    result: TelegramDeliveryResult,
) -> RecoveryAction:
    return RecoveryAction(
        slot_id,
        slot.theme_id,
        action,
        result.delivery_id,
        result.status,
        result.failure_reason or "",
    )


def already_sent_action(slot: ProtectedBetaScheduleSlot, slot_id: str, delivery_id: str) -> RecoveryAction:
    return RecoveryAction(slot_id, slot.theme_id, "already_sent_noop", delivery_id, "sent")


def channel_by_chat_id(channel_id: str) -> ProtectedBetaTelegramChannel:
    for channel in PROTECTED_BETA_TELEGRAM_CHANNELS:
        if channel.chat_id == channel_id:
            return channel
    raise ValueError("protected beta channel_id is not configured")


def slots_for_codes(
    channel: ProtectedBetaTelegramChannel,
    slot_codes: tuple[str, ...],
) -> tuple[ProtectedBetaScheduleSlot, ...]:
    requested = set(slot_codes)
    slots = tuple(slot for slot in channel.schedule_slots if slot.theme_id in requested)
    missing = requested - {slot.theme_id for slot in slots}
    if missing:
        raise ValueError(f"slot-code is not configured: {','.join(sorted(missing))}")
    return slots


def load_slot_run(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    delivery_date: str,
    slot_id: str,
) -> dict[str, object] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM scheduled_delivery_slots
            WHERE consumer_id = ? AND channel_id = ?
              AND delivery_date = ? AND slot_id = ?
            """,
            (channel.consumer_id, channel.chat_id, delivery_date, slot_id),
        ).fetchone()
    return None if row is None else row_to_dict(row)


def find_resume_delivery(
    db_path: Path | None,
    channel: ProtectedBetaTelegramChannel,
    slot: ProtectedBetaScheduleSlot,
    delivery_date: str,
) -> str | None:
    start, end = utc_day_bounds(delivery_date)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT d.delivery_id
            FROM deliveries d
            JOIN quiz_items q ON q.item_id = d.quiz_item_id
            LEFT JOIN scheduled_delivery_slots s ON s.delivery_id = d.delivery_id
            LEFT JOIN telegram_delivery_results t
              ON t.delivery_id = d.delivery_id AND t.status = 'sent'
            WHERE d.consumer_id = ?
              AND q.theme_id = ?
              AND q.sublevel = ?
              AND d.selected_at >= ?
              AND d.selected_at < ?
              AND d.delivery_status IN ('created', 'failed')
              AND s.delivery_id IS NULL
              AND t.delivery_id IS NULL
            ORDER BY d.selected_at ASC
            LIMIT 1
            """,
            (channel.consumer_id, slot.theme_id, slot.cefr_level, start, end),
        ).fetchone()
    if row is None:
        return None
    return str(row["delivery_id"])


def delivery_has_sent_result(db_path: Path | None, delivery_id: str, consumer_id: str) -> bool:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM telegram_delivery_results
            WHERE delivery_id = ? AND consumer_id = ? AND status = 'sent'
            """,
            (delivery_id, consumer_id),
        ).fetchone()
    return row is not None


def utc_day_bounds(delivery_date: str) -> tuple[str, str]:
    start_date = date.fromisoformat(delivery_date)
    end_date = start_date + timedelta(days=1)
    return f"{start_date.isoformat()}T00:00:00Z", f"{end_date.isoformat()}T00:00:00Z"
