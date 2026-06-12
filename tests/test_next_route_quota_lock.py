from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import selection, selection_eligibility  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.problems import QuizBankProblem  # noqa: E402
from quizbank_mvp.selection import SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection_policy import RepeatPolicy, SelectionPolicy  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class NextRouteQuotaLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_quota_is_still_enforced_after_read_phase(self) -> None:
        self.seed_access(quota=1)

        first = self.call_next()
        second = self.call_next()

        self.assertEqual(first, "ok")
        self.assertEqual(second, "QUOTA_EXCEEDED")
        self.assertEqual(self.delivery_count(), 1)
        self.assertEqual(self.quota_used_count(), 1)

    def test_delivery_is_not_written_if_quota_is_denied(self) -> None:
        self.seed_access(quota=0)

        result = self.call_next()

        self.assertEqual(result, "QUOTA_EXCEEDED")
        self.assertEqual(self.delivery_count(), 0)
        self.assertEqual(self.quota_row_count(), 0)

    def test_exhausted_quota_precedes_no_candidate_without_increment(self) -> None:
        self.seed_access(quota=1)

        first = self.call_next(self.default_repeat_request())
        second = self.call_next(self.default_repeat_request())

        self.assertEqual(first, "ok")
        self.assertEqual(second, "QUOTA_EXCEEDED")
        self.assertEqual(self.delivery_count(), 1)
        self.assertEqual(self.quota_used_count(), 1)

    def test_quota_rolls_back_if_delivery_insert_fails(self) -> None:
        self.seed_access(quota=2)

        with mock.patch.object(
            selection,
            "create_delivery",
            side_effect=RuntimeError("forced delivery failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "forced delivery failure"):
                selection.select_next_item(self.db_path, self.request())

        self.assertEqual(self.delivery_count(), 0)
        self.assertEqual(self.quota_row_count(), 0)
        self.assertEqual(self.selection_decision_count(), 0)

        self.assertEqual(self.call_next(), "ok")
        self.assertEqual(self.quota_used_count(), 1)

    def test_concurrent_requests_do_not_overrun_quota(self) -> None:
        self.seed_access(quota=3)

        with ThreadPoolExecutor(max_workers=6) as executor:
            outcomes = list(executor.map(lambda _index: self.call_next(), range(6)))

        counts = Counter(outcomes)
        self.assertEqual(counts["ok"], 3)
        self.assertEqual(counts["QUOTA_EXCEEDED"], 3)
        self.assertEqual(self.delivery_count(), 3)
        self.assertEqual(self.quota_used_count(), 3)

    def test_delivery_history_read_completes_before_quota_reserve(self) -> None:
        self.seed_access(quota=1)
        events: list[str] = []
        original_find = selection.find_eligible_item
        original_reserve = selection.reserve_quota

        def observed_find(connection, request):
            events.append("find_start")
            result = original_find(connection, request)
            events.append("find_done")
            return result

        def observed_reserve(connection, consumer, request):
            events.append("reserve")
            return original_reserve(connection, consumer, request)

        with mock.patch.object(selection, "find_eligible_item", side_effect=observed_find):
            with mock.patch.object(selection, "reserve_quota", side_effect=observed_reserve):
                self.assertEqual(self.call_next(), "ok")

        self.assertLess(events.index("find_done"), events.index("reserve"))

    def test_concurrent_request_can_reserve_while_peer_reads_delivery_history(self) -> None:
        self.seed_access(quota=2)
        first_metrics_started = threading.Event()
        release_first_metrics = threading.Event()
        call_lock = threading.Lock()
        call_count = 0
        original_load_metrics = selection_eligibility.load_item_delivery_metrics
        first_result: dict[str, object] = {}
        second_result: dict[str, object] = {}

        def observed_load_metrics(connection, item_ids, request):
            nonlocal call_count
            with call_lock:
                call_count += 1
                current_call = call_count
            if current_call == 1:
                first_metrics_started.set()
                release_first_metrics.wait(timeout=5)
            return original_load_metrics(connection, item_ids, request)

        with mock.patch.object(
            selection_eligibility,
            "load_item_delivery_metrics",
            side_effect=observed_load_metrics,
        ):
            first_thread = threading.Thread(
                target=self.capture_next_result,
                args=(first_result,),
            )
            second_thread = threading.Thread(
                target=self.capture_next_result,
                args=(second_result,),
            )
            first_thread.start()
            self.assertTrue(first_metrics_started.wait(timeout=2))
            self.assertEqual(self.quota_row_count(), 0)
            second_thread.start()
            second_thread.join(timeout=2)
            second_finished_before_release = not second_thread.is_alive()
            release_first_metrics.set()
            first_thread.join(timeout=5)
            second_thread.join(timeout=5)

        self.assertTrue(second_finished_before_release)
        self.assertEqual(first_result, {"result": "ok"})
        self.assertEqual(second_result, {"result": "ok"})
        self.assertEqual(self.delivery_count(), 2)
        self.assertEqual(self.quota_used_count(), 2)

    def seed_access(self, quota: int) -> None:
        seed_consumer(self.db_path, "consumer_allowed", quota, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])

    def request(self) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            deterministic=True,
            policy=SelectionPolicy(repeat_policy=RepeatPolicy(enabled=False)),
        )

    def default_repeat_request(self) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            deterministic=True,
        )

    def call_next(self, request: SelectionRequest | None = None) -> str:
        try:
            selection.select_next_item(self.db_path, request or self.request())
        except QuizBankProblem as error:
            return error.reason_code
        return "ok"

    def capture_next_result(self, target: dict[str, object]) -> None:
        try:
            target["result"] = self.call_next()
        except Exception as error:
            target["error"] = repr(error)

    def delivery_count(self) -> int:
        return self.scalar_count("deliveries")

    def quota_row_count(self) -> int:
        return self.scalar_count("quota_usage")

    def selection_decision_count(self) -> int:
        return self.scalar_count("selection_decisions")

    def quota_used_count(self) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(used_count), 0) AS count FROM quota_usage"
            ).fetchone()
        return int(row["count"])

    def scalar_count(self, table_name: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])


if __name__ == "__main__":
    unittest.main()
