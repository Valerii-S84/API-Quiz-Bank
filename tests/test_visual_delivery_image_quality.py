from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import initialize_database, seed_consumer, seed_control_fixture, seed_entitlement  # noqa: E402
from quizbank_mvp.selection import select_next_item  # noqa: E402
from quizbank_mvp.visual_delivery import resolve_visual_delivery  # noqa: E402
from quizbank_mvp.visual_provider import FakeImageProvider  # noqa: E402
from tests.test_visual_delivery import (  # noqa: E402
    APPROVED_FIXTURE,
    enable_standard_visual,
    grant_feature,
    load_delivery,
    load_quiz_item,
    selection_request,
)


class VisualDeliveryImageQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        self.asset_root = Path(self.temp_directory.name) / "visual-assets"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_visual", ["A2"], ["T10"])
        select_next_item(self.db_path, selection_request())
        self.delivery = load_delivery(self)
        self.quiz_item = load_quiz_item(self)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_generation_uses_recommended_image_quality(self) -> None:
        provider = self.generate_with({"image_quality_recommended": "medium"})

        self.assertEqual(provider.calls[0].quality, "medium")

    def test_missing_recommended_image_quality_falls_back_to_low_with_warning(self) -> None:
        with self.assertLogs("quizbank_mvp.visual_delivery", level="WARNING"):
            provider = self.generate_with({"image_quality_recommended": None})

        self.assertEqual(provider.calls[0].quality, "low")

    def generate_with(self, item_updates: dict[str, object]) -> FakeImageProvider:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")
        provider = FakeImageProvider()
        resolve_visual_delivery(
            self.db_path,
            self.delivery,
            {**self.quiz_item, **item_updates},
            "consumer_visual",
            provider,
            self.asset_root,
        )
        return provider


if __name__ == "__main__":
    unittest.main()
