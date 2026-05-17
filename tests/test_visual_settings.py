from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import initialize_database, seed_consumer  # noqa: E402
from quizbank_mvp.visual_models import (  # noqa: E402
    VisualDeliveryMode,
    VisualFallbackPolicy,
    VisualSettings,
)
from quizbank_mvp.visual_settings import (  # noqa: E402
    load_visual_settings,
    save_visual_settings,
    visual_settings_from_mapping,
)


class VisualSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_missing_visual_settings_default_to_text_only(self) -> None:
        settings = load_visual_settings(self.db_path, "consumer_visual")

        self.assertEqual(settings.delivery_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertEqual(settings.fallback_policy, VisualFallbackPolicy.TEXT_ONLY)
        self.assertFalse(settings.is_active)

    def test_visual_settings_are_consumer_scoped(self) -> None:
        seed_consumer(self.db_path, "consumer_other", 5, ["A2"], ["T10"])
        save_visual_settings(self.db_path, self.standard_settings("consumer_visual"))

        configured = load_visual_settings(self.db_path, "consumer_visual")
        missing = load_visual_settings(self.db_path, "consumer_other")

        self.assertEqual(configured.delivery_mode, VisualDeliveryMode.IMAGE_STANDARD)
        self.assertEqual(missing.delivery_mode, VisualDeliveryMode.TEXT_ONLY)

    def test_save_and_load_round_trips_visual_limits(self) -> None:
        save_visual_settings(self.db_path, self.standard_settings("consumer_visual"))

        settings = load_visual_settings(self.db_path, "consumer_visual")

        self.assertEqual(settings.visual_style, "standard_illustration")
        self.assertEqual(settings.branding_preset, "none")
        self.assertEqual(settings.daily_visual_delivery_limit, 3)
        self.assertEqual(settings.daily_generation_limit, 2)
        self.assertEqual(settings.monthly_generation_limit, 10)
        self.assertTrue(settings.is_active)

    def test_invalid_visual_mode_is_rejected_by_service_parser(self) -> None:
        row = {
            "consumer_id": "consumer_visual",
            "delivery_mode": "video",
            "visual_style": "standard_illustration",
            "branding_preset": "none",
            "fallback_policy": "text_only",
            "daily_visual_delivery_limit": 1,
            "daily_generation_limit": 1,
            "monthly_generation_limit": 1,
            "is_active": 1,
        }

        with self.assertRaises(ValueError):
            visual_settings_from_mapping(row)

    def test_invalid_fallback_policy_is_rejected_by_service_parser(self) -> None:
        row = {
            "consumer_id": "consumer_visual",
            "delivery_mode": "image_standard",
            "visual_style": "standard_illustration",
            "branding_preset": "none",
            "fallback_policy": "retry_forever",
            "daily_visual_delivery_limit": 1,
            "daily_generation_limit": 1,
            "monthly_generation_limit": 1,
            "is_active": 1,
        }

        with self.assertRaises(ValueError):
            visual_settings_from_mapping(row)

    def standard_settings(self, consumer_id: str) -> VisualSettings:
        return VisualSettings(
            consumer_id=consumer_id,
            delivery_mode=VisualDeliveryMode.IMAGE_STANDARD,
            visual_style="standard_illustration",
            branding_preset="none",
            fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
            daily_visual_delivery_limit=3,
            daily_generation_limit=2,
            monthly_generation_limit=10,
            is_active=True,
        )


if __name__ == "__main__":
    unittest.main()
