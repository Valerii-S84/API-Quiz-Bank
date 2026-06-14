from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    utc_now,
)
from quizbank_mvp.selection_models import (  # noqa: E402
    SelectionFilters,
    SelectionRequest,
    SelectionTargetMix,
)
from quizbank_mvp.selection_queue_filler import (  # noqa: E402
    refill_selection_queue_for_request,
    refill_selection_queues,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class SelectionQueueFillerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_refill_creates_ready_queue_from_candidate_pool(self) -> None:
        self.seed_access("consumer_allowed")
        rebuild_candidate_pools(self.db_path)

        summary = refill_selection_queue_for_request(self.db_path, self.request())

        self.assertEqual(summary["queue_count"], 1)
        self.assertEqual(summary["added_item_count"], 1)
        queue = self.single_queue()
        items = self.queued_items()
        self.assertEqual(queue["queue_status"], "ready")
        self.assertEqual(queue["available_count"], 1)
        self.assertEqual(queue["target_size"], 50)
        self.assertEqual(queue["cefr_level"], "A2")
        self.assertEqual(queue["theme_id"], "T10")
        self.assertEqual(queue["objective_id"], "")
        self.assertEqual(items[0]["item_id"], "approved_traceable_001")
        self.assertEqual(json.loads(items[0]["score_snapshot_json"])["pool_rank_position"], 0)

    def test_refill_is_idempotent_for_already_queued_items(self) -> None:
        self.seed_access("consumer_allowed")
        rebuild_candidate_pools(self.db_path)

        first = refill_selection_queue_for_request(self.db_path, self.request())
        second = refill_selection_queue_for_request(self.db_path, self.request())

        self.assertEqual(first["added_item_count"], 1)
        self.assertEqual(second["added_item_count"], 0)
        self.assertEqual(len(self.queued_items()), 1)
        self.assertEqual(self.single_queue()["available_count"], 1)

    def test_refill_excludes_recent_blocked_delivery_state(self) -> None:
        self.seed_access("consumer_allowed")
        insert_item_copy(self.db_path, "approved_traceable_002", "T10", "O02", "P01")
        self.seed_state("consumer_allowed", "api", "approved_traceable_001", "created")
        rebuild_candidate_pools(self.db_path)

        summary = refill_selection_queue_for_request(self.db_path, self.request())

        self.assertEqual(summary["added_item_count"], 1)
        self.assertEqual([item["item_id"] for item in self.queued_items()], ["approved_traceable_002"])

    def test_refill_orders_cross_pool_candidates_by_target_mix(self) -> None:
        self.seed_access("consumer_allowed")
        insert_item_copy(self.db_path, "approved_traceable_002", "T10", "O03", "P02")
        rebuild_candidate_pools(self.db_path)

        refill_selection_queue_for_request(
            self.db_path,
            self.request(
                target_mix=SelectionTargetMix(
                    objective_weights={"O02": 0.0, "O03": 1.0},
                    pattern_weights={"P01": 0.0, "P02": 1.0},
                ),
            ),
        )

        items = self.queued_items()
        self.assertEqual(items[0]["item_id"], "approved_traceable_002")
        self.assertEqual(items[1]["item_id"], "approved_traceable_001")

    def test_batch_refill_expands_channels_and_theme_scopes(self) -> None:
        self.seed_access("consumer_allowed", themes=("T10", "T11"))
        insert_item_copy(self.db_path, "approved_traceable_t11", "T11", "O02", "P01")
        rebuild_candidate_pools(self.db_path)

        summary = refill_selection_queues(
            self.db_path,
            channel_ids=("api", "telegram"),
        )

        self.assertEqual(summary["consumer_count"], 1)
        self.assertEqual(summary["queue_count"], 4)
        self.assertEqual(summary["ready_queue_count"], 4)
        self.assertEqual(summary["added_item_count"], 4)
        self.assertEqual(
            self.queue_scope_tuples(),
            [
                ("api", "A2", "T10"),
                ("api", "A2", "T11"),
                ("telegram", "A2", "T10"),
                ("telegram", "A2", "T11"),
            ],
        )

    def test_target_size_must_stay_in_refill_contract_range(self) -> None:
        self.seed_access("consumer_allowed")

        with self.assertRaisesRegex(ValueError, "between 50 and 100"):
            refill_selection_queue_for_request(self.db_path, self.request(), target_size=49)

    def seed_access(
        self,
        consumer_id: str,
        themes: tuple[str, ...] = ("T10",),
    ) -> None:
        seed_consumer(self.db_path, consumer_id, 100, ["A2"], themes)
        seed_entitlement(self.db_path, consumer_id, ["A2"], themes)

    def request(
        self,
        target_mix: SelectionTargetMix | None = None,
    ) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            target_mix=target_mix or SelectionTargetMix(),
        )

    def seed_state(
        self,
        consumer_id: str,
        channel_id: str,
        item_id: str,
        status: str,
    ) -> None:
        with connect(self.db_path) as connection:
            item = connection.execute(
                """
                SELECT language_code, content_bank_id, bank_version_id
                FROM quiz_items
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO consumer_delivery_state (
                    consumer_id, channel_id, language_code, content_bank_id,
                    bank_version_id, quiz_item_id, delivery_count,
                    last_delivery_status, last_delivered_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    consumer_id,
                    channel_id,
                    item["language_code"],
                    item["content_bank_id"],
                    item["bank_version_id"],
                    item_id,
                    status,
                    utc_now(),
                    utc_now(),
                ),
            )

    def single_queue(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_queues").fetchone()

    def queued_items(self):
        with connect(self.db_path) as connection:
            return connection.execute(
                """
                SELECT *
                FROM selection_queue_items
                ORDER BY position
                """
            ).fetchall()

    def queue_scope_tuples(self) -> list[tuple[str, str, str]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT channel_id, cefr_level, theme_id
                FROM selection_queues
                ORDER BY channel_id, theme_id
                """
            ).fetchall()
        return [(row["channel_id"], row["cefr_level"], row["theme_id"]) for row in rows]


def insert_item_copy(
    db_path: Path,
    item_id: str,
    theme_id: str,
    objective_id: str,
    pattern_id: str,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO quiz_items (
                item_id, source_id, language, language_code, content_bank_id,
                bank_version_id, level_band, sublevel, theme_id, subtheme_id,
                objective_id, pattern_id, difficulty_band, register, prompt,
                stem_text, options_json, answer_key, explanation, tags,
                coverage_cell_id, status, version, created_at, updated_at,
                reviewed_at, level_locked, locked_at
            )
            SELECT ?, source_id, language, language_code, content_bank_id,
                   bank_version_id, level_band, sublevel, ?, subtheme_id,
                   ?, ?, difficulty_band, register, prompt, stem_text,
                   options_json, answer_key, explanation, tags,
                   ? || '::copy', status, version, created_at, updated_at,
                   reviewed_at, level_locked, locked_at
            FROM quiz_items
            WHERE item_id = 'approved_traceable_001'
            """,
            (
                item_id,
                theme_id,
                objective_id,
                pattern_id,
                f"A2::{theme_id}::{objective_id}::{pattern_id}",
            ),
        )


if __name__ == "__main__":
    unittest.main()
