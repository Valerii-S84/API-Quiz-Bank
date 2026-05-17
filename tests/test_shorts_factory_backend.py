from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.trusted_delivery import SHORTS_FACTORY_BACKEND_CONSUMER_ID  # noqa: E402
from tools.provision_shorts_factory_backend_consumer import (  # noqa: E402
    provision_shorts_factory_backend,
    write_secret_env,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
TRUSTED_CONSUMER_ID = SHORTS_FACTORY_BACKEND_CONSUMER_ID
REGULAR_CONSUMER_ID = "regular_video_probe"


class ShortsFactoryBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "runtime.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.client = TestClient(create_app(self.db_path))

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_trusted_consumer_receives_answer_enabled_projection(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key")

        response = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key")

        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz_item"]
        self.assertEqual(quiz["status"], "approved")
        self.assertEqual(quiz["feedback"]["correctAnswerId"], "option_1")
        self.assertEqual(
            quiz["feedback"]["explanation"],
            "Internal answer explanation is retained in canonical data only.",
        )
        self.assertTrue(response.json()["interaction"]["answer_key_included"])
        self.assertNotIn("answer_key", quiz)

    def test_trusted_consumer_scope_limits_selection_when_filters_are_omitted(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key")

        response = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": TRUSTED_CONSUMER_ID},
            headers={
                "X-Consumer-Id": TRUSTED_CONSUMER_ID,
                "X-QuizBank-API-Key": "trusted_key",
            },
        )

        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz_item"]
        self.assertEqual(quiz["cefr_level"], "A2")
        self.assertEqual(item_scope(self.db_path, quiz["id"]), ("A2", "T10"))

    def test_trusted_consumer_scope_rejects_outside_filters(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key")

        level_denial = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key", "B1", "T10")
        theme_denial = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key", "A2", "T11")

        self.assertEqual(level_denial.status_code, 403)
        self.assertEqual(theme_denial.status_code, 403)
        self.assertEqual(level_denial.json()["reason_code"], "CONSUMER_LEVEL_NOT_ALLOWED")
        self.assertEqual(theme_denial.json()["reason_code"], "CONSUMER_THEME_NOT_ALLOWED")

    def test_regular_consumer_does_not_receive_answer_feedback(self) -> None:
        self.seed_access(REGULAR_CONSUMER_ID, "regular_key")

        response = self.next_item(REGULAR_CONSUMER_ID, "regular_key")

        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz_item"]
        self.assertEqual(quiz["status"], "approved")
        self.assertNotIn("feedback", quiz)
        self.assertNotIn("explanation", quiz)
        self.assertNotIn("answer_key", quiz)
        self.assertFalse(response.json()["interaction"]["answer_key_included"])

    def test_trusted_consumer_still_requires_entitlement(self) -> None:
        seed_consumer(self.db_path, TRUSTED_CONSUMER_ID, 5, ["A2"], ["T10"])
        seed_api_credential(self.db_path, TRUSTED_CONSUMER_ID, "trusted_key")

        response = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "ENTITLEMENT_MISSING_FEATURE")

    def test_trusted_consumer_still_respects_quota(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key", quota=0)

        response = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["reason_code"], "QUOTA_EXCEEDED")

    def test_trusted_get_by_item_id_supports_manual_quiz_id_flow(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key")

        response = self.client.get(
            "/v1/quiz-items/approved_traceable_001",
            headers={
                "X-Consumer-Id": TRUSTED_CONSUMER_ID,
                "X-QuizBank-API-Key": "trusted_key",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(payload["quiz_item"]["feedback"]["correctAnswerId"], "option_1")
        self.assertTrue(payload["interaction"]["answer_key_included"])
        self.assertEqual(self.delivery_count(), 0)

    def test_regular_consumer_cannot_use_trusted_item_lookup(self) -> None:
        self.seed_access(REGULAR_CONSUMER_ID, "regular_key")

        response = self.client.get(
            "/v1/quiz-items/approved_traceable_001",
            headers={
                "X-Consumer-Id": REGULAR_CONSUMER_ID,
                "X-QuizBank-API-Key": "regular_key",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "TRUSTED_CONSUMER_REQUIRED")

    def test_trusted_consumer_can_record_delivery_outcomes(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key")
        delivery_id = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key").json()["delivery_id"]

        for status in ("sent", "failed", "cancelled"):
            with self.subTest(status=status):
                response = self.client.post(
                    f"/v1/deliveries/{delivery_id}/outcome",
                    json={"status": status, "reason": f"test {status}"},
                    headers={
                        "X-Consumer-Id": TRUSTED_CONSUMER_ID,
                        "X-QuizBank-API-Key": "trusted_key",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], status)

    def test_regular_consumer_cannot_record_delivery_outcome(self) -> None:
        self.seed_access(TRUSTED_CONSUMER_ID, "trusted_key")
        self.seed_access(REGULAR_CONSUMER_ID, "regular_key")
        delivery_id = self.next_item(TRUSTED_CONSUMER_ID, "trusted_key").json()["delivery_id"]

        response = self.client.post(
            f"/v1/deliveries/{delivery_id}/outcome",
            json={"status": "sent"},
            headers={
                "X-Consumer-Id": REGULAR_CONSUMER_ID,
                "X-QuizBank-API-Key": "regular_key",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "TRUSTED_CONSUMER_REQUIRED")

    def test_provisioning_creates_active_consumer_without_reported_secret(self) -> None:
        secret_env_path = Path(self.temp_directory.name) / "shorts.env"
        args = argparse.Namespace(
            db_path=self.db_path,
            secret_env_out=secret_env_path,
            api_base_url="https://api.example.test",
            consumer_api_key_env="TEST_SHORTS_FACTORY_KEY_NOT_SET",
            daily_quota_limit=3,
        )

        evidence = provision_shorts_factory_backend(args)
        write_secret_env(secret_env_path, evidence["env_handoff"]["raw"])

        consumer = self.consumer_row(TRUSTED_CONSUMER_ID)
        self.assertEqual(consumer["status"], "active")
        self.assertEqual(consumer["daily_quota_limit"], 3)
        self.assertEqual(json.loads(consumer["allowed_cefr_levels_json"]), ["A2"])
        self.assertEqual(json.loads(consumer["allowed_theme_ids_json"]), ["T05"])
        entitlement = entitlement_row(self.db_path, TRUSTED_CONSUMER_ID)
        self.assertEqual(entitlement["status"], "active")
        self.assertEqual(json.loads(entitlement["allowed_cefr_levels_json"]), ["A2"])
        self.assertEqual(json.loads(entitlement["allowed_theme_ids_json"]), ["T05"])
        self.assertTrue(secret_env_path.exists())
        raw_key = evidence["env_handoff"]["raw"]["QUIZ_BANK_CONSUMER_API_KEY"]
        self.assertNotEqual(raw_key, evidence["credential_masked"])
        self.assertNotIn(raw_key, str(evidence["env_handoff"]["masked"]))
        self.assertIn("...", evidence["credential_masked"])

    def seed_access(self, consumer_id: str, api_key: str, quota: int = 5) -> None:
        seed_consumer(self.db_path, consumer_id, quota, ["A2"], ["T10"])
        seed_api_credential(self.db_path, consumer_id, api_key)
        seed_entitlement(self.db_path, consumer_id, ["A2"], ["T10"])

    def next_item(
        self,
        consumer_id: str,
        api_key: str,
        cefr_level: str = "A2",
        theme_id: str = "T10",
    ):
        return self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": consumer_id, "cefr_level": cefr_level, "theme_ids": [theme_id]},
            headers={"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": api_key},
        )

    def delivery_count(self) -> int:
        with sqlite3.connect(self.db_path) as connection:
            return int(connection.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0])

    def consumer_row(self, consumer_id: str) -> sqlite3.Row:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                "SELECT * FROM consumers WHERE consumer_id = ?",
                (consumer_id,),
            ).fetchone()
            if row is None:
                raise AssertionError(f"consumer not found: {consumer_id}")
            return row
        finally:
            connection.close()


def entitlement_row(db_path: Path, consumer_id: str) -> sqlite3.Row:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT * FROM entitlements WHERE consumer_id = ? AND feature = 'quiz_delivery'",
            (consumer_id,),
        ).fetchone()
        if row is None:
            raise AssertionError(f"entitlement not found: {consumer_id}")
        return row
    finally:
        connection.close()


def item_scope(db_path: Path, item_id: str) -> tuple[str, str]:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT sublevel, theme_id FROM quiz_items WHERE item_id = ?",
            (item_id,),
        ).fetchone()
    if row is None:
        raise AssertionError(f"item not found: {item_id}")
    return str(row[0]), str(row[1])


if __name__ == "__main__":
    unittest.main()
