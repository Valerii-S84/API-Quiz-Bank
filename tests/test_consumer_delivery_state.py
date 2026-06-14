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
from quizbank_mvp.selection import (  # noqa: E402
    QuizBankProblem,
    SelectionFilters,
    SelectionRequest,
    select_next_item,
)
from quizbank_mvp.selection_policy import RepeatPolicy, SelectionPolicy  # noqa: E402
from quizbank_mvp.telegram_delivery import (  # noqa: E402
    TelegramDeliveryRequest,
    run_telegram_delivery,
)
from quizbank_mvp.trusted_delivery import (  # noqa: E402
    SHORTS_FACTORY_BACKEND_CONSUMER_ID,
    record_delivery_outcome,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class ConsumerDeliveryStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_next_item_writes_consumer_delivery_state(self) -> None:
        self.seed_access("consumer_allowed")

        result = select_next_item(self.db_path, self.request())
        state = self.state_for_delivery(result["delivery"]["delivery_id"])

        self.assertEqual(state["channel_id"], "api")
        self.assertEqual(state["delivery_count"], 1)
        self.assertEqual(state["last_delivery_status"], "created")
        self.assertEqual(state["last_delivered_at"], result["delivery"]["selected_at"])

    def test_repeat_policy_reads_consumer_delivery_state(self) -> None:
        self.seed_access("consumer_allowed")
        self.seed_state("consumer_allowed", "api", "created")

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(self.db_path, self.request())

        self.assertEqual(error.exception.reason_code, "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(self.delivery_count(), 0)

    def test_non_blocked_state_status_allows_selection(self) -> None:
        self.seed_access("consumer_allowed", quota=2)
        self.seed_state("consumer_allowed", "api", "cancelled")

        result = select_next_item(self.db_path, self.request())
        state = self.state_for_delivery(result["delivery"]["delivery_id"])

        self.assertEqual(result["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(state["delivery_count"], 2)
        self.assertEqual(state["last_delivery_status"], "created")

    def test_repeat_window_ignores_expired_state(self) -> None:
        self.seed_access("consumer_allowed", quota=2)
        self.seed_state(
            "consumer_allowed",
            "api",
            "created",
            last_delivered_at="2000-01-01T00:00:00Z",
        )

        result = select_next_item(
            self.db_path,
            self.request(
                policy=SelectionPolicy(repeat_policy=RepeatPolicy(repeat_window_days=1)),
            ),
        )

        self.assertEqual(result["quiz_item"]["id"], "approved_traceable_001")

    def test_channel_specific_state_does_not_block_api_request(self) -> None:
        self.seed_access("consumer_allowed", quota=2)
        self.seed_state("consumer_allowed", "telegram", "created")

        result = select_next_item(self.db_path, self.request())

        self.assertEqual(result["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(self.state_count("consumer_allowed"), 2)

    def test_repeat_disabled_second_delivery_updates_state_count(self) -> None:
        self.seed_access("consumer_allowed", quota=2)
        request = self.request(
            policy=SelectionPolicy(repeat_policy=RepeatPolicy(enabled=False)),
        )

        first = select_next_item(self.db_path, request)
        second = select_next_item(self.db_path, request)
        state = self.state_for_delivery(second["delivery"]["delivery_id"])

        self.assertNotEqual(first["delivery"]["delivery_id"], second["delivery"]["delivery_id"])
        self.assertEqual(state["delivery_count"], 2)

    def test_telegram_result_updates_consumer_delivery_state_status(self) -> None:
        self.seed_access("consumer_allowed")

        result = run_telegram_delivery(
            self.db_path,
            TelegramDeliveryRequest(
                consumer_id="consumer_allowed",
                chat_id="@controlled_channel",
                mode="dry_run",
                cefr_level="A2",
                theme_ids=("T10",),
            ),
        )
        state = self.state_for_delivery(result.delivery_id)

        self.assertEqual(state["channel_id"], "telegram")
        self.assertEqual(state["last_delivery_status"], "skipped")

    def test_trusted_outcome_updates_consumer_delivery_state_status(self) -> None:
        self.seed_access(SHORTS_FACTORY_BACKEND_CONSUMER_ID)
        result = select_next_item(
            self.db_path,
            self.request(consumer_id=SHORTS_FACTORY_BACKEND_CONSUMER_ID),
        )
        delivery_id = result["delivery"]["delivery_id"]

        record_delivery_outcome(
            self.db_path,
            delivery_id,
            SHORTS_FACTORY_BACKEND_CONSUMER_ID,
            "cancelled",
        )
        state = self.state_for_delivery(delivery_id)

        self.assertEqual(state["last_delivery_status"], "cancelled")

    def seed_access(self, consumer_id: str, quota: int = 5) -> None:
        seed_consumer(self.db_path, consumer_id, quota, ["A2"], ["T10"])
        seed_entitlement(self.db_path, consumer_id, ["A2"], ["T10"])

    def request(
        self,
        consumer_id: str = "consumer_allowed",
        policy: SelectionPolicy | None = None,
    ) -> SelectionRequest:
        return SelectionRequest(
            consumer_id=consumer_id,
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            deterministic=True,
            policy=policy or SelectionPolicy(),
        )

    def seed_state(
        self,
        consumer_id: str,
        channel_id: str,
        last_delivery_status: str,
        last_delivered_at: str | None = None,
    ) -> None:
        with connect(self.db_path) as connection:
            item = connection.execute(
                """
                SELECT item_id, language_code, content_bank_id, bank_version_id
                FROM quiz_items
                WHERE item_id = 'approved_traceable_001'
                """
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
                    item["item_id"],
                    last_delivery_status,
                    last_delivered_at or utc_now(),
                    utc_now(),
                ),
            )

    def state_for_delivery(self, delivery_id: str):
        with connect(self.db_path) as connection:
            return connection.execute(
                """
                SELECT *
                FROM consumer_delivery_state
                WHERE last_delivery_id = ?
                """,
                (delivery_id,),
            ).fetchone()

    def delivery_count(self) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM deliveries").fetchone()
        return int(row["count"])

    def state_count(self, consumer_id: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM consumer_delivery_state WHERE consumer_id = ?",
                (consumer_id,),
            ).fetchone()
        return int(row["count"])


if __name__ == "__main__":
    unittest.main()
