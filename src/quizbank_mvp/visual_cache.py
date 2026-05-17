"""Visual asset cache lookup and local asset storage."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database import ROOT, connect, insert_visual_asset, new_id, row_to_dict, utc_now
from .visual_models import VisualDeliveryMode, VisualSettings
from .visual_provider import ImageGenerationResult


DEFAULT_ASSET_ROOT = ROOT / "var" / "visual-assets"
VISUAL_IMAGE_VERSION = "v4_visual_mode_policy"


@dataclass(frozen=True)
class VisualAssetRecord:
    asset_id: str
    cache_key: str
    image_path: Path
    image_sha256: str
    mime_type: str
    width: int
    height: int
    qa_status: str
    provider_name: str
    provider_model: str


def compute_visual_cache_key(
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    image_version: str = VISUAL_IMAGE_VERSION,
) -> str:
    language = str(quiz_item.get("language", "de"))
    scope = "global"
    if settings.delivery_mode == VisualDeliveryMode.IMAGE_BRANDED:
        scope = f"consumer:{settings.consumer_id}"
    parts = [
        f"quiz:{quiz_item['item_id']}",
        f"mode:{settings.delivery_mode.value}",
        f"style:{settings.visual_style}",
        f"brand:{settings.branding_preset}",
        f"version:{image_version}",
        f"language:{language}",
        f"scope:{scope}",
    ]
    return "|".join(parts)


def find_approved_asset(
    db_path: Path | None,
    cache_key: str,
    asset_root: Path = DEFAULT_ASSET_ROOT,
) -> VisualAssetRecord | None:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM visual_assets
            WHERE cache_key = ? AND qa_status = 'approved'
            """,
            (cache_key,),
        ).fetchone()
    if row is None:
        return None
    return valid_asset_record(row_to_dict(row), asset_root)


def store_visual_asset_candidate(
    db_path: Path | None,
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    cache_key: str,
    result: ImageGenerationResult,
    asset_root: Path = DEFAULT_ASSET_ROOT,
    visual_metadata: dict[str, str] | None = None,
) -> VisualAssetRecord:
    asset_root.mkdir(parents=True, exist_ok=True)
    asset_id = new_id("vasset")
    image_path = resolve_asset_path(asset_root / f"{asset_id}.{extension_for(result.mime_type)}", asset_root)
    image_path.write_bytes(result.image_bytes)
    image_sha256 = compute_image_sha256(image_path)
    insert_visual_asset(
        db_path,
        asset_payload(
            asset_id,
            quiz_item,
            settings,
            cache_key,
            result,
            image_path,
            image_sha256,
            visual_metadata,
        ),
    )
    return VisualAssetRecord(
        asset_id=asset_id,
        cache_key=cache_key,
        image_path=image_path,
        image_sha256=image_sha256,
        mime_type=result.mime_type,
        width=result.width,
        height=result.height,
        qa_status="needs_review",
        provider_name=result.provider_name,
        provider_model=result.provider_model,
    )


def mark_visual_asset_qa_status(db_path: Path | None, asset_id: str, qa_status: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE visual_assets SET qa_status = ?, updated_at = ? WHERE asset_id = ?",
            (qa_status, utc_now(), asset_id),
        )


def valid_asset_record(row: dict[str, Any], asset_root: Path) -> VisualAssetRecord | None:
    image_path = resolve_asset_path(Path(str(row["image_path"])), asset_root)
    if not image_path.exists():
        return None
    if compute_image_sha256(image_path) != row["image_sha256"]:
        return None
    return VisualAssetRecord(
        asset_id=str(row["asset_id"]),
        cache_key=str(row["cache_key"]),
        image_path=image_path,
        image_sha256=str(row["image_sha256"]),
        mime_type=str(row["mime_type"]),
        width=int(row["width"]),
        height=int(row["height"]),
        qa_status=str(row["qa_status"]),
        provider_name=str(row["provider_name"]),
        provider_model=str(row["provider_model"]),
    )


def resolve_asset_path(path: Path, asset_root: Path) -> Path:
    root = asset_root.resolve()
    candidate = path if path.is_absolute() else (root / path).resolve()
    if not candidate.resolve().is_relative_to(root):
        raise ValueError("visual asset path must stay under asset root")
    return candidate.resolve()


def asset_payload(
    asset_id: str,
    quiz_item: dict[str, Any],
    settings: VisualSettings,
    cache_key: str,
    result: ImageGenerationResult,
    image_path: Path,
    image_sha256: str,
    visual_metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    metadata = visual_metadata or {}
    return {
        "asset_id": asset_id,
        "quiz_item_id": quiz_item["item_id"],
        "consumer_id": consumer_scope(settings),
        "delivery_mode": settings.delivery_mode.value,
        "visual_style": settings.visual_style,
        "branding_preset": settings.branding_preset,
        "image_version": VISUAL_IMAGE_VERSION,
        "language": quiz_item.get("language", "de"),
        "cache_key": cache_key,
        "image_path": str(image_path),
        "image_sha256": image_sha256,
        "mime_type": result.mime_type,
        "width": result.width,
        "height": result.height,
        "qa_status": "needs_review",
        "provider_name": result.provider_name,
        "provider_model": result.provider_model,
        "provider_asset_ref": result.provider_response_id,
        "visual_mode": metadata.get("visual_mode", "target_object"),
        "visual_target": metadata.get("visual_target", "unknown"),
        "visual_context_hint": metadata.get("visual_context_hint", ""),
        "visual_prompt_policy_version": metadata.get("visual_prompt_policy_version", "unknown"),
    }


def consumer_scope(settings: VisualSettings) -> str | None:
    if settings.delivery_mode == VisualDeliveryMode.IMAGE_BRANDED:
        return settings.consumer_id
    return None


def compute_image_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extension_for(mime_type: str) -> str:
    return {"image/png": "png", "image/webp": "webp", "image/jpeg": "jpeg"}[mime_type]
