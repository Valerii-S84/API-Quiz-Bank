from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import selection_eligibility  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection import SelectionFilters, SelectionRequest, select_next_item  # noqa: E402
from tools.run_next_route_read_path_perf import primary_api_key  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
READ_PATH_REPORT = ROOT / "reports" / "scale" / "read_path_perf_after_fix_2026-06-12.json"


class NextRouteSelectionPerformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_runtime_selector_scores_only_history_shortlist(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_allowed", 500, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])
        self.clone_many_items(selection_eligibility.CANDIDATE_POOL_LIMIT + 25)
        self.block_original_item()
        observed: dict[str, int] = {}

        def capture_candidate_count(candidates, _request):
            observed["count"] = len(candidates)
            return candidates[-1] if candidates else None

        with mock.patch.object(
            selection_eligibility,
            "select_ranked_candidate",
            side_effect=capture_candidate_count,
        ):
            result = select_next_item(
                self.db_path,
                SelectionRequest(
                    consumer_id="consumer_allowed",
                    filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
                    deterministic=True,
                ),
            )

        self.assertEqual(observed["count"], selection_eligibility.HISTORY_SCORING_CANDIDATE_LIMIT)
        self.assertEqual(
            result["selection_decision"]["candidate_count"],
            selection_eligibility.CANDIDATE_POOL_LIMIT,
        )

    def test_candidate_pool_limit_is_read_path_safe(self) -> None:
        self.assertEqual(selection_eligibility.CANDIDATE_POOL_LIMIT, 150)
        self.assertLessEqual(
            selection_eligibility.HISTORY_SCORING_CANDIDATE_LIMIT,
            selection_eligibility.CANDIDATE_POOL_LIMIT,
        )

    def test_delivery_history_metrics_are_loaded_for_shortlist_only(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_allowed", 500, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])
        self.clone_many_items(selection_eligibility.CANDIDATE_POOL_LIMIT + 25)
        self.block_original_item()
        observed: dict[str, int] = {}

        def capture_metric_ids(_connection, item_ids, _request):
            observed["count"] = len(item_ids)
            return {}

        with mock.patch.object(
            selection_eligibility,
            "load_item_delivery_metrics",
            side_effect=capture_metric_ids,
        ):
            result = select_next_item(
                self.db_path,
                SelectionRequest(
                    consumer_id="consumer_allowed",
                    filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
                    deterministic=True,
                ),
            )

        self.assertEqual(observed["count"], selection_eligibility.HISTORY_SCORING_CANDIDATE_LIMIT)
        self.assertEqual(
            result["selection_decision"]["candidate_count"],
            selection_eligibility.CANDIDATE_POOL_LIMIT,
        )

    def test_thirty_thousand_item_pool_keeps_candidate_limit(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_allowed", 1, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])
        self.clone_many_items(30_000)
        self.block_original_item()

        result = select_next_item(
            self.db_path,
            SelectionRequest(
                consumer_id="consumer_allowed",
                filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
                deterministic=True,
            ),
        )

        self.assertEqual(result["selection_decision"]["candidate_count"], 150)
        self.assertEqual(result["delivery"]["item_status"], "approved")

    def test_next_route_selection_indexes_are_applied(self) -> None:
        with connect(self.db_path) as connection:
            index_names = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                ).fetchall()
            }

        self.assertTrue(
            {
                "idx_quiz_items_selection_pool",
                "idx_quiz_items_cell_lookup",
                "idx_deliveries_item",
                "idx_deliveries_item_selected_at",
                "idx_deliveries_consumer_status_item",
                "idx_deliveries_consumer_item_selected_at",
                "idx_entitlements_consumer_feature_status",
            }.issubset(index_names)
        )

    def test_read_path_report_records_baseline_gate_fields(self) -> None:
        report = json.loads(READ_PATH_REPORT.read_text(encoding="utf-8"))

        self.assertEqual(report["baseline_gate"]["request_path"], "/v1/quiz-items/next")
        self.assertTrue(report["baseline_gate"]["local_only"])
        self.assertFalse(report["baseline_gate"]["runtime_behavior_changed"])
        self.assertFalse(report["baseline_gate"]["schema_or_migration_changed"])
        self.assertIn("query_count", report["baseline_gate"]["measurements"])
        self.assertIsNotNone(report["sequential"]["query_count"]["min"])
        self.assertIn("p50", report["sequential"]["latency_ms"])
        self.assertIn("p95", report["sequential"]["latency_ms"])
        self.assert_baseline_sql_profile(report)
        self.assert_baseline_report_is_sanitized(report)

    def assert_baseline_sql_profile(self, report: dict[str, object]) -> None:
        sql_profile = report["sql_profile"]
        self.assertFalse(sql_profile["parameters_serialized"])
        self.assertGreater(sql_profile["statement_count"], 0)
        self.assertGreater(len(sql_profile["slow_sql_fingerprints"]), 0)
        explain_plans = report["explain_query_plan"]
        self.assertGreater(len(explain_plans), 0)
        self.assertFalse(any("explain_error_type" in plan for plan in explain_plans))
        self.assertTrue(all("plan" in plan for plan in explain_plans))

    def assert_baseline_report_is_sanitized(self, report: dict[str, object]) -> None:
        self.assertFalse(report["secret_or_quiz_content_printed"])
        serialized = json.dumps(report).lower()
        self.assertNotIn(primary_api_key().lower(), serialized)
        self.assertNotIn("x-quizbank-api-key", serialized)
        self.assertNotIn("stem_text", serialized)
        self.assertNotIn("answer_key", serialized)
        self.assertNotIn("options_json", serialized)

    def clone_many_items(self, count: int) -> None:
        if count <= 0:
            return
        with connect(self.db_path) as connection:
            self.clone_items_with_generated_numbers(connection, count)

    def clone_items_with_generated_numbers(self, connection, count: int) -> None:
        connection.execute(
            """
            WITH digits(digit) AS (
                VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)
            ),
            numbers(number) AS (
                SELECT ones.digit
                     + tens.digit * 10
                     + hundreds.digit * 100
                     + thousands.digit * 1000
                     + ten_thousands.digit * 10000
                FROM digits ones
                CROSS JOIN digits tens
                CROSS JOIN digits hundreds
                CROSS JOIN digits thousands
                CROSS JOIN digits ten_thousands
            )
            INSERT INTO quiz_items (
                item_id, source_id, language, language_code, content_bank_id,
                bank_version_id, level_band, sublevel, theme_id, subtheme_id,
                objective_id, pattern_id, difficulty_band, register, prompt,
                stem_text, options_json, answer_key, explanation, tags,
                coverage_cell_id, status, version, created_at, updated_at,
                reviewed_at, level_locked, locked_at
            )
            SELECT 'pool_candidate_' || printf('%05d', numbers.number),
                   source_id, language, language_code, content_bank_id,
                   bank_version_id, level_band, sublevel, 'T10', subtheme_id,
                   objective_id, pattern_id, difficulty_band, register, prompt,
                   stem_text, options_json, answer_key, explanation, tags,
                   'A2::T10::O02::P01::' || printf('%05d', numbers.number),
                   'approved', version, created_at,
                   updated_at, reviewed_at, level_locked, locked_at
            FROM quiz_items
            CROSS JOIN numbers
            WHERE item_id = 'approved_traceable_001'
              AND numbers.number < ?
            """,
            (count,),
        )

    def block_original_item(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                "UPDATE quiz_items SET status = 'blocked' WHERE item_id = 'approved_traceable_001'"
            )


if __name__ == "__main__":
    unittest.main()
