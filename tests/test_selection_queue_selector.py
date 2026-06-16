from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import app as app_module  # noqa: E402
from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.problems import QuizBankProblem  # noqa: E402
from quizbank_mvp.selection_models import SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection_queue_filler import refill_selection_queue_for_request  # noqa: E402
from quizbank_mvp.selection_queue_selector import select_next_item_from_queue  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class SelectionQueueSelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_queue_selector_claims_item_and_finalizes_delivery(self) -> None:
        self.seed_access(quota=5)
        self.warm_queue()

        result = select_next_item_from_queue(self.db_path, self.request())

        queue_item = self.single_queue_item()
        queue = self.single_queue()
        self.assertEqual(result["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(queue_item["claim_status"], "delivered")
        self.assertEqual(queue_item["delivery_id"], result["delivery"]["delivery_id"])
        self.assertEqual(queue["available_count"], 0)
        self.assertEqual(queue["queue_status"], "warming")
        self.assertEqual(self.scalar_count("deliveries"), 1)
        self.assertEqual(self.quota_used_count(), 1)
        self.assertEqual(self.quota_reservation_count(), 1)
        self.assertTrue(self.single_delivery()["quota_reservation_id"])
        self.assertEqual(self.scalar_count("consumer_delivery_state"), 1)
        self.assertEqual(self.single_decision()["selected_item_id"], "approved_traceable_001")

    def test_queue_selector_returns_503_without_quota_charge_when_queue_is_empty(self) -> None:
        self.seed_access(quota=5)

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item_from_queue(self.db_path, self.request())

        self.assertEqual(error.exception.status, 503)
        self.assertEqual(error.exception.reason_code, "SELECTION_QUEUE_NOT_READY")
        self.assertEqual(self.scalar_count("deliveries"), 0)
        self.assertEqual(self.scalar_count("quota_usage"), 0)
        self.assertEqual(self.quota_reservation_count(), 0)
        self.assertEqual(self.scalar_count("selection_decisions"), 0)

    def test_queue_selector_denies_exhausted_quota_before_queue_claim(self) -> None:
        self.seed_access(quota=0)

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item_from_queue(self.db_path, self.request())

        self.assertEqual(error.exception.status, 429)
        self.assertEqual(error.exception.reason_code, "QUOTA_EXCEEDED")
        self.assertEqual(self.scalar_count("selection_queue_items"), 0)
        self.assertEqual(self.scalar_count("deliveries"), 0)

    def test_queue_claim_rolls_back_when_quota_is_denied(self) -> None:
        self.seed_access(quota=0)
        self.warm_queue()

        result = self.call_queue()

        self.assertEqual(result, "QUOTA_EXCEEDED")
        self.assertEqual(self.single_queue_item()["claim_status"], "available")
        self.assertEqual(self.scalar_count("deliveries"), 0)
        self.assertEqual(self.scalar_count("quota_usage"), 0)
        self.assertEqual(self.quota_reservation_count(), 0)

    def test_queue_claim_rolls_back_when_delivery_insert_fails(self) -> None:
        self.seed_access(quota=5)
        self.warm_queue()

        with mock.patch(
            "quizbank_mvp.selection_queue_selector.create_delivery",
            side_effect=RuntimeError("forced delivery failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "forced delivery failure"):
                select_next_item_from_queue(self.db_path, self.request())

        self.assertEqual(self.single_queue_item()["claim_status"], "available")
        self.assertEqual(self.scalar_count("deliveries"), 0)
        self.assertEqual(self.scalar_count("quota_usage"), 0)
        self.assertEqual(self.quota_reservation_count(), 0)
        self.assertEqual(self.scalar_count("selection_decisions"), 0)

    def test_stale_blocked_queue_item_is_not_delivered(self) -> None:
        self.seed_access(quota=5)
        self.warm_queue()
        self.block_item("approved_traceable_001")

        result = self.call_queue()

        self.assertEqual(result, "SELECTION_QUEUE_NOT_READY")
        self.assertEqual(self.single_queue_item()["claim_status"], "available")
        self.assertEqual(self.scalar_count("deliveries"), 0)
        self.assertEqual(self.scalar_count("quota_usage"), 0)
        self.assertEqual(self.quota_reservation_count(), 0)

    def test_concurrent_queue_claims_do_not_duplicate_single_item(self) -> None:
        self.seed_access(quota=5)
        self.warm_queue()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _index: self.call_queue(), range(2)))

        counts = Counter(outcomes)
        self.assertEqual(counts["ok"], 1)
        self.assertEqual(counts["SELECTION_QUEUE_NOT_READY"], 1)
        self.assertEqual(self.scalar_count("deliveries"), 1)
        self.assertEqual(self.single_queue_item()["claim_status"], "delivered")

    def seed_access(self, quota: int) -> None:
        seed_consumer(self.db_path, "consumer_allowed", quota, ["A2"], ["T10"])
        seed_api_credential(self.db_path, "consumer_allowed", self.api_key())
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])

    def warm_queue(self) -> None:
        rebuild_candidate_pools(self.db_path)
        refill_selection_queue_for_request(self.db_path, self.request())

    def request(self) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            deterministic=True,
        )

    def call_queue(self) -> str:
        try:
            select_next_item_from_queue(self.db_path, self.request())
        except QuizBankProblem as error:
            return error.reason_code
        return "ok"

    def api_key(self) -> str:
        return "test_queue_first_api_key"

    def single_queue(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_queues").fetchone()

    def single_queue_item(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_queue_items").fetchone()

    def single_delivery(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM deliveries").fetchone()

    def single_decision(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_decisions").fetchone()

    def scalar_count(self, table_name: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])

    def quota_used_count(self) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(used_count), 0) AS count FROM quota_usage"
            ).fetchone()
        return int(row["count"])

    def quota_reservation_count(self) -> int:
        return self.scalar_count("quota_reservations")

    def block_item(self, item_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                "UPDATE quiz_items SET status = 'blocked' WHERE item_id = ?",
                (item_id,),
            )


class SelectionRouteRolloutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_route_uses_queue_selector_by_default(self) -> None:
        self.seed_access(quota=5)
        self.warm_queue()

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(
                app_module,
                "select_next_item",
                side_effect=AssertionError("live selector should not run"),
            ):
                response = self.next_item_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(self.single_queue_item()["claim_status"], "delivered")

    def test_route_queue_first_returns_503_without_live_fallback(self) -> None:
        self.seed_access(quota=5)

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(
                app_module,
                "select_next_item",
                side_effect=AssertionError("live selector should not run"),
            ):
                response = self.next_item_response()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["reason_code"], "SELECTION_QUEUE_NOT_READY")
        self.assertEqual(self.scalar_count("deliveries"), 0)

    def test_route_live_fallback_requires_controlled_pilot_allowlist(self) -> None:
        self.seed_access(quota=5)

        with mock.patch.dict(os.environ, self.controlled_fallback_env("other_consumer")):
            with mock.patch.object(
                app_module,
                "select_next_item",
                side_effect=AssertionError("live selector should not run"),
            ):
                response = self.next_item_response()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["reason_code"], "SELECTION_QUEUE_NOT_READY")
        self.assertEqual(self.scalar_count("deliveries"), 0)

    def test_route_live_fallback_runs_for_allowlisted_pilot_consumer(self) -> None:
        self.seed_access(quota=5)

        with mock.patch.dict(os.environ, self.controlled_fallback_env("consumer_allowed")):
            with mock.patch.object(
                app_module,
                "select_next_item",
                wraps=app_module.select_next_item,
            ) as live_selector:
                response = self.next_item_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(live_selector.call_count, 1)
        self.assertEqual(self.scalar_count("deliveries"), 1)

    def test_route_live_fallback_does_not_bypass_quota_denial(self) -> None:
        self.seed_access(quota=0)
        self.warm_queue()

        with mock.patch.dict(os.environ, self.controlled_fallback_env("consumer_allowed")):
            with mock.patch.object(
                app_module,
                "select_next_item",
                side_effect=AssertionError("live selector should not run"),
            ):
                response = self.next_item_response()

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["reason_code"], "QUOTA_EXCEEDED")
        self.assertEqual(self.single_queue_item()["claim_status"], "available")
        self.assertEqual(self.scalar_count("deliveries"), 0)

    def test_route_denies_exhausted_quota_without_warmed_queue(self) -> None:
        self.seed_access(quota=0)

        with mock.patch.dict(os.environ, {}, clear=True):
            response = self.next_item_response()

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["reason_code"], "QUOTA_EXCEEDED")
        self.assertEqual(self.scalar_count("selection_queue_items"), 0)

    def test_route_ignores_removed_legacy_queue_flag_default(self) -> None:
        self.seed_access(quota=5)

        with mock.patch.dict(
            os.environ,
            {"QUIZBANK_NEXT_SELECTION_MODE": "", "QUIZBANK_SELECTION_QUEUE_FIRST": ""},
        ):
            with mock.patch.object(
                app_module,
                "select_next_item",
                side_effect=AssertionError("live selector should not run"),
            ):
                response = self.next_item_response()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["reason_code"], "SELECTION_QUEUE_NOT_READY")

    def test_route_rejects_explicit_live_selection_mode(self) -> None:
        self.seed_access(quota=5)

        with mock.patch.dict(os.environ, {"QUIZBANK_NEXT_SELECTION_MODE": "live"}):
            response = self.next_item_response()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["reason_code"], "SELECTION_MODE_INVALID")

    def test_route_rejects_invalid_explicit_selection_mode(self) -> None:
        self.seed_access(quota=5)

        with mock.patch.dict(os.environ, {"QUIZBANK_NEXT_SELECTION_MODE": "queue_fist"}):
            response = self.next_item_response()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["reason_code"], "SELECTION_MODE_INVALID")

    def seed_access(self, quota: int) -> None:
        seed_consumer(self.db_path, "consumer_allowed", quota, ["A2"], ["T10"])
        seed_api_credential(self.db_path, "consumer_allowed", self.api_key())
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])

    def warm_queue(self) -> None:
        rebuild_candidate_pools(self.db_path)
        refill_selection_queue_for_request(self.db_path, self.request())

    def request(self) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            deterministic=True,
        )

    def next_item_response(self):
        return TestClient(create_app(self.db_path)).post(
            "/v1/quiz-items/next",
            json={
                "consumer_id": "consumer_allowed",
                "cefr_level": "A2",
                "theme_ids": ["T10"],
            },
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": self.api_key(),
            },
        )

    def controlled_fallback_env(self, consumers: str) -> dict[str, str]:
        return {
            "QUIZBANK_NEXT_SELECTION_MODE": "controlled_pilot_fallback",
            "QUIZBANK_SELECTION_LIVE_FALLBACK_CONSUMERS": consumers,
        }

    def api_key(self) -> str:
        return "test_queue_first_api_key"

    def single_queue_item(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_queue_items").fetchone()

    def scalar_count(self, table_name: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])


if __name__ == "__main__":
    unittest.main()
