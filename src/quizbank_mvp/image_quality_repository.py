"""Persistence helpers for quiz item image quality metadata."""

from __future__ import annotations

import sqlite3
from typing import Any

from .database import utc_now


IMAGE_QUALITY_POLICY_REQUIRED_FIELDS = (
    "theme_group",
    "image_quality_recommended",
    "image_quality_source",
    "image_quality_policy_share",
)


def upsert_quiz_item_image_quality_policy(
    connection: sqlite3.Connection,
    item: dict[str, Any],
) -> None:
    if not any(field in item for field in IMAGE_QUALITY_POLICY_REQUIRED_FIELDS):
        return
    missing = [
        field
        for field in IMAGE_QUALITY_POLICY_REQUIRED_FIELDS
        if item.get(field) in (None, "")
    ]
    if missing:
        raise ValueError(f"missing image quality policy fields: {', '.join(missing)}")
    now = utc_now()
    connection.execute(
        """
        INSERT INTO quiz_item_image_quality_policy (
            item_id, theme_group, image_quality_recommended, image_quality_source,
            image_quality_policy_share, image_quality_override, created_at, updated_at
        ) VALUES (
            :item_id, :theme_group, :image_quality_recommended, :image_quality_source,
            :image_quality_policy_share, :image_quality_override, :created_at, :updated_at
        )
        ON CONFLICT(item_id) DO UPDATE SET
            theme_group = excluded.theme_group,
            image_quality_recommended = excluded.image_quality_recommended,
            image_quality_source = excluded.image_quality_source,
            image_quality_policy_share = excluded.image_quality_policy_share,
            image_quality_override = excluded.image_quality_override,
            updated_at = excluded.updated_at
        """,
        {
            "item_id": item["item_id"],
            "theme_group": item["theme_group"],
            "image_quality_recommended": item["image_quality_recommended"],
            "image_quality_source": item["image_quality_source"],
            "image_quality_policy_share": int(item["image_quality_policy_share"]),
            "image_quality_override": item.get("image_quality_override") or None,
            "created_at": item.get("image_quality_created_at", now),
            "updated_at": item.get("image_quality_updated_at", now),
        },
    )
