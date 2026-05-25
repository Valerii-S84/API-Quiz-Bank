"""Persistence helpers for Telegram delivery results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .database_connection import connect, row_to_dict, utc_now
from .telegram_bot_api import TelegramDeliveryError
from .telegram_models import (
    TelegramDeliveryRequest,
    TelegramDeliveryResult,
    VisualTelegramResult,
)
from .visual_delivery import VisualDeliveryResolution


def load_delivery_item(
    db_path: Path | None,
    delivery_id: str,
    consumer_id: str,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT qi.*, d.delivery_id, d.consumer_id,
                   iq.theme_group,
                   iq.image_quality_recommended,
                   iq.image_quality_source,
                   iq.image_quality_policy_share,
                   iq.image_quality_override
            FROM deliveries d
            JOIN quiz_items qi ON qi.item_id = d.quiz_item_id
            LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
            WHERE d.delivery_id = ? AND d.consumer_id = ?
            """,
            (delivery_id, consumer_id),
        ).fetchone()
    if row is None:
        raise TelegramDeliveryError("delivery_item_not_found")
    return row_to_dict(row)


def telegram_excluded_item_ids(
    db_path: Path | None,
    request: TelegramDeliveryRequest,
) -> tuple[str, ...]:
    excluded = [*sent_item_ids_for_target(db_path, request.chat_id), *request.excluded_item_ids]
    return tuple(dict.fromkeys(excluded))


def sent_item_ids_for_target(db_path: Path | None, chat_id: str) -> tuple[str, ...]:
    target_ref = redact_telegram_target(chat_id)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT d.quiz_item_id
            FROM telegram_delivery_results t
            JOIN deliveries d ON d.delivery_id = t.delivery_id
            WHERE t.telegram_target_ref = ?
              AND t.status = 'sent'
            ORDER BY t.recorded_at DESC
            """,
            (target_ref,),
        ).fetchall()
    return tuple(str(row["quiz_item_id"]) for row in rows)


def record_telegram_result(db_path: Path | None, result: TelegramDeliveryResult) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO telegram_delivery_results (
                delivery_id, consumer_id, mode, status, telegram_target_ref,
                telegram_message_id, telegram_poll_id, failure_reason, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(delivery_id) DO UPDATE SET
                mode = excluded.mode,
                status = excluded.status,
                telegram_target_ref = excluded.telegram_target_ref,
                telegram_message_id = excluded.telegram_message_id,
                telegram_poll_id = excluded.telegram_poll_id,
                failure_reason = excluded.failure_reason,
                recorded_at = excluded.recorded_at
            """,
            (
                result.delivery_id,
                result.consumer_id,
                result.mode,
                result.status,
                result.telegram_target_ref,
                result.telegram_message_id,
                result.telegram_poll_id,
                result.failure_reason,
                utc_now(),
            ),
        )
        connection.execute(
            """
            UPDATE deliveries
            SET delivery_status = ?
            WHERE delivery_id = ? AND consumer_id = ?
            """,
            (result.status, result.delivery_id, result.consumer_id),
        )


def record_visual_result(
    db_path: Path | None,
    delivery_id: str,
    consumer_id: str,
    resolution: VisualDeliveryResolution,
    visual_result: VisualTelegramResult | None,
) -> None:
    if visual_result is None:
        return
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO visual_delivery_results (
                delivery_id, consumer_id, asset_id, requested_delivery_mode,
                resolved_delivery_mode, visual_status, fallback_used,
                fallback_reason, telegram_image_message_id, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(delivery_id) DO UPDATE SET
                asset_id = excluded.asset_id,
                resolved_delivery_mode = excluded.resolved_delivery_mode,
                visual_status = excluded.visual_status,
                fallback_used = excluded.fallback_used,
                fallback_reason = excluded.fallback_reason,
                telegram_image_message_id = excluded.telegram_image_message_id,
                recorded_at = excluded.recorded_at
            """,
            (
                delivery_id,
                consumer_id,
                resolution.asset_id,
                resolution.requested_mode.value,
                resolution.resolved_mode.value,
                visual_result.visual_status,
                int(visual_result.fallback_used),
                visual_result.fallback_reason,
                visual_result.telegram_image_message_id,
                utc_now(),
            ),
        )


def redact_telegram_target(chat_id: str) -> str:
    stripped = chat_id.strip()
    if len(stripped) <= 4:
        return "***"
    return f"***{stripped[-4:]}"
