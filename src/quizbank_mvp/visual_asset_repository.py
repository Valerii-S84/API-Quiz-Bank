"""Persistence helpers for visual asset rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def insert_visual_asset_record(
    db_path: Path | None,
    asset: dict[str, Any],
    connect_fn: Callable[[Path | None], Any],
    new_id_fn: Callable[[str], str],
    utc_now_fn: Callable[[], str],
) -> str:
    asset_id = str(asset.get("asset_id") or new_id_fn("vasset"))
    values = visual_asset_values(asset_id, asset, utc_now_fn())
    with connect_fn(db_path) as connection:
        connection.execute(
            """
            INSERT INTO visual_assets (
                asset_id, quiz_item_id, consumer_id, delivery_mode, visual_style,
                branding_preset, image_version, language, cache_key, image_path,
                image_sha256, mime_type, width, height, qa_status, provider_name,
                provider_model, provider_asset_ref, visual_mode, visual_target,
                visual_context_hint, visual_prompt_policy_version, created_at, updated_at
            ) VALUES (
                :asset_id, :quiz_item_id, :consumer_id, :delivery_mode, :visual_style,
                :branding_preset, :image_version, :language, :cache_key, :image_path,
                :image_sha256, :mime_type, :width, :height, :qa_status, :provider_name,
                :provider_model, :provider_asset_ref, :visual_mode, :visual_target,
                :visual_context_hint, :visual_prompt_policy_version, :created_at, :updated_at
            )
            """,
            values,
        )
    return asset_id


def visual_asset_values(asset_id: str, asset: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        **asset,
        "asset_id": asset_id,
        "created_at": asset.get("created_at", now),
        "updated_at": asset.get("updated_at", now),
        "provider_asset_ref": asset.get("provider_asset_ref"),
        "visual_mode": asset.get("visual_mode", "target_object"),
        "visual_target": asset.get("visual_target", "unknown"),
        "visual_context_hint": asset.get("visual_context_hint", ""),
        "visual_prompt_policy_version": asset.get("visual_prompt_policy_version", "unknown"),
    }
