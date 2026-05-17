from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    insert_visual_asset,
    row_to_dict,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    today_usage_date,
    utc_now,
)
from quizbank_mvp.selection import QuizBankProblem, SelectionFilters, SelectionRequest, select_next_item  # noqa: E402
from quizbank_mvp.visual_cache import compute_visual_cache_key  # noqa: E402
from quizbank_mvp.visual_delivery import resolve_visual_delivery  # noqa: E402
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_provider import FakeImageProvider, ImageGenerationError  # noqa: E402
from quizbank_mvp.visual_settings import save_visual_settings  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class VisualDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        self.asset_root = Path(self.temp_directory.name) / "visual-assets"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_visual", ["A2"], ["T10"])
        self.selection = select_next_item(self.db_path, selection_request())
        self.delivery = load_delivery(self)
        self.quiz_item = load_quiz_item(self)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_missing_visual_settings_returns_text_only(self) -> None:
        provider = FakeImageProvider()

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", provider, self.asset_root
        )

        self.assertEqual(resolution.state, "text_only")
        self.assertEqual(len(provider.calls), 0)

    def test_standard_cache_hit_does_not_call_provider(self) -> None:
        settings = enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        cache_key = insert_cached_asset(self, settings)
        provider = FakeImageProvider()

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", provider, self.asset_root
        )

        self.assertEqual(resolution.state, "cache_hit")
        self.assertEqual(len(provider.calls), 0)
        self.assertEqual(resolution.asset_id, "vasset_cached")
        self.assertEqual(usage_count(self, "cache_hit"), 1)
        self.assertIn("approved_traceable_001", cache_key)

    def test_cache_miss_generates_and_stores_approved_asset(self) -> None:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")
        provider = FakeImageProvider()

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", provider, self.asset_root
        )

        self.assertEqual(resolution.state, "generated_approved")
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(asset_status(self, resolution.asset_id), "approved")
        self.assertEqual(prompt_audit_count(self), 1)
        self.assertEqual(usage_count(self, "generation_succeeded"), 1)
        self.assertEqual(quota_used(self, "visual_delivery.standard", today_usage_date()), 1)
        self.assertEqual(quota_used(self, "visual_generation.standard", today_usage_date()), 1)
        self.assertEqual(quota_used(self, "visual_generation.standard", today_usage_date()[:7]), 1)

    def test_cache_hit_consumes_delivery_quota_without_generation_quota(self) -> None:
        settings = enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        insert_cached_asset(self, settings)

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", FakeImageProvider(), self.asset_root
        )

        self.assertEqual(resolution.state, "cache_hit")
        self.assertEqual(quota_used(self, "visual_delivery.standard", today_usage_date()), 1)
        self.assertEqual(quota_used(self, "visual_generation.standard", today_usage_date()), 0)

    def test_provider_failure_falls_back_to_text_only(self) -> None:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")

        resolution = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(should_fail=True),
            self.asset_root,
        )

        self.assertEqual(resolution.state, "fallback_used")
        self.assertEqual(resolution.fallback_reason, "GENERATION_FAILED")
        self.assertEqual(usage_count(self, "fallback_used"), 1)

    def test_provider_timeout_failure_falls_back_to_text_only(self) -> None:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")

        resolution = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            TimeoutImageProvider(),
            self.asset_root,
        )

        self.assertEqual(resolution.state, "fallback_used")
        self.assertEqual(resolution.fallback_reason, "GENERATION_FAILED")

    def test_qa_rejection_falls_back_to_text_only(self) -> None:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")

        resolution = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(mime_type="image/gif"),
            self.asset_root,
        )

        self.assertEqual(resolution.state, "fallback_used")
        self.assertEqual(resolution.fallback_reason, "UNSUPPORTED_MIME_TYPE")

    def test_cache_only_policy_does_not_call_provider(self) -> None:
        enable_standard_visual(self, fallback_policy=VisualFallbackPolicy.CACHE_ONLY)
        grant_feature(self, "visual_delivery.standard")
        provider = FakeImageProvider()

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", provider, self.asset_root
        )

        self.assertEqual(resolution.fallback_reason, "CACHE_ONLY_MISS")
        self.assertEqual(len(provider.calls), 0)

    def test_no_visual_entitlement_blocks_when_policy_requires_block(self) -> None:
        enable_standard_visual(self, fallback_policy=VisualFallbackPolicy.BLOCK_VISUAL_DELIVERY)

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", FakeImageProvider(), self.asset_root
        )

        self.assertEqual(resolution.state, "blocked")
        self.assertEqual(resolution.fallback_reason, "VISUAL_ENTITLEMENT_MISSING")

    def test_branded_mode_requires_branded_entitlement(self) -> None:
        enable_branded_visual(self)
        grant_feature(self, "visual_delivery.standard")

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", FakeImageProvider(), self.asset_root
        )

        self.assertEqual(resolution.resolved_mode, VisualDeliveryMode.TEXT_ONLY)
        self.assertEqual(resolution.fallback_reason, "VISUAL_ENTITLEMENT_MISSING")

    def test_generation_quota_exhausted_uses_fallback(self) -> None:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")
        record_quota(self, "visual_generation.standard", "2026-05-17", 3, 3)

        resolution = resolve_visual_delivery(
            self.db_path, self.delivery, self.quiz_item, "consumer_visual", FakeImageProvider(), self.asset_root
        )

        self.assertEqual(resolution.state, "fallback_used")
        self.assertEqual(resolution.fallback_reason, "VISUAL_QUOTA_EXHAUSTED")

    def test_base_quiz_delivery_quota_controls_selection_before_visual_pipeline(self) -> None:
        seed_consumer(self.db_path, "consumer_quota_blocked", 0, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_quota_blocked", ["A2"], ["T10"])

        with self.assertRaises(QuizBankProblem) as problem:
            select_next_item(
                self.db_path,
                SelectionRequest(
                    consumer_id="consumer_quota_blocked",
                    filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
                ),
            )

        self.assertEqual(problem.exception.reason_code, "QUOTA_EXCEEDED")

def enable_standard_visual(
    case: VisualDeliveryTests,
    fallback_policy: VisualFallbackPolicy = VisualFallbackPolicy.TEXT_ONLY,
) -> VisualSettings:
    settings = visual_settings(VisualDeliveryMode.IMAGE_STANDARD, fallback_policy)
    save_visual_settings(case.db_path, settings)
    return settings


def enable_branded_visual(case: VisualDeliveryTests) -> VisualSettings:
    settings = visual_settings(VisualDeliveryMode.IMAGE_BRANDED, VisualFallbackPolicy.TEXT_ONLY)
    save_visual_settings(case.db_path, settings)
    return settings


def visual_settings(mode: VisualDeliveryMode, fallback_policy: VisualFallbackPolicy) -> VisualSettings:
    return VisualSettings(
        consumer_id="consumer_visual",
        delivery_mode=mode,
        visual_style="standard_illustration",
        branding_preset="pilot_brand" if mode == VisualDeliveryMode.IMAGE_BRANDED else "none",
        fallback_policy=fallback_policy,
        daily_visual_delivery_limit=3,
        daily_generation_limit=3,
        monthly_generation_limit=10,
        is_active=True,
    )


def insert_cached_asset(case: VisualDeliveryTests, settings: VisualSettings) -> str:
    case.asset_root.mkdir(parents=True, exist_ok=True)
    image_path = case.asset_root / "cached.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\ncached")
    cache_key = compute_visual_cache_key(case.quiz_item, settings)
    insert_visual_asset(case.db_path, cached_asset_payload(cache_key, image_path))
    return cache_key


def cached_asset_payload(cache_key: str, image_path: Path) -> dict[str, object]:
    return {
        "asset_id": "vasset_cached",
        "quiz_item_id": "approved_traceable_001",
        "consumer_id": None,
        "delivery_mode": "image_standard",
        "visual_style": "standard_illustration",
        "branding_preset": "none",
        "image_version": "v1",
        "language": "de",
        "cache_key": cache_key,
        "image_path": str(image_path),
        "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "mime_type": "image/png",
        "width": 1024,
        "height": 1024,
        "qa_status": "approved",
        "provider_name": "fake",
        "provider_model": "fake-image-v1",
    }


def grant_feature(case: VisualDeliveryTests, feature: str) -> None:
    with connect(case.db_path) as connection:
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


def record_quota(
    case: VisualDeliveryTests,
    feature: str,
    period_key: str,
    used_count: int,
    quota_limit: int,
) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO quota_usage (
                quota_usage_id, consumer_id, feature, usage_date, used_count,
                quota_limit, updated_at
            ) VALUES (?, 'consumer_visual', ?, ?, ?, ?, ?)
            """,
            (f"quota_{feature}_{period_key}", feature, period_key, used_count, quota_limit, utc_now()),
        )


def load_delivery(case: VisualDeliveryTests) -> dict[str, object]:
    with connect(case.db_path) as connection:
        row = connection.execute("SELECT * FROM deliveries LIMIT 1").fetchone()
    return row_to_dict(row)


def load_quiz_item(case: VisualDeliveryTests) -> dict[str, object]:
    with connect(case.db_path) as connection:
        row = connection.execute(
            "SELECT * FROM quiz_items WHERE item_id = 'approved_traceable_001'"
        ).fetchone()
    return row_to_dict(row)


def selection_request() -> SelectionRequest:
    return SelectionRequest(
        consumer_id="consumer_visual",
        filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
    )


def asset_status(case: VisualDeliveryTests, asset_id: str | None) -> str:
    with connect(case.db_path) as connection:
        row = connection.execute(
            "SELECT qa_status FROM visual_assets WHERE asset_id = ?",
            (asset_id,),
        ).fetchone()
    return str(row["qa_status"])


def prompt_audit_count(case: VisualDeliveryTests) -> int:
    with connect(case.db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM visual_prompt_audit").fetchone()
    return int(row["count"])


def usage_count(case: VisualDeliveryTests, event_type: str) -> int:
    with connect(case.db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM visual_usage_events WHERE event_type = ?",
            (event_type,),
        ).fetchone()
    return int(row["count"])


def quota_used(case: VisualDeliveryTests, feature: str, period_key: str) -> int:
    with connect(case.db_path) as connection:
        row = connection.execute(
            """
            SELECT used_count FROM quota_usage
            WHERE consumer_id = 'consumer_visual' AND feature = ? AND usage_date = ?
            """,
            (feature, period_key),
        ).fetchone()
    return 0 if row is None else int(row["used_count"])


class TimeoutImageProvider:
    def generate(self, request) -> None:
        raise ImageGenerationError("openai_image_request_failed:TimeoutError")


if __name__ == "__main__":
    unittest.main()
