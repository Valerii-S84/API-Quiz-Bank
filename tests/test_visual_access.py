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
    check_visual_delivery_quota,
    check_visual_generation_access,
    check_visual_generation_quota,
    reserve_visual_delivery_quota,
    reserve_visual_generation_quota,
)
from quizbank_mvp.visual_models import (  # noqa: E402
    VisualDeliveryMode,
    VisualFallbackPolicy,
    VisualSettings,
)


class VisualAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_text_only_settings_do_not_require_visual_entitlement_or_quota(self) -> None:
        settings = self.settings(VisualDeliveryMode.TEXT_ONLY, active=False)

        access = check_visual_delivery_access(self.db_path, settings)
        quota = check_visual_delivery_quota(self.db_path, settings, "2026-05-17")

        self.assertTrue(access.is_allowed)
        self.assertEqual(access.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertTrue(quota.is_allowed)

    def test_standard_visual_requires_standard_delivery_entitlement(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_STANDARD)

        missing = check_visual_delivery_access(self.db_path, settings)
        self.grant_feature("visual_delivery.standard")
        allowed = check_visual_delivery_access(self.db_path, settings)

        self.assertTrue(missing.is_allowed)
        self.assertEqual(missing.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertEqual(missing.reason_code, "VISUAL_ENTITLEMENT_MISSING")
        self.assertTrue(allowed.is_allowed)
        self.assertEqual(allowed.resolved_mode, VisualDeliveryMode.IMAGE_STANDARD)

    def test_cache_only_policy_blocks_when_visual_entitlement_is_missing(self) -> None:
        settings = self.settings(
            VisualDeliveryMode.IMAGE_STANDARD,
            fallback_policy=VisualFallbackPolicy.CACHE_ONLY,
        )

        access = check_visual_delivery_access(self.db_path, settings)

        self.assertFalse(access.is_allowed)
        self.assertEqual(access.resolved_mode, VisualDeliveryMode.IMAGE_STANDARD)

    def test_branded_visual_requires_branded_entitlement(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_BRANDED)
        self.grant_feature("visual_delivery.standard")

        standard_only = check_visual_delivery_access(self.db_path, settings)
        self.grant_feature("visual_delivery.branded")
        branded = check_visual_delivery_access(self.db_path, settings)

        self.assertEqual(standard_only.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertEqual(branded.resolved_mode, VisualDeliveryMode.IMAGE_BRANDED)
        self.assertEqual(branded.feature, "visual_delivery.branded")

    def test_generation_requires_generation_entitlement(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_STANDARD)
        self.grant_feature("visual_delivery.standard")

        missing = check_visual_generation_access(self.db_path, settings)
        self.grant_feature("visual_generation.standard")
        allowed = check_visual_generation_access(self.db_path, settings)

        self.assertEqual(missing.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertEqual(missing.reason_code, "VISUAL_GENERATION_ENTITLEMENT_MISSING")
        self.assertEqual(allowed.feature, "visual_generation.standard")

    def test_visual_quota_is_separate_from_base_quiz_delivery_quota(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_STANDARD)
        self.record_quota("quiz_delivery", "2026-05-17", used_count=5, quota_limit=5)

        allowed = check_visual_delivery_quota(self.db_path, settings, "2026-05-17")
        self.record_quota("visual_delivery.standard", "2026-05-17", 3, 3)
        exhausted = check_visual_delivery_quota(self.db_path, settings, "2026-05-17")

        self.assertTrue(allowed.is_allowed)
        self.assertEqual(allowed.feature, "visual_delivery.standard")
        self.assertFalse(exhausted.is_allowed)
        self.assertEqual(exhausted.reason_code, "VISUAL_QUOTA_EXHAUSTED")

    def test_generation_quota_checks_daily_and_monthly_windows(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_STANDARD)
        self.record_quota("visual_generation.standard", "2026-05", 10, 10)

        monthly = check_visual_generation_quota(self.db_path, settings, "2026-05-17")
        self.record_quota("visual_generation.standard", "2026-05-17", 2, 2)
        daily = check_visual_generation_quota(self.db_path, settings, "2026-05-17")

        self.assertFalse(monthly.is_allowed)
        self.assertEqual(monthly.period_key, "2026-05")
        self.assertFalse(daily.is_allowed)
        self.assertEqual(daily.period_key, "2026-05-17")

    def test_visual_delivery_quota_reservation_updates_quota_usage(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_STANDARD)

        first = reserve_visual_delivery_quota(self.db_path, settings, "2026-05-17")
        second = reserve_visual_delivery_quota(self.db_path, settings, "2026-05-17")

        self.assertTrue(first.is_allowed)
        self.assertTrue(second.is_allowed)
        self.assertEqual(self.quota_used("visual_delivery.standard", "2026-05-17"), 2)

    def test_visual_generation_quota_reservation_updates_daily_and_monthly_usage(self) -> None:
        settings = self.settings(VisualDeliveryMode.IMAGE_STANDARD)

        reservation = reserve_visual_generation_quota(self.db_path, settings, "2026-05-17")

        self.assertTrue(reservation.is_allowed)
        self.assertEqual(self.quota_used("visual_generation.standard", "2026-05-17"), 1)
        self.assertEqual(self.quota_used("visual_generation.standard", "2026-05"), 1)

    def settings(
        self,
        mode: VisualDeliveryMode,
        active: bool = True,
        fallback_policy: VisualFallbackPolicy = VisualFallbackPolicy.TEXT_ONLY,
    ) -> VisualSettings:
        return VisualSettings(
            consumer_id="consumer_visual",
            delivery_mode=mode,
            visual_style="standard_illustration",
            branding_preset="none",
            fallback_policy=fallback_policy,
            daily_visual_delivery_limit=3,
            daily_generation_limit=2,
            monthly_generation_limit=10,
            is_active=active,
        )

    def grant_feature(self, feature: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO entitlements (
                    entitlement_id, consumer_id, feature, status,
                    allowed_cefr_levels_json, allowed_theme_ids_json,
                    valid_until, created_at
                ) VALUES (?, ?, ?, 'active', ?, ?, NULL, ?)
                """,
                (
                    f"ent_{feature}",
                    "consumer_visual",
                    feature,
                    json.dumps(["A2"]),
                    json.dumps(["T10"]),
                    utc_now(),
                ),
            )

    def record_quota(
        self,
        feature: str,
        period_key: str,
        used_count: int,
        quota_limit: int,
    ) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO quota_usage (
                    quota_usage_id, consumer_id, feature, usage_date, used_count,
                    quota_limit, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"quota_{feature}_{period_key}",
                    "consumer_visual",
                    feature,
                    period_key,
                    used_count,
                    quota_limit,
                    utc_now(),
                ),
            )

    def quota_used(self, feature: str, period_key: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT used_count FROM quota_usage
                WHERE consumer_id = ? AND feature = ? AND usage_date = ?
                """,
                ("consumer_visual", feature, period_key),
            ).fetchone()
        return 0 if row is None else int(row["used_count"])


if __name__ == "__main__":
    unittest.main()
