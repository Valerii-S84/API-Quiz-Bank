from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import connect, initialize_database, seed_consumer, utc_now  # noqa: E402
from quizbank_mvp.visual_access import (  # noqa: E402
    check_visual_delivery_access,
    check_visual_generation_access,
    check_visual_generation_quota,
    reserve_visual_delivery_quota,
    reserve_visual_generation_quota,
)
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402


class VisualAccessGateCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_text_only_access_and_reservations_short_circuit(self) -> None:
        settings = visual_settings(mode=VisualDeliveryMode.TEXT_ONLY, is_active=False)

        delivery_access = check_visual_delivery_access(self.db_path, settings)
        generation_access = check_visual_generation_access(self.db_path, settings)
        delivery_quota = reserve_visual_delivery_quota(self.db_path, settings, "2026-05-17")
        generation_quota = reserve_visual_generation_quota(self.db_path, settings, "2026-05-17")

        self.assertEqual(delivery_access.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertEqual(generation_access.reason_code, "TEXT_ONLY_VISUAL_MODE")
        self.assertEqual(delivery_quota.feature, "visual_delivery.none")
        self.assertEqual(generation_quota.feature, "visual_generation.none")

    def test_entitlements_allow_delivery_and_generation_modes(self) -> None:
        settings = visual_settings()
        grant_feature(self.db_path, "visual_delivery.standard")
        grant_feature(self.db_path, "visual_generation.standard")

        delivery = check_visual_delivery_access(self.db_path, settings)
        generation = check_visual_generation_access(self.db_path, settings)

        self.assertTrue(delivery.is_allowed)
        self.assertEqual(delivery.feature, "visual_delivery.standard")
        self.assertTrue(generation.is_allowed)
        self.assertEqual(generation.feature, "visual_generation.standard")

    def test_missing_generation_entitlement_can_block_or_fallback(self) -> None:
        fallback = check_visual_generation_access(self.db_path, visual_settings())
        blocked = check_visual_generation_access(
            self.db_path,
            visual_settings(fallback_policy=VisualFallbackPolicy.BLOCK_VISUAL_DELIVERY),
        )

        self.assertTrue(fallback.is_allowed)
        self.assertEqual(fallback.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertFalse(blocked.is_allowed)
        self.assertEqual(blocked.resolved_mode, VisualDeliveryMode.IMAGE_STANDARD)

    def test_daily_and_monthly_generation_quota_edges_are_explicit(self) -> None:
        settings = visual_settings()
        record_quota(self.db_path, "visual_generation.standard", "2026-05-17", 3, 3)

        daily = check_visual_generation_quota(self.db_path, settings, "2026-05-17")

        self.assertFalse(daily.is_allowed)
        self.assertEqual(daily.period_key, "2026-05-17")

        record_quota(self.db_path, "visual_generation.standard", "2026-05-17", 0, 3)
        record_quota(self.db_path, "visual_generation.standard", "2026-05", 10, 10)
        monthly = check_visual_generation_quota(self.db_path, settings, "2026-05-17")

        self.assertFalse(monthly.is_allowed)
        self.assertEqual(monthly.period_key, "2026-05")


def visual_settings(
    fallback_policy: VisualFallbackPolicy = VisualFallbackPolicy.TEXT_ONLY,
    mode: VisualDeliveryMode = VisualDeliveryMode.IMAGE_STANDARD,
    is_active: bool = True,
) -> VisualSettings:
    return VisualSettings(
        consumer_id="consumer_visual",
        delivery_mode=mode,
        visual_style="standard_illustration",
        branding_preset="none",
        fallback_policy=fallback_policy,
        daily_visual_delivery_limit=3,
        daily_generation_limit=3,
        monthly_generation_limit=10,
        is_active=is_active,
    )


def grant_feature(db_path: Path, feature: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status,
                allowed_cefr_levels_json, allowed_theme_ids_json,
                valid_until, created_at
            ) VALUES (?, 'consumer_visual', ?, 'active', ?, ?, NULL, ?)
            """,
            (f"ent_{feature}", feature, json.dumps(["A2"]), json.dumps(["T10"]), utc_now()),
        )


def record_quota(db_path: Path, feature: str, period_key: str, used_count: int, quota_limit: int) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO quota_usage (
                quota_usage_id, consumer_id, feature, usage_date, used_count,
                quota_limit, updated_at
            ) VALUES (?, 'consumer_visual', ?, ?, ?, ?, ?)
            """,
            (f"quota_{feature}_{period_key}", feature, period_key, used_count, quota_limit, utc_now()),
        )


if __name__ == "__main__":
    unittest.main()
