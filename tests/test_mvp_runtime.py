from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app
from quizbank_mvp.database import (
    connect,
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    transition_consumer_status,
    transition_item_status,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
CONTROL_FIXTURE = ROOT / "data" / "imports" / "control_sample_items.jsonl"


class MvpRuntimeCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        self.client = TestClient(create_app(self.db_path))

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def seed_access(self, consumer_id: str = "consumer_allowed", quota: int = 5) -> None:
        seed_consumer(self.db_path, consumer_id, quota, ["A2"], ["T10"])
        seed_entitlement(self.db_path, consumer_id, ["A2"], ["T10"])

    def next_item(self, consumer_id: str = "consumer_allowed"):
        return self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": consumer_id, "cefr_level": "A2", "theme_ids": ["T10"]},
            headers={"X-Consumer-Id": consumer_id},
        )


class MvpRuntimeEndpointTests(MvpRuntimeCase):
    def test_health_and_ready_endpoints_pass_after_database_init(self) -> None:
        self.assertEqual(self.client.get("/health").json()["status"], "ok")
        self.assertEqual(self.client.get("/ready").json()["status"], "ok")

    def test_app_routes_are_reflected_in_committed_openapi_seed(self) -> None:
        committed_openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        app_paths = set(create_app(self.db_path).openapi()["paths"])

        for path in [
            "/health",
            "/ready",
            "/v1/health",
            "/v1/ready",
            "/v1/quiz-items/next",
            "/v1/deliveries/{delivery_id}",
        ]:
            self.assertIn(path, app_paths)
            self.assertIn(f"  {path}:", committed_openapi)

    def test_next_item_returns_public_projection_and_delivery_log(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        response = self.next_item()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("delivery_id", payload)
        self.assertEqual(payload["quiz_item"]["item_id"], "approved_traceable_001")
        self.assertNotIn("answer_key", payload["quiz_item"])
        self.assertNotIn("explanation", payload["quiz_item"])
        self.assertFalse(payload["interaction"]["answer_key_included"])

        delivery = self.client.get(
            f"/v1/deliveries/{payload['delivery_id']}",
            headers={"X-Consumer-Id": "consumer_allowed"},
        )
        self.assertEqual(delivery.status_code, 200)
        self.assertEqual(delivery.json()["quiz_item_id"], "approved_traceable_001")

    def test_no_eligible_item_uses_problem_details_reason_code(self) -> None:
        seed_control_fixture(self.db_path, CONTROL_FIXTURE, "draft")
        self.seed_access()

        response = self.next_item()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"], "application/problem+json")
        self.assertEqual(response.json()["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")

    def test_repeat_policy_excludes_delivered_item(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access(quota=2)

        self.assertEqual(self.next_item().status_code, 200)
        repeat = self.next_item()

        self.assertEqual(repeat.status_code, 404)
        self.assertEqual(repeat.json()["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")

    def test_published_items_are_delivery_eligible(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "published")
        self.seed_access()

        response = self.next_item()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["delivery"]["item_status"], "published")

    def test_retired_items_are_not_delivery_eligible(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "retired")
        self.seed_access()

        response = self.next_item()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")

    def test_entitlement_and_quota_denials_happen_before_selection(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_no_entitlement", 5, ["A2"], ["T10"])
        self.seed_access("consumer_quota_denied", quota=0)

        entitlement = self.next_item("consumer_no_entitlement")
        quota = self.next_item("consumer_quota_denied")

        self.assertEqual(entitlement.status_code, 403)
        self.assertEqual(entitlement.json()["reason_code"], "ENTITLEMENT_MISSING_FEATURE")
        self.assertEqual(quota.status_code, 429)
        self.assertEqual(quota.json()["reason_code"], "QUOTA_EXCEEDED")

    def test_cross_consumer_delivery_read_is_denied(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access("consumer_one")
        self.seed_access("consumer_two")
        delivery_id = self.next_item("consumer_one").json()["delivery_id"]

        response = self.client.get(
            f"/v1/deliveries/{delivery_id}",
            headers={"X-Consumer-Id": "consumer_two"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["reason_code"], "DELIVERY_NOT_FOUND")

    def test_suspended_consumer_is_denied_before_delivery(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        transition_consumer_status(
            self.db_path,
            "consumer_allowed",
            "suspended",
            "local_admin",
            "pilot suspension test",
        )
        response = self.next_item()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "CONSUMER_NOT_ACTIVE")
        with connect(self.db_path) as connection:
            delivery_count = connection.execute("SELECT COUNT(*) AS count FROM deliveries").fetchone()
            audit = connection.execute(
                "SELECT * FROM audit_log WHERE entity_type = 'consumer'"
            ).fetchone()
        self.assertEqual(delivery_count["count"], 0)
        self.assertEqual(audit["action"], "consumer_status_transition")


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
                "quota_usage",
                "audit_log",
            }.issubset(table_names)
        )

    def test_status_transition_is_audited_and_controls_selection(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")
        self.seed_access(quota=5)
        self.assertEqual(self.next_item().status_code, 404)

        transition_item_status(
            self.db_path,
            "approved_traceable_001",
            "approved",
            "local_admin",
            "MVP approval test",
        )
        self.assertEqual(self.next_item().status_code, 200)

        with connect(self.db_path) as connection:
            delivery_item = connection.execute(
                "SELECT quiz_item_id FROM deliveries WHERE consumer_id = 'consumer_allowed'"
            ).fetchone()
            connection.execute(
                "DELETE FROM deliveries WHERE delivery_id IN (SELECT delivery_id FROM deliveries)"
            )
            connection.execute(
                "DELETE FROM quota_usage WHERE quota_usage_id IN (SELECT quota_usage_id FROM quota_usage)"
            )
        self.assertEqual(delivery_item["quiz_item_id"], "approved_traceable_001")

        transition_item_status(
            self.db_path,
            "approved_traceable_001",
            "blocked",
            "local_admin",
            "MVP block test",
        )
        self.assertEqual(self.next_item().status_code, 404)

        with connect(self.db_path) as connection:
            audit_count = connection.execute("SELECT COUNT(*) AS count FROM audit_log").fetchone()
        self.assertEqual(audit_count["count"], 2)

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
