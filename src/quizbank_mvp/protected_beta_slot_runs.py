"""Scheduled protected beta slot run persistence helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .database_connection import connect, new_id, row_to_dict, utc_now
from .problems import QuizBankProblem
from .telegram_bot_api import TelegramDeliveryError
from .telegram_models import TelegramDeliveryResult
from .telegram_result_repository import redact_telegram_target
from .visual_cache import VisualAssetStorageError


def scheduled_slot_id(channel: Any, slot: Any, delivery_options: Any) -> str:
    slot_id = slot.stable_slot_id(channel.consumer_id)
    if slot.quiz_count > 1:
        return f"{slot_id}:{delivery_options.occurrence}"
    return slot_id


def upsert_pending_slot_run(
    db_path: Path | None,
    channel: Any,
    slot: Any,
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


def attach_slot_run_delivery(db_path: Path | None, slot_run_id: str, delivery_id: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE scheduled_delivery_slots
            SET delivery_id = ?, updated_at = ?
            WHERE slot_run_id = ?
              AND (delivery_id IS NULL OR delivery_id = ?)
            """,
            (delivery_id, utc_now(), slot_run_id, delivery_id),
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


def mark_slot_run_failed(
    db_path: Path | None,
    slot_run_id: str,
    failure_reason: str,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE scheduled_delivery_slots
            SET status = 'failed', failure_reason = ?, updated_at = ?
            WHERE slot_run_id = ?
            """,
            (failure_reason, utc_now(), slot_run_id),
        )


def mark_scheduled_slot_failed_result(
    db_path: Path | None,
    channel: Any,
    slot: Any,
    mode: str,
    delivery_date: str,
    slot_id: str,
    error: Exception,
) -> TelegramDeliveryResult:
    slot_run = upsert_pending_slot_run(db_path, channel, slot, delivery_date, slot_id)
    failure_reason = slot_failure_reason(error)
    mark_slot_run_failed(db_path, str(slot_run["slot_run_id"]), failure_reason)
    return TelegramDeliveryResult(
        delivery_id=str(slot_run["delivery_id"] or ""),
        consumer_id=channel.consumer_id,
        quiz_item_id="",
        mode=mode,
        status="failed",
        telegram_target_ref=redact_telegram_target(channel.chat_id),
        failure_reason=failure_reason,
    )


def slot_failure_reason(error: Exception) -> str:
    if isinstance(error, QuizBankProblem):
        return str(error.reason_code)
    if isinstance(error, VisualAssetStorageError):
        return str(error)
    if isinstance(error, TelegramDeliveryError):
        return f"TELEGRAM_DELIVERY_ERROR:{error}"
    return f"UNEXPECTED_SLOT_ERROR:{type(error).__name__}"


def sent_telegram_result_for_slot_run(
    db_path: Path | None,
    slot_run: dict[str, object],
    channel: Any,
    mode: str,
) -> TelegramDeliveryResult | None:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT d.delivery_id, d.consumer_id, d.quiz_item_id,
                   t.status, t.telegram_target_ref, t.telegram_message_id,
                   t.telegram_poll_id, t.failure_reason
            FROM deliveries d
            JOIN telegram_delivery_results t ON t.delivery_id = d.delivery_id
            WHERE d.delivery_id = ? AND d.consumer_id = ? AND t.status = 'sent'
            """,
            (slot_run["delivery_id"], channel.consumer_id),
        ).fetchone()
    if row is None:
        return None
    return telegram_result_from_record(row_to_dict(row), channel, mode)


def telegram_result_for_slot_run(
    db_path: Path | None,
    slot_run: dict[str, object],
    channel: Any,
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
    return telegram_result_from_record(row_to_dict(row), channel, mode)


def telegram_result_from_record(
    record: dict[str, object],
    channel: Any,
    mode: str,
) -> TelegramDeliveryResult:
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
