from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from tests.test_mvp_runtime import APPROVED_FIXTURE, MvpRuntimeCase

from quizbank_mvp.database import (  # noqa: E402
    connect,
    database_is_ready,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    transition_item_status,
)


class MvpRuntimeDatabaseTests(MvpRuntimeCase):
    def test_database_can_be_created_from_empty_schema(self) -> None:
        with connect(self.db_path) as connection:
            table_names = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        self.assertTrue(
            {
                "sources",
                "quiz_items",
                "consumers",
                "deliveries",
                "entitlements",
                "api_credentials",
                "quota_usage",
                "audit_log",
                "telegram_delivery_results",
                "selection_decisions",
            }.issubset(table_names)
        )

    def test_readiness_requires_api_credentials_table(self) -> None:
        legacy_db_path = Path(self.temp_directory.name) / "legacy.sqlite3"
        with sqlite3.connect(legacy_db_path) as connection:
            connection.execute("CREATE TABLE quiz_items (item_id TEXT PRIMARY KEY)")
            connection.execute("CREATE TABLE consumers (consumer_id TEXT PRIMARY KEY)")
            connection.execute("CREATE TABLE deliveries (delivery_id TEXT PRIMARY KEY)")

        self.assertFalse(database_is_ready(legacy_db_path))

    def test_status_transition_is_audited_and_controls_selection(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")
        self.seed_access(quota=5)
        self.assertEqual(self.next_item().status_code, 503)

        transition_item_status(
            self.db_path,
            "approved_traceable_001",
            "approved",
            "local_admin",
            "MVP approval test",
        )
        self.warm_queue()
        self.assertEqual(self.next_item().status_code, 200)
        self.assert_delivered_item("approved_traceable_001")

        transition_item_status(
            self.db_path,
            "approved_traceable_001",
            "blocked",
            "local_admin",
            "MVP block test",
        )
        self.assertEqual(self.next_item().status_code, 503)
        self.assert_item_audit_count(2)

    def assert_delivered_item(self, item_id: str) -> None:
        with connect(self.db_path) as connection:
            delivery_item = connection.execute(
                "SELECT quiz_item_id FROM deliveries WHERE consumer_id = 'consumer_allowed'"
            ).fetchone()
            connection.execute("DELETE FROM consumer_delivery_state")
            connection.execute("DELETE FROM selection_queue_items")
            connection.execute("DELETE FROM selection_queues")
            connection.execute("DELETE FROM deliveries")
            connection.execute("DELETE FROM quota_usage")
        self.assertEqual(delivery_item["quiz_item_id"], item_id)

    def assert_item_audit_count(self, expected_count: int) -> None:
        with connect(self.db_path) as connection:
            audit_count = connection.execute("SELECT COUNT(*) AS count FROM audit_log").fetchone()
            item_audit_count = connection.execute(
                "SELECT COUNT(*) AS count FROM audit_log WHERE entity_type = 'quiz_item'"
            ).fetchone()
        self.assertGreaterEqual(audit_count["count"], expected_count)
        self.assertEqual(item_audit_count["count"], expected_count)

    def test_manual_entitlement_grant_is_audited(self) -> None:
        seed_consumer(self.db_path, "consumer_manual_grant", 3, ["A2"], ["T10"])
        entitlement_id = seed_entitlement(
            self.db_path,
            "consumer_manual_grant",
            ["A2"],
            ["T10"],
            valid_until="2026-12-31T00:00:00Z",
            actor="billing_admin",
            reason="manual pilot grant",
        )

        with connect(self.db_path) as connection:
            entitlement = connection.execute(
                "SELECT * FROM entitlements WHERE entitlement_id = ?",
                (entitlement_id,),
            ).fetchone()
            audit = connection.execute(
                "SELECT * FROM audit_log WHERE entity_id = ?",
                (entitlement_id,),
            ).fetchone()

        self.assertEqual(entitlement["valid_until"], "2026-12-31T00:00:00Z")
        self.assertEqual(audit["actor"], "billing_admin")
        self.assertEqual(audit["action"], "entitlement_grant")
        self.assertEqual(audit["reason"], "manual pilot grant")

    def test_duplicate_item_ids_are_rejected_by_database(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        with self.assertRaises(sqlite3.IntegrityError), connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO quiz_items (
                    item_id, source_id, language, level_band, sublevel, theme_id,
                    subtheme_id, objective_id, pattern_id, difficulty_band, register,
                    prompt, stem_text, options_json, answer_key, explanation, tags,
                    coverage_cell_id, status, version, created_at, updated_at,
                    reviewed_at, level_locked, locked_at
                )
                SELECT item_id, source_id, language, level_band, sublevel, theme_id,
                       subtheme_id, objective_id, pattern_id, difficulty_band, register,
                       prompt, stem_text, options_json, answer_key, explanation, tags,
                       coverage_cell_id, status, version, created_at, updated_at,
                       reviewed_at, level_locked, locked_at
                FROM quiz_items
                WHERE item_id = 'approved_traceable_001'
                """
            )


if __name__ == "__main__":
    unittest.main()
