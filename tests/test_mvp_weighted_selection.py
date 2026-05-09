from __future__ import annotations

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
    utc_now,
)
from quizbank_mvp.selection import SelectionFilters, SelectionRequest, select_next_item  # noqa: E402
from quizbank_mvp.weighted_selection import candidate_score, select_ranked_candidate  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class MvpWeightedSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_weighted_scorer_prefers_under_delivered_coverage_cell(self) -> None:
        overused = self.candidate("aaa_overused", "T10", "P01", cell_delivery_count=5)
        balanced = self.candidate("zzz_balanced", "T11", "P02", cell_delivery_count=0)
        request = SelectionRequest("consumer_allowed", deterministic=True)

        selected = select_ranked_candidate([overused, balanced], request)

        self.assertEqual(selected["item_id"], "zzz_balanced")
        self.assertGreater(
            candidate_score(balanced, request).total,
            candidate_score(overused, request).total,
        )

    def test_first_eligible_strategy_remains_explicit_compatibility_path(self) -> None:
        request = SelectionRequest("consumer_allowed", selection_strategy="first_eligible")

        selected = select_ranked_candidate(
            [self.candidate("zzz_balanced", "T11", "P02"), self.candidate("aaa_first", "T10", "P01")],
            request,
        )

        self.assertEqual(selected["item_id"], "aaa_first")

    def test_runtime_weighted_selector_chooses_top_scored_candidate_not_first_id(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_allowed", 2, ["A2"], ["T10", "T11"])
        seed_consumer(self.db_path, "history_consumer", 10, ["A2"], ["T10", "T11"])
        entitlement_id = seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10", "T11"])
        self.clone_item("aaa_overused", "T10", "P01")
        self.clone_item("zzz_balanced", "T11", "P02")
        self.block_original_item()
        self.record_historical_deliveries(entitlement_id)

        result = select_next_item(
            self.db_path,
            SelectionRequest(
                consumer_id="consumer_allowed",
                filters=SelectionFilters(cefr_level="A2", theme_ids=("T10", "T11")),
                deterministic=True,
            ),
        )

        self.assertEqual(result["quiz_item"]["id"], "zzz_balanced")

    def candidate(
        self,
        item_id: str,
        theme_id: str,
        pattern_id: str,
        cell_delivery_count: int = 0,
    ) -> dict[str, object]:
        return {
            "item_id": item_id,
            "sublevel": "A2",
            "theme_id": theme_id,
            "objective_id": "O02",
            "pattern_id": pattern_id,
            "delivery_count": 0,
            "cell_delivery_count": cell_delivery_count,
            "last_delivered_at": "",
        }

    def clone_item(self, item_id: str, theme_id: str, pattern_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO quiz_items (
                    item_id, source_id, language, level_band, sublevel, theme_id,
                    subtheme_id, objective_id, pattern_id, difficulty_band, register,
                    prompt, stem_text, options_json, answer_key, explanation, tags,
                    coverage_cell_id, status, version, created_at, updated_at,
                    reviewed_at, level_locked, locked_at
                )
                SELECT ?, source_id, language, level_band, sublevel, ?, subtheme_id,
                       objective_id, ?, difficulty_band, register, prompt, stem_text,
                       options_json, answer_key, explanation, tags, ?, 'approved',
                       version, created_at, updated_at, reviewed_at, level_locked, locked_at
                FROM quiz_items
                WHERE item_id = 'approved_traceable_001'
                """,
                (item_id, theme_id, pattern_id, f"A2::{theme_id}::O02::{pattern_id}"),
            )

    def block_original_item(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                "UPDATE quiz_items SET status = 'blocked' WHERE item_id = 'approved_traceable_001'"
            )

    def record_historical_deliveries(self, entitlement_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO quota_usage (
                    quota_usage_id, consumer_id, feature, usage_date, used_count,
                    quota_limit, updated_at
                ) VALUES ('quota_history', 'consumer_allowed', 'quiz_delivery', '2026-05-10', 0, 10, ?)
                """,
                (utc_now(),),
            )
            for index in range(3):
                connection.execute(
                    """
                    INSERT INTO deliveries (
                        delivery_id, consumer_id, quiz_item_id, item_status,
                        delivery_status, source_id, source_type, provenance_note,
                        selection_reason_summary, selected_at, entitlement_id, quota_usage_id
                    ) VALUES (?, 'history_consumer', 'aaa_overused', 'approved',
                        'delivered', 'src_control_mvp', 'fixture_approved_source',
                        'control_selection_fixture:approved_traceable',
                        'historical_delivery', ?, ?, 'quota_history')
                    """,
                    (f"deliv_history_{index}", utc_now(), entitlement_id),
                )


if __name__ == "__main__":
    unittest.main()
