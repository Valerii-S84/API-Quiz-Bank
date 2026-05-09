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
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection import (  # noqa: E402
    QuizBankProblem,
    SelectionFilters,
    SelectionRequest,
    select_next_item,
)
from quizbank_mvp.selection_analytics import selection_analytics_snapshot  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
CONTROL_FIXTURE = ROOT / "data" / "imports" / "control_sample_items.jsonl"


class MvpSelectionDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_successful_selection_writes_decision_log(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        result = select_next_item(self.db_path, self.request())
        decision = self.single_decision()

        self.assertEqual(decision["delivery_id"], result["delivery"]["delivery_id"])
        self.assertEqual(decision["candidate_count"], 1)
        self.assertEqual(decision["eligible_count"], 1)
        self.assertEqual(decision["selected_item_id"], "approved_traceable_001")
        self.assertEqual(decision["selected_reason"], "selected_top_score")
        self.assertIn("total", json.loads(decision["selected_score_json"]))
        self.assertEqual(
            result["selection_decision"]["selection_request_id"],
            decision["selection_request_id"],
        )

    def test_no_candidate_selection_writes_decision_log_without_quota_charge(self) -> None:
        seed_control_fixture(self.db_path, CONTROL_FIXTURE, "draft")
        self.seed_access()

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(self.db_path, self.request())
        decision = self.single_decision()

        self.assertEqual(error.exception.reason_code, "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertIsNone(decision["delivery_id"])
        self.assertEqual(decision["eligible_count"], 0)
        self.assertEqual(decision["fallback_reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(json.loads(decision["blocked_reason_counts_json"])["non_deliverable_status"], 2)
        with connect(self.db_path) as connection:
            quota_count = connection.execute("SELECT COUNT(*) AS count FROM quota_usage").fetchone()
        self.assertEqual(quota_count["count"], 0)

    def test_selection_analytics_snapshot_reports_inventory_delivery_and_failures(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access(quota=2)
        select_next_item(self.db_path, self.request())
        with self.assertRaises(QuizBankProblem):
            select_next_item(self.db_path, self.request())

        snapshot = selection_analytics_snapshot(self.db_path)

        self.assertEqual(snapshot["inventory"]["by_level"]["A2"], 1)
        self.assertEqual(snapshot["inventory"]["by_theme"]["T10"], 1)
        self.assertEqual(snapshot["inventory"]["by_objective"]["O02"], 1)
        self.assertEqual(snapshot["inventory"]["by_pattern"]["P01"], 1)
        self.assertEqual(snapshot["deliveries"][0]["consumer_id"], "consumer_allowed")
        self.assertEqual(snapshot["repeat_blocks"], 1)
        self.assertEqual(snapshot["no_candidate_reasons"]["SELECTION_NO_ELIGIBLE_ITEM"], 1)

    def seed_access(self, consumer_id: str = "consumer_allowed", quota: int = 5) -> None:
        seed_consumer(self.db_path, consumer_id, quota, ["A2"], ["T10"])
        seed_entitlement(self.db_path, consumer_id, ["A2"], ["T10"])

    def request(self) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            deterministic=True,
        )

    def single_decision(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_decisions").fetchone()


if __name__ == "__main__":
    unittest.main()
