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
    today_usage_date,
    utc_now,
)
from quizbank_mvp.selection import (  # noqa: E402
    SelectionFilters,
    SelectionRequest,
    select_next_item,
    upsert_quota_usage,
)
from quizbank_mvp.selection_policy import RepeatPolicy, SelectionPolicy  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class MvpSelectionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_policy_context_exposes_phase_five_controls(self) -> None:
        policy = SelectionPolicy()
        context = policy.to_context()

        self.assertIn("status", context["hard_filters"])
        self.assertEqual(
            context["channel_cycle_policy"]["exhaustion_rule"],
            "deny_when_cycle_exhausted",
        )
        self.assertEqual(context["target_distribution_policy"]["scope"], "consumer_channel")
        self.assertIn("SELECTION_REPEAT_POLICY_EXHAUSTED", context["fallback_reason_codes"])

    def test_repeat_policy_can_be_overridden_by_policy_model(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_allowed", 2, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])
        request = SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            policy=SelectionPolicy(repeat_policy=RepeatPolicy(enabled=False)),
        )

        first = select_next_item(self.db_path, request)
        second = select_next_item(self.db_path, request)

        self.assertEqual(first["quiz_item"]["id"], "approved_traceable_001")
        self.assertEqual(second["quiz_item"]["id"], "approved_traceable_001")
        self.assertIn("repeat_policy", second["delivery"]["reason"])

    def test_quota_upsert_returns_existing_row_after_conflict(self) -> None:
        seed_consumer(self.db_path, "consumer_allowed", 3, ["A2"], ["T10"])
        usage_date = today_usage_date()

        with connect(self.db_path) as connection:
            consumer = dict(
                connection.execute(
                    "SELECT * FROM consumers WHERE consumer_id = ?",
                    ("consumer_allowed",),
                ).fetchone()
            )
            connection.execute(
                """
                INSERT INTO quota_usage (
                    quota_usage_id, consumer_id, feature, usage_date, used_count,
                    quota_limit, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "quota_existing",
                    "consumer_allowed",
                    "quiz_delivery",
                    usage_date,
                    1,
                    3,
                    utc_now(),
                ),
            )

            reservation = upsert_quota_usage(
                connection,
                consumer,
                usage_date,
                "quiz_delivery",
                "quota_new_racing_insert",
            )
            rows = connection.execute(
                "SELECT quota_usage_id, used_count FROM quota_usage"
            ).fetchall()

        self.assertEqual(reservation["quota_usage_id"], "quota_existing")
        self.assertEqual(reservation["used_count"], 2)
        self.assertEqual(
            [(row["quota_usage_id"], row["used_count"]) for row in rows],
            [("quota_existing", 2)],
        )


if __name__ == "__main__":
    unittest.main()
