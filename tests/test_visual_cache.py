from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    insert_visual_asset,
    seed_consumer,
    seed_control_fixture,
)
from quizbank_mvp.visual_cache import (  # noqa: E402
    VisualAssetStorageError,
    compute_visual_cache_key,
    find_approved_asset,
    store_visual_asset_candidate,
)
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_provider import ImageGenerationResult  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class VisualCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        self.asset_root = Path(self.temp_directory.name) / "visual-assets"
        self.asset_root.mkdir()
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_same_settings_produce_same_cache_key(self) -> None:
        first = compute_visual_cache_key(self.quiz_item(), self.settings())
        second = compute_visual_cache_key(self.quiz_item(), self.settings())

        self.assertEqual(first, second)

    def test_different_branding_preset_changes_cache_key(self) -> None:
        first = compute_visual_cache_key(self.quiz_item(), self.settings(branding_preset="brand_a"))
        second = compute_visual_cache_key(self.quiz_item(), self.settings(branding_preset="brand_b"))

        self.assertNotEqual(first, second)

    def test_branded_mode_includes_consumer_scope(self) -> None:
        key = compute_visual_cache_key(
            self.quiz_item(),
            self.settings(mode=VisualDeliveryMode.IMAGE_BRANDED),
        )

        self.assertIn("consumer:consumer_visual", key)

    def test_cache_key_includes_visual_mode_image_version(self) -> None:
        key = compute_visual_cache_key(self.quiz_item(), self.settings())

        self.assertIn("version:v4_visual_mode_policy", key)

    def test_approved_asset_is_reused(self) -> None:
        cache_key = self.insert_asset("approved")

        asset = find_approved_asset(self.db_path, cache_key, self.asset_root)

        self.assertIsNotNone(asset)
        self.assertEqual(asset.cache_key, cache_key)

    def test_relative_asset_path_is_resolved_from_asset_root(self) -> None:
        cache_key = self.insert_asset(
            "approved",
            file_name="relative.png",
            stored_image_path=Path("relative.png"),
        )

        asset = find_approved_asset(self.db_path, cache_key, self.asset_root)

        self.assertIsNotNone(asset)
        self.assertEqual(asset.image_path, (self.asset_root / "relative.png").resolve())

    def test_rejected_or_needs_review_asset_is_not_reused(self) -> None:
        rejected_key = self.insert_asset("rejected")
        review_key = self.insert_asset("needs_review", file_name="review.png")

        self.assertIsNone(find_approved_asset(self.db_path, rejected_key, self.asset_root))
        self.assertIsNone(find_approved_asset(self.db_path, review_key, self.asset_root))

    def test_missing_file_invalidates_cache_hit(self) -> None:
        cache_key = self.insert_asset("approved")
        (self.asset_root / "asset.png").unlink()

        self.assertIsNone(find_approved_asset(self.db_path, cache_key, self.asset_root))

    def test_visual_asset_candidate_write_succeeds_in_writable_directory(self) -> None:
        result = self.image_result()

        asset = store_visual_asset_candidate(
            self.db_path,
            self.quiz_item(),
            self.settings(),
            "cache:writable",
            result,
            self.asset_root,
        )

        self.assertTrue(asset.image_path.exists())
        self.assertEqual(asset.image_sha256, hashlib.sha256(result.image_bytes).hexdigest())
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT image_path, qa_status FROM visual_assets WHERE asset_id = ?",
                (asset.asset_id,),
            ).fetchone()
        self.assertEqual(row["image_path"], str(asset.image_path))
        self.assertEqual(row["qa_status"], "needs_review")

    def test_visual_asset_candidate_permission_denied_is_controlled(self) -> None:
        with patch(
            "quizbank_mvp.visual_cache.Path.write_bytes",
            side_effect=PermissionError(13, "Permission denied"),
        ), self.assertRaises(VisualAssetStorageError) as raised:
            store_visual_asset_candidate(
                self.db_path,
                self.quiz_item(),
                self.settings(),
                "cache:blocked",
                self.image_result(),
                self.asset_root,
            )

        self.assertEqual(raised.exception.reason_code, "VISUAL_ASSET_PERMISSION_DENIED")

    def test_image_path_outside_asset_root_is_rejected(self) -> None:
        outside_path = Path(self.temp_directory.name) / "outside.png"
        outside_path.write_bytes(b"outside")
        cache_key = self.insert_asset("approved", image_path=outside_path)

        with self.assertRaises(ValueError):
            find_approved_asset(self.db_path, cache_key, self.asset_root)

    def insert_asset(
        self,
        qa_status: str,
        file_name: str = "asset.png",
        image_path: Path | None = None,
        stored_image_path: Path | None = None,
    ) -> str:
        path = image_path or self.asset_root / file_name
        path.write_bytes(b"\x89PNG\r\n\x1a\nasset")
        cache_key = f"cache:{qa_status}:{file_name}"
        insert_visual_asset(
            self.db_path,
            {
                "quiz_item_id": "approved_traceable_001",
                "consumer_id": None,
                "delivery_mode": "image_standard",
                "visual_style": "standard_illustration",
                "branding_preset": "none",
                "image_version": "v4_visual_mode_policy",
                "language": "de",
                "cache_key": cache_key,
                "image_path": str(stored_image_path or path),
                "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mime_type": "image/png",
                "width": 1024,
                "height": 1024,
                "qa_status": qa_status,
                "provider_name": "fake",
                "provider_model": "fake-image-v1",
            },
        )
        return cache_key

    def settings(
        self,
        mode: VisualDeliveryMode = VisualDeliveryMode.IMAGE_STANDARD,
        branding_preset: str = "none",
    ) -> VisualSettings:
        return VisualSettings(
            consumer_id="consumer_visual",
            delivery_mode=mode,
            visual_style="standard_illustration",
            branding_preset=branding_preset,
            fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
            daily_visual_delivery_limit=3,
            daily_generation_limit=3,
            monthly_generation_limit=10,
            is_active=True,
        )

    def quiz_item(self) -> dict[str, str]:
        return {
            "item_id": "approved_traceable_001",
            "language": "de",
        }

    def image_result(self) -> ImageGenerationResult:
        return ImageGenerationResult(
            provider_name="fake",
            provider_model="fake-image-v1",
            provider_response_id="fake_response",
            revised_prompt="fake prompt",
            image_bytes=b"\x89PNG\r\n\x1a\ncandidate",
            mime_type="image/png",
            width=1,
            height=1,
        )


if __name__ == "__main__":
    unittest.main()
