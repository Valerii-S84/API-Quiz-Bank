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
    database_is_ready,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    transition_consumer_status,
    transition_item_status,
)
from quizbank_mvp.selection import QuizBankProblem
from quizbank_mvp.telegram_delivery import (
    TelegramDeliveryError,
    TelegramDeliveryRequest,
    TelegramSendResult,
    build_telegram_poll_payload,
    run_telegram_delivery,
    telegram_api_payload,
    validate_telegram_poll,
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
        seed_api_credential(self.db_path, consumer_id, self.api_key_for(consumer_id))
        seed_entitlement(self.db_path, consumer_id, ["A2"], ["T10"])

    def api_key_for(self, consumer_id: str) -> str:
        return f"test_api_key_for_{consumer_id}"

    def next_item(self, consumer_id: str = "consumer_allowed"):
        return self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": consumer_id, "cefr_level": "A2", "theme_ids": ["T10"]},
            headers={
                "X-Consumer-Id": consumer_id,
                "X-QuizBank-API-Key": self.api_key_for(consumer_id),
            },
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
            "/v1/levels",
            "/v1/topics",
            "/v1/quiz-items/next",
            "/v1/deliveries/{delivery_id}",
        ]:
            self.assertIn(path, app_paths)
            self.assertIn(f"  {path}:", committed_openapi)

    def test_taxonomy_endpoints_return_canonical_levels_and_topics(self) -> None:
        levels = self.client.get("/v1/levels")
        topics = self.client.get("/v1/topics")

        self.assertEqual(levels.status_code, 200)
        self.assertEqual(
            [level["cefr_level"] for level in levels.json()["data"]],
            ["A1", "A2", "B1", "B2", "C1", "C2"],
        )
        self.assertEqual(topics.status_code, 200)
        self.assertEqual(len(topics.json()["data"]), 18)
        self.assertEqual(topics.json()["data"][0]["topic_id"], "T01")
        self.assertEqual(topics.json()["data"][0]["theme_id"], "T01")

    def test_next_item_returns_public_projection_and_delivery_log(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        response = self.next_item()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        quiz = payload["quiz_item"]
        self.assertEqual(quiz["id"], "approved_traceable_001")
        hidden_fields = {"source_traceability", "theme_id", "objective_id", "pattern_id", "answer_key", "explanation"}
        self.assertFalse(hidden_fields & quiz.keys())
        self.assertNotIn("source_traceability", payload["delivery"])
        self.assertFalse(payload["interaction"]["answer_key_included"])

        delivery = self.client.get(
            f"/v1/deliveries/{payload['delivery_id']}",
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": self.api_key_for("consumer_allowed"),
            },
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

    def test_blocked_items_are_not_delivery_eligible(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "blocked")
        self.seed_access()

        response = self.next_item()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")


class FakeTelegramAdapter:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.payloads: list[dict[str, object]] = []

    def send_quiz_poll(self, payload: dict[str, object]) -> TelegramSendResult:
        self.payloads.append(payload)
        if self.should_fail:
            raise TelegramDeliveryError("telegram_adapter_failure")
        return TelegramSendResult(message_id="12345", poll_id="poll_abc")


class MvpTelegramDeliveryTests(MvpRuntimeCase):
    def test_telegram_dry_run_uses_selection_and_records_skipped_result(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        result = run_telegram_delivery(
            self.db_path,
            TelegramDeliveryRequest(
                consumer_id="consumer_allowed",
                chat_id="-1001234567890",
                mode="dry_run",
                cefr_level="A2",
                theme_ids=("T10",),
            ),
        )

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.failure_reason, "dry_run_no_bot_api_call")
        self.assertEqual(result.telegram_target_ref, "***7890")
        with connect(self.db_path) as connection:
            delivery = connection.execute(
                "SELECT delivery_status FROM deliveries WHERE delivery_id = ?",
                (result.delivery_id,),
            ).fetchone()
            telegram_result = connection.execute(
                "SELECT * FROM telegram_delivery_results WHERE delivery_id = ?",
                (result.delivery_id,),
            ).fetchone()
        self.assertEqual(delivery["delivery_status"], "skipped")
        self.assertEqual(telegram_result["status"], "skipped")
        self.assertIsNone(telegram_result["telegram_message_id"])

    def test_telegram_real_send_records_message_and_poll_ids(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()
        adapter = FakeTelegramAdapter()

        result = run_telegram_delivery(
            self.db_path,
            TelegramDeliveryRequest(
                consumer_id="consumer_allowed",
                chat_id="@controlled_channel",
                mode="real",
                cefr_level="A2",
                theme_ids=("T10",),
            ),
            adapter=adapter,
        )

        self.assertEqual(result.status, "sent")
        self.assertEqual(result.telegram_message_id, "12345")
        self.assertEqual(result.telegram_poll_id, "poll_abc")
        self.assertEqual(adapter.payloads[0]["correct_option_ids"], [0])
        self.assertEqual(
            adapter.payloads[0]["explanation"],
            "Internal answer explanation is retained in canonical data only.",
        )
        self.assertNotIn("correct_option_id", adapter.payloads[0])
        api_payload = telegram_api_payload(adapter.payloads[0])
        self.assertEqual(api_payload["correct_option_id"], 0)
        self.assertEqual(
            api_payload["explanation"],
            "Internal answer explanation is retained in canonical data only.",
        )
        with connect(self.db_path) as connection:
            delivery = connection.execute(
                "SELECT delivery_status FROM deliveries WHERE delivery_id = ?",
                (result.delivery_id,),
            ).fetchone()
        self.assertEqual(delivery["delivery_status"], "sent")

    def test_telegram_question_omits_internal_prompt_keys_only(self) -> None:
        stem = "Im Portal ist der Antrag neu, und Lena will jetzt ___."
        cases = {
            "a1_klein_kommentar_nom_def_1?": stem,
            "Welche Antwort passt zur Situation?": f"Welche Antwort passt zur Situation?\n{stem}",
            "Setze _bitte_ passend ein.": f"Setze _bitte_ passend ein.\n{stem}",
        }
        for prompt, expected_question in cases.items():
            payload = build_telegram_poll_payload(
                "@controlled_channel",
                {
                    "delivery_id": f"deliv_{prompt[:2]}",
                    "consumer_id": "consumer_allowed",
                    "item_id": f"item_{prompt[:2]}",
                    "prompt": prompt,
                    "stem_text": stem,
                    "options_json": "[\"den Antrag senden\", \"das Brot schneiden\"]",
                    "answer_key": "0",
                    "explanation": "Die Wendung passt, weil es um das Absenden eines Antrags geht.",
                },
            )
            self.assertEqual(payload["question"], expected_question)

    def test_telegram_target_repeat_guard_blocks_same_item_for_channel(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()
        self.seed_access("consumer_second_channel_run")
        adapter = FakeTelegramAdapter()

        result = run_telegram_delivery(
            self.db_path,
            TelegramDeliveryRequest(
                consumer_id="consumer_allowed",
                chat_id="@controlled_channel",
                mode="real",
                cefr_level="A2",
                theme_ids=("T10",),
            ),
            adapter=adapter,
        )
        with self.assertRaises(QuizBankProblem) as repeat_error:
            run_telegram_delivery(
                self.db_path,
                TelegramDeliveryRequest(
                    consumer_id="consumer_second_channel_run",
                    chat_id="@controlled_channel",
                    mode="real",
                    cefr_level="A2",
                    theme_ids=("T10",),
                ),
                adapter=adapter,
            )

        self.assertEqual(result.status, "sent")
        self.assertEqual(repeat_error.exception.reason_code, "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(len(adapter.payloads), 1)

    def test_telegram_real_send_failure_is_recorded_without_duplicate_retry(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access(quota=2)
        adapter = FakeTelegramAdapter(should_fail=True)

        result = run_telegram_delivery(
            self.db_path,
            TelegramDeliveryRequest(
                consumer_id="consumer_allowed",
                chat_id="@controlled_channel",
                mode="real",
                cefr_level="A2",
                theme_ids=("T10",),
            ),
            adapter=adapter,
        )
        repeat = self.next_item()

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.failure_reason, "telegram_adapter_failure")
        self.assertEqual(repeat.status_code, 404)
        with connect(self.db_path) as connection:
            telegram_result = connection.execute(
                "SELECT * FROM telegram_delivery_results WHERE delivery_id = ?",
                (result.delivery_id,),
            ).fetchone()
        self.assertEqual(telegram_result["status"], "failed")

    def test_telegram_validation_accepts_twelve_options_profile_limit(self) -> None:
        options = [f"Option {index}" for index in range(12)]

        validate_telegram_poll("Welche Antwort ist richtig?", options, [11], "Kurz erklaert.")


class MvpRuntimeAccessControlTests(MvpRuntimeCase):
    def test_entitlement_and_quota_denials_happen_before_selection(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_no_entitlement", 5, ["A2"], ["T10"])
        seed_api_credential(
            self.db_path,
            "consumer_no_entitlement",
            self.api_key_for("consumer_no_entitlement"),
        )
        self.seed_access("consumer_quota_denied", quota=0)

        entitlement = self.next_item("consumer_no_entitlement")
        quota = self.next_item("consumer_quota_denied")

        self.assertEqual(entitlement.status_code, 403)
        self.assertEqual(entitlement.json()["reason_code"], "ENTITLEMENT_MISSING_FEATURE")
        self.assertEqual(quota.status_code, 429)
        self.assertEqual(quota.json()["reason_code"], "QUOTA_EXCEEDED")

    def test_level_and_theme_filters_control_item_eligibility(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_allowed", 5, ["A2", "B1"], ["T10", "T11"])
        seed_api_credential(self.db_path, "consumer_allowed", self.api_key_for("consumer_allowed"))
        seed_entitlement(self.db_path, "consumer_allowed", ["A2", "B1"], ["T10", "T11"])

        level_mismatch = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "B1", "theme_ids": ["T10"]},
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": self.api_key_for("consumer_allowed"),
            },
        )
        theme_mismatch = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "A2", "theme_ids": ["T11"]},
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": self.api_key_for("consumer_allowed"),
            },
        )

        self.assertEqual(level_mismatch.status_code, 404)
        self.assertEqual(theme_mismatch.status_code, 404)
        self.assertEqual(level_mismatch.json()["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(theme_mismatch.json()["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")

    def test_consumer_scope_denials_happen_before_selection(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        level_denial = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "B1", "theme_ids": ["T10"]},
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": self.api_key_for("consumer_allowed"),
            },
        )
        theme_denial = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "A2", "theme_ids": ["T11"]},
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": self.api_key_for("consumer_allowed"),
            },
        )

        self.assertEqual(level_denial.status_code, 403)
        self.assertEqual(theme_denial.status_code, 403)
        self.assertEqual(level_denial.json()["reason_code"], "CONSUMER_LEVEL_NOT_ALLOWED")
        self.assertEqual(theme_denial.json()["reason_code"], "CONSUMER_THEME_NOT_ALLOWED")

    def test_cross_consumer_delivery_read_is_denied(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access("consumer_one")
        self.seed_access("consumer_two")
        delivery_id = self.next_item("consumer_one").json()["delivery_id"]

        response = self.client.get(
            f"/v1/deliveries/{delivery_id}",
            headers={
                "X-Consumer-Id": "consumer_two",
                "X-QuizBank-API-Key": self.api_key_for("consumer_two"),
            },
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

    def test_missing_api_key_is_denied_before_delivery(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        response = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "A2"},
            headers={"X-Consumer-Id": "consumer_allowed"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["reason_code"], "AUTH_REQUIRED")

    def test_invalid_api_key_is_denied_before_delivery(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        response = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "A2"},
            headers={"X-Consumer-Id": "consumer_allowed", "X-QuizBank-API-Key": "wrong_key"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["reason_code"], "AUTH_INVALID_API_KEY")

    def test_raw_api_key_is_not_stored(self) -> None:
        self.seed_access()

        with connect(self.db_path) as connection:
            credential = connection.execute(
                "SELECT key_prefix, key_hash FROM api_credentials WHERE consumer_id = ?",
                ("consumer_allowed",),
            ).fetchone()

        self.assertEqual(credential["key_prefix"], self.api_key_for("consumer_allowed")[:12])
        self.assertNotEqual(credential["key_hash"], self.api_key_for("consumer_allowed"))
        self.assertNotIn("consumer_allowed", credential["key_hash"])

    def test_api_key_cannot_be_used_for_another_consumer(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access("consumer_one")
        self.seed_access("consumer_two")

        response = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_two", "cefr_level": "A2"},
            headers={
                "X-Consumer-Id": "consumer_one",
                "X-QuizBank-API-Key": self.api_key_for("consumer_one"),
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "AUTH_CONSUMER_MISMATCH")


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
            item_audit_count = connection.execute(
                "SELECT COUNT(*) AS count FROM audit_log WHERE entity_type = 'quiz_item'"
            ).fetchone()
        self.assertGreaterEqual(audit_count["count"], 2)
        self.assertEqual(item_audit_count["count"], 2)

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
