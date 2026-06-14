from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.selection import (  # noqa: E402
    ConsumerProfile,
    SelectionFilters,
    SelectionRequest,
    SelectionTargetMix,
    no_eligible_problem,
)
from quizbank_mvp.selection_policy import RepeatPolicy, SelectionPolicy  # noqa: E402


class MvpSelectionContractTests(unittest.TestCase):
    def test_selection_request_accepts_explicit_filters_contract(self) -> None:
        request = SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(
                cefr_level="A2",
                theme_ids=("T10",),
                objective_ids=("O02",),
                pattern_ids=("P01",),
                excluded_item_ids=("qi_seen",),
            ),
            delivery_mode="telegram",
            deterministic=True,
            selection_strategy="weighted_policy",
            consumer_profile=ConsumerProfile("consumer_allowed", "telegram"),
            target_mix=SelectionTargetMix(theme_weights={"T10": 1.0}),
        )

        self.assertEqual(request.filters.cefr_level, "A2")
        self.assertEqual(request.cefr_level, "A2")
        self.assertEqual(request.theme_ids, ("T10",))
        self.assertEqual(request.excluded_item_ids, ("qi_seen",))
        self.assertEqual(request.delivery_mode, "telegram")
        self.assertTrue(request.deterministic)
        self.assertEqual(request.selection_strategy, "weighted_policy")
        self.assertEqual(request.consumer_profile.delivery_channel, "telegram")
        self.assertEqual(request.target_mix.theme_weights, {"T10": 1.0})

    def test_selection_request_keeps_legacy_filter_fields_compatible(self) -> None:
        request = SelectionRequest(
            consumer_id="consumer_allowed",
            cefr_level="A2",
            theme_ids=("T10",),
        )

        self.assertEqual(request.filters.cefr_level, "A2")
        self.assertEqual(request.filters.theme_ids, ("T10",))
        self.assertEqual(request.consumer_profile.delivery_channel, "api")

    def test_selection_request_rejects_mixed_filter_contracts(self) -> None:
        with self.assertRaisesRegex(ValueError, "filters or legacy"):
            SelectionRequest(
                consumer_id="consumer_allowed",
                filters=SelectionFilters(cefr_level="A2"),
                cefr_level="B1",
            )

    def test_no_eligible_context_exposes_selection_contract_metadata(self) -> None:
        policy = SelectionPolicy(repeat_policy=RepeatPolicy(repeat_window_days=14))
        request = SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            delivery_mode="telegram",
            deterministic=True,
            selection_strategy="weighted_policy",
            policy=policy,
            target_mix=SelectionTargetMix(theme_weights={"T10": 1.0}),
        )

        context = no_eligible_problem(request).extra["selection_context"]

        self.assertEqual(context["delivery_mode"], "telegram")
        self.assertTrue(context["deterministic"])
        self.assertEqual(context["selection_strategy"], "weighted_policy")
        self.assertEqual(context["policy"]["repeat_policy"]["repeat_window_days"], 14)
        self.assertIn("SELECTION_CHANNEL_CYCLE_EXHAUSTED", context["fallback_reason_codes"])
        self.assertEqual(context["consumer_profile"]["delivery_channel"], "telegram")
        self.assertEqual(context["target_mix"]["theme_weights"], {"T10": 1.0})
        self.assertEqual(
            context["filters"],
            {
                "cefr_level": "A2",
                "theme_ids": ["T10"],
                "objective_ids": [],
                "pattern_ids": [],
                "excluded_item_ids": [],
                "language_code": "de",
                "content_bank_id": None,
                "bank_version_id": None,
            },
        )
        self.assertEqual(context["content_scope"]["language_code"], "de")

    def test_repeat_policy_rejects_negative_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            RepeatPolicy(repeat_window_days=-1)


if __name__ == "__main__":
    unittest.main()
