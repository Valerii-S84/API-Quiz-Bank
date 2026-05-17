from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    insert_visual_asset,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    upsert_consumer_visual_settings,
    utc_now,
    visual_database_is_ready,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
VISUAL_TABLES = {
    "consumer_visual_settings",
    "visual_assets",
    "visual_prompt_audit",
    "visual_delivery_results",
    "visual_usage_events",
}


class VisualDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_visual_migration_is_idempotent_and_ready(self) -> None:
        initialize_database(self.db_path)

        with connect(self.db_path) as connection:
            table_names = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

        self.assertTrue(VISUAL_TABLES.issubset(table_names))
        self.assertTrue(visual_database_is_ready(self.db_path))

    def test_runtime_readiness_reports_visual_database_check(self) -> None:
        ready = TestClient(create_app(self.db_path)).get("/ready").json()

        self.assertEqual(ready["status"], "ok")
        self.assertIn({"name": "visual_database", "status": "ok"}, ready["checks"])

    def test_visual_settings_helper_writes_defaults_and_updates_mode(self) -> None:
        seed_consumer(self.db_path, "consumer_visual", 3, ["A2"], ["T10"])

        upsert_consumer_visual_settings(self.db_path, "consumer_visual")
        upsert_consumer_visual_settings(
            self.db_path,
            "consumer_visual",
            {"delivery_mode": "image_standard", "daily_visual_delivery_limit": 2},
        )

        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM consumer_visual_settings WHERE consumer_id = ?",
                ("consumer_visual",),
            ).fetchone()

        self.assertEqual(row["delivery_mode"], "image_standard")
        self.assertEqual(row["fallback_policy"], "text_only")
        self.assertEqual(row["daily_visual_delivery_limit"], 2)

    def test_visual_constraints_reject_invalid_modes_and_statuses(self) -> None:
        self.seed_delivery()

        with self.assertRaises(sqlite3.IntegrityError):
            upsert_consumer_visual_settings(
                self.db_path,
                "consumer_visual",
                {"delivery_mode": "video"},
            )
        with self.assertRaises(sqlite3.IntegrityError):
            insert_visual_asset(self.db_path, {**self.asset_record(), "qa_status": "ready"})
        with self.assertRaises(sqlite3.IntegrityError), connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO visual_delivery_results (
                    delivery_id, consumer_id, requested_delivery_mode,
                    resolved_delivery_mode, visual_status, fallback_used, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "delivery_visual",
                    "consumer_visual",
                    "image_standard",
                    "image_standard",
                    "queued",
                    0,
                    utc_now(),
                ),
            )

    def test_visual_foreign_keys_are_enforced(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            upsert_consumer_visual_settings(self.db_path, "missing_consumer")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_visual_asset(
                self.db_path,
                {**self.asset_record(), "quiz_item_id": "missing_item"},
            )
        with self.assertRaises(sqlite3.IntegrityError), connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO visual_delivery_results (
                    delivery_id, consumer_id, requested_delivery_mode,
                    resolved_delivery_mode, visual_status, fallback_used, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "missing_delivery",
                    "missing_consumer",
                    "text_only",
                    "text_only",
                    "skipped",
                    0,
                    utc_now(),
                ),
            )

    def test_visual_asset_helper_stores_consumer_scoped_cache_record(self) -> None:
        self.seed_delivery()

        asset_id = insert_visual_asset(self.db_path, self.asset_record())

        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM visual_assets WHERE asset_id = ?",
                (asset_id,),
            ).fetchone()

        self.assertEqual(row["consumer_id"], "consumer_visual")
        self.assertIn("consumer_visual", row["cache_key"])
        self.assertEqual(row["qa_status"], "approved")

    def seed_delivery(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_visual", 3, ["A2"], ["T10"])
        entitlement_id = seed_entitlement(self.db_path, "consumer_visual", ["A2"], ["T10"])
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO quota_usage (
                    quota_usage_id, consumer_id, feature, usage_date, used_count,
                    quota_limit, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "quota_visual",
                    "consumer_visual",
                    "quiz_delivery",
                    "2026-05-17",
                    1,
                    3,
                    utc_now(),
                ),
            )
            connection.execute(
                """
                INSERT INTO deliveries (
                    delivery_id, consumer_id, quiz_item_id, item_status,
                    delivery_status, source_id, source_type, provenance_note,
                    selection_reason_summary, selected_at, entitlement_id,
                    quota_usage_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "delivery_visual",
                    "consumer_visual",
                    "approved_traceable_001",
                    "approved",
                    "selected",
                    "src_control_mvp",
                    "fixture_approved_source",
                    "control_selection_fixture:approved_traceable",
                    "visual database test",
                    utc_now(),
                    entitlement_id,
                    "quota_visual",
                ),
            )

    def asset_record(self) -> dict[str, object]:
        return {
            "quiz_item_id": "approved_traceable_001",
            "consumer_id": "consumer_visual",
            "delivery_mode": "image_branded",
            "visual_style": "standard_illustration",
            "branding_preset": "pilot_brand",
            "image_version": "v1",
            "language": "de",
            "cache_key": "approved_traceable_001:image_branded:consumer_visual:v1",
            "image_path": "var/visual-assets/vasset_test.png",
            "image_sha256": "a" * 64,
            "mime_type": "image/png",
            "width": 1024,
            "height": 1024,
            "qa_status": "approved",
            "provider_name": "fake",
            "provider_model": "fake-image-v1",
        }


if __name__ == "__main__":
    unittest.main()
