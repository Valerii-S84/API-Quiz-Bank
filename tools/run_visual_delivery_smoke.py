#!/usr/bin/env python3
"""Run Visual Quiz Delivery smoke with fake provider by default."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    insert_visual_asset,
    new_id,
    row_to_dict,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    utc_now,
)
from quizbank_mvp.selection import SelectionFilters, SelectionRequest, select_next_item  # noqa: E402
from quizbank_mvp.visual_cache import compute_visual_cache_key  # noqa: E402
from quizbank_mvp.visual_delivery import resolve_visual_delivery  # noqa: E402
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_provider import FakeImageProvider, ImageGenerationProvider  # noqa: E402
from quizbank_mvp.visual_reporting import visual_metrics_summary  # noqa: E402
from quizbank_mvp.visual_provider_openai import (  # noqa: E402
    OpenAIImageProvider,
    OpenAIProviderConfigurationError,
)
from quizbank_mvp.visual_settings import save_visual_settings  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API Quiz Bank visual delivery smoke.")
    parser.add_argument("--db-path", type=Path)
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--consumer-id", default="consumer_visual_smoke")
    parser.add_argument("--provider", choices=["fake", "openai"], default="fake")
    parser.add_argument(
        "--scenario",
        choices=["generated", "cache-hit", "provider-failure", "text-only"],
        default="generated",
    )
    parser.add_argument("--visual-mode", choices=["image_standard", "image_branded"], default="image_standard")
    parser.add_argument("--cefr-level", default="A2")
    parser.add_argument("--theme-id", default="T10")
    parser.add_argument("--approve-real-generation", action="store_true")
    parser.add_argument("--openai-api-key-file", type=Path)
    parser.add_argument("--openai-model")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = provider_for_args(args)
    with tempfile.TemporaryDirectory() as directory:
        db_path = args.db_path or Path(directory) / "visual_smoke.sqlite3"
        asset_root = args.asset_root or Path(directory) / "visual-assets"
        prepare_smoke_database(db_path, args)
        selection = select_next_item(db_path, selection_request(args))
        quiz_item = load_quiz_item(db_path, selection["delivery"]["quiz_item_id"])
        settings = visual_settings_for_args(args)
        if args.scenario == "cache-hit":
            insert_smoke_cached_asset(db_path, asset_root, quiz_item, settings)
        resolution = resolve_visual_delivery(
            db_path, selection["delivery"], quiz_item, args.consumer_id, provider, asset_root
        )
        report = smoke_report(args, selection["delivery"], resolution, db_path)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def prepare_smoke_database(db_path: Path, args: argparse.Namespace) -> None:
    initialize_database(db_path)
    seed_control_fixture(db_path, APPROVED_FIXTURE, "approved")
    seed_consumer(db_path, args.consumer_id, 5, [args.cefr_level], [args.theme_id])
    seed_entitlement(db_path, args.consumer_id, [args.cefr_level], [args.theme_id])
    if args.scenario == "text-only":
        save_visual_settings(db_path, visual_settings_for_args(args))
        return
    mode = visual_mode_for_args(args)
    grant_visual_feature(db_path, args.consumer_id, f"visual_delivery.{mode.value.removeprefix('image_')}")
    if args.scenario != "cache-hit":
        grant_visual_feature(db_path, args.consumer_id, f"visual_generation.{mode.value.removeprefix('image_')}")
    save_visual_settings(db_path, visual_settings_for_args(args))


def provider_for_args(args: argparse.Namespace) -> ImageGenerationProvider:
    if args.scenario == "provider-failure":
        if args.provider != "fake":
            raise SystemExit("provider-failure scenario uses the fake provider")
        return FakeImageProvider(should_fail=True)
    if args.scenario in {"cache-hit", "text-only"}:
        return FakeImageProvider()
    if args.provider == "fake":
        return FakeImageProvider()
    if not args.approve_real_generation:
        raise SystemExit("OpenAI provider requires --approve-real-generation")
    try:
        return OpenAIImageProvider.from_environment(True, openai_environment(args))
    except OpenAIProviderConfigurationError as error:
        raise SystemExit(str(error)) from None


def openai_environment(args: argparse.Namespace) -> dict[str, str]:
    env = dict(os.environ)
    env["VISUAL_IMAGE_PROVIDER"] = "openai"
    if args.openai_api_key_file is not None:
        env["VISUAL_OPENAI_API_KEY_FILE"] = str(args.openai_api_key_file)
    if args.openai_model:
        env["VISUAL_OPENAI_IMAGE_MODEL"] = args.openai_model
    return env


def visual_settings_for_args(args: argparse.Namespace) -> VisualSettings:
    mode = visual_mode_for_args(args)
    return VisualSettings(
        consumer_id=args.consumer_id,
        delivery_mode=mode,
        visual_style="standard_illustration",
        branding_preset="visual_smoke_brand" if mode == VisualDeliveryMode.IMAGE_BRANDED else "none",
        fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
        daily_visual_delivery_limit=3,
        daily_generation_limit=3,
        monthly_generation_limit=10,
        is_active=True,
    )


def visual_mode_for_args(args: argparse.Namespace) -> VisualDeliveryMode:
    if args.scenario == "text-only":
        return VisualDeliveryMode.TEXT_ONLY
    return VisualDeliveryMode(args.visual_mode)


def selection_request(args: argparse.Namespace) -> SelectionRequest:
    return SelectionRequest(
        consumer_id=args.consumer_id,
        filters=SelectionFilters(cefr_level=args.cefr_level, theme_ids=(args.theme_id,)),
    )


def load_quiz_item(db_path: Path, item_id: str) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM quiz_items WHERE item_id = ?", (item_id,)).fetchone()
    return row_to_dict(row)


def insert_smoke_cached_asset(
    db_path: Path,
    asset_root: Path,
    quiz_item: dict[str, object],
    settings: VisualSettings,
) -> None:
    asset_root.mkdir(parents=True, exist_ok=True)
    image_path = asset_root / "visual-smoke-cache-hit.png"
    image_bytes = b"\x89PNG\r\n\x1a\nvisual-smoke-cache-hit"
    image_path.write_bytes(image_bytes)
    insert_visual_asset(
        db_path,
        {
            "asset_id": "vasset_visual_smoke_cache_hit",
            "quiz_item_id": quiz_item["item_id"],
            "consumer_id": None,
            "delivery_mode": settings.delivery_mode.value,
            "visual_style": settings.visual_style,
            "branding_preset": settings.branding_preset,
            "image_version": "v1",
            "language": quiz_item.get("language", "de"),
            "cache_key": compute_visual_cache_key(quiz_item, settings),
            "image_path": str(image_path),
            "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
            "mime_type": "image/png",
            "width": 1024,
            "height": 1024,
            "qa_status": "approved",
            "provider_name": "fake",
            "provider_model": "fake-image-v1",
        },
    )


def grant_visual_feature(db_path: Path, consumer_id: str, feature: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status,
                allowed_cefr_levels_json, allowed_theme_ids_json, valid_until, created_at
            ) VALUES (?, ?, ?, 'active', ?, ?, NULL, ?)
            ON CONFLICT(entitlement_id) DO UPDATE SET status = excluded.status
            """,
            (new_id("ent"), consumer_id, feature, json.dumps(["A2"]), json.dumps(["T10"]), utc_now()),
        )


def smoke_report(args, delivery: dict[str, object], resolution, db_path: Path) -> dict[str, object]:
    return {
        "provider": args.provider,
        "scenario": args.scenario,
        "visual_mode": args.visual_mode,
        "delivery_id": delivery["delivery_id"],
        "quiz_item_id": delivery["quiz_item_id"],
        "resolution": {
            "state": resolution.state,
            "resolved_mode": resolution.resolved_mode.value,
            "fallback_used": resolution.fallback_used,
            "fallback_reason": resolution.fallback_reason,
        },
        "asset": load_asset_summary(db_path, resolution.asset_id),
        "metrics": visual_metrics_summary(db_path),
        "quota_usage": load_quota_usage_summary(db_path, args.consumer_id),
    }


def load_asset_summary(db_path: Path, asset_id: str | None) -> dict[str, object] | None:
    if asset_id is None:
        return None
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT asset_id, image_sha256, mime_type, width, height,
                   qa_status, provider_name, provider_model
            FROM visual_assets
            WHERE asset_id = ?
            """,
            (asset_id,),
        ).fetchone()
    return None if row is None else row_to_dict(row)


def load_quota_usage_summary(db_path: Path, consumer_id: str) -> list[dict[str, object]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT feature, usage_date, used_count, quota_limit
            FROM quota_usage
            WHERE consumer_id = ? AND feature LIKE 'visual_%'
            ORDER BY feature, usage_date
            """,
            (consumer_id,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


if __name__ == "__main__":
    raise SystemExit(main())
