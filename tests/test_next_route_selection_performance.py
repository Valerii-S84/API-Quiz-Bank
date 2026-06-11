from __future__ import annotations

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


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class NextRouteSelectionPerformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_runtime_selector_scores_only_bounded_candidate_pool(self) -> None:
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

        self.assertEqual(observed["count"], selection_eligibility.CANDIDATE_POOL_LIMIT)
        self.assertEqual(
            result["selection_decision"]["candidate_count"],
            selection_eligibility.CANDIDATE_POOL_LIMIT,
        )

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

    def clone_many_items(self, count: int) -> None:
        with connect(self.db_path) as connection:
            for index in range(count):
                self.clone_item(connection, index)

    def clone_item(self, connection, index: int) -> None:
        connection.execute(
            """
            INSERT INTO quiz_items (
                item_id, source_id, language, level_band, sublevel, theme_id,
                subtheme_id, objective_id, pattern_id, difficulty_band, register,
                prompt, stem_text, options_json, answer_key, explanation, tags,
                coverage_cell_id, status, version, created_at, updated_at,
                reviewed_at, level_locked, locked_at
            )
            SELECT ?, source_id, language, level_band, sublevel, 'T10',
                   subtheme_id, objective_id, pattern_id, difficulty_band,
                   register, prompt, stem_text, options_json, answer_key,
                   explanation, tags, ?, 'approved', version, created_at,
                   updated_at, reviewed_at, level_locked, locked_at
            FROM quiz_items
            WHERE item_id = 'approved_traceable_001'
            """,
            (
                f"pool_candidate_{index:03d}",
                f"A2::T10::O02::P01::{index:03d}",
            ),
        )

    def block_original_item(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                "UPDATE quiz_items SET status = 'blocked' WHERE item_id = 'approved_traceable_001'"
            )


if __name__ == "__main__":
    unittest.main()
