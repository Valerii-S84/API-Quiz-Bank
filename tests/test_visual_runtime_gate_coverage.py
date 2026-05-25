from __future__ import annotations

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
    row_to_dict,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    today_usage_date,
    utc_now,
)
from quizbank_mvp.selection import SelectionFilters, SelectionRequest, select_next_item  # noqa: E402
from quizbank_mvp.visual_delivery import resolve_visual_delivery  # noqa: E402
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_provider import FakeImageProvider  # noqa: E402
from quizbank_mvp.visual_settings import save_visual_settings  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class VisualRuntimeGateCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        self.asset_root = Path(self.temp_directory.name) / "visual-assets"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_visual", ["A2"], ["T10"])
        select_next_item(self.db_path, selection_request())
        self.delivery = load_delivery(self.db_path)
        self.quiz_item = load_quiz_item(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_generated_asset_records_visual_usage_and_quota(self) -> None:
        save_visual_settings(self.db_path, visual_settings())
        grant_feature(self.db_path, "visual_delivery.standard")
        grant_feature(self.db_path, "visual_generation.standard")

        resolution = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(),
            self.asset_root,
        )

        self.assertEqual(resolution.state, "generated_approved")
        self.assertEqual(count_events(self.db_path, "generation_requested"), 1)
        self.assertEqual(quota_used(self.db_path, "visual_delivery.standard", 10), 1)
        self.assertEqual(quota_used(self.db_path, "visual_generation.standard", 10), 1)
        self.assertEqual(quota_used(self.db_path, "visual_generation.standard", 7), 1)

    def test_cache_only_and_block_policies_stop_generation(self) -> None:
        save_visual_settings(self.db_path, visual_settings(VisualFallbackPolicy.CACHE_ONLY))
        grant_feature(self.db_path, "visual_delivery.standard")

        cache_only = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(),
            self.asset_root,
        )
        self.assertEqual(cache_only.fallback_reason, "CACHE_ONLY_MISS")

        save_visual_settings(self.db_path, visual_settings(VisualFallbackPolicy.BLOCK_VISUAL_DELIVERY))
        blocked = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(),
            self.asset_root,
        )
        self.assertEqual(blocked.state, "blocked")
        self.assertEqual(blocked.fallback_reason, "VISUAL_GENERATION_ENTITLEMENT_MISSING")

    def test_generation_quota_exhaustion_uses_text_fallback(self) -> None:
        save_visual_settings(self.db_path, visual_settings())
        grant_feature(self.db_path, "visual_delivery.standard")
        grant_feature(self.db_path, "visual_generation.standard")
        record_quota(self.db_path, "visual_generation.standard", today_usage_date(), 3, 3)

        resolution = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(),
            self.asset_root,
        )

        self.assertEqual(resolution.state, "fallback_used")
        self.assertEqual(resolution.fallback_reason, "VISUAL_QUOTA_EXHAUSTED")
        self.assertEqual(count_events(self.db_path, "fallback_used"), 1)


def selection_request() -> SelectionRequest:
    return SelectionRequest(
        consumer_id="consumer_visual",
        filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
    )


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
            INSERT INTO quota_usage (
                quota_usage_id, consumer_id, feature, usage_date, used_count,
                quota_limit, updated_at
            ) VALUES (?, 'consumer_visual', ?, ?, ?, ?, ?)
            """,
            (f"quota_{feature}_{period_key}", feature, period_key, used_count, quota_limit, utc_now()),
        )


def load_delivery(db_path: Path) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM deliveries LIMIT 1").fetchone()
    return row_to_dict(row)


def load_quiz_item(db_path: Path) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM quiz_items WHERE item_id = ?", ("approved_traceable_001",)).fetchone()
    return row_to_dict(row)


def count_events(db_path: Path, event_type: str) -> int:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM visual_usage_events WHERE event_type = ?",
            (event_type,),
        ).fetchone()
    return int(row["count"])


def quota_used(db_path: Path, feature: str, period_key_length: int) -> int:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT used_count FROM quota_usage
            WHERE consumer_id = 'consumer_visual' AND feature = ? AND length(usage_date) = ?
            """,
            (feature, period_key_length),
        ).fetchone()
    return 0 if row is None else int(row["used_count"])


if __name__ == "__main__":
    unittest.main()
