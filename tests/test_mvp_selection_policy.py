from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection import SelectionFilters, SelectionRequest, select_next_item  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
