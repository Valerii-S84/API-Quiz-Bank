from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import (
    CANONICAL_LEVELS,
    NORMAL_DELIVERY_STATUSES,
    ROOT,
    THEME_TITLES,
    file_texts,
    run_command,
)


COVERAGE_CELL_FIELDS = {
    "cefr_level",
    "primary_theme_id",
    "objective_id",
    "pattern_id",
    "item_count_total",
    "item_count_draft",
    "item_count_approved",
    "item_count_published",
    "item_count_retired",
    "item_count_blocked",
    "coverage_status",
    "last_generated_at",
}


class ReportsSelectionInvariantTests(unittest.TestCase):
    def test_coverage_report_is_current(self) -> None:
        before = file_texts(["reports/coverage/corpus_coverage.json"])
        run_command(
            sys.executable,
            "tools/quizbank_gap_map.py",
            "--quizbank-dir",
            "QuizBank",
            "--write-artifacts",
        )
        self.assertEqual(file_texts(["reports/coverage/corpus_coverage.json"]), before)
        self.assert_coverage_report_payload()

    def assert_coverage_report_payload(self) -> None:
        report = json.loads((ROOT / "reports/coverage/corpus_coverage.json").read_text())
        self.assertEqual(report["report_type"], "coverage")
        self.assertEqual(report["source"]["active_bank_files"], 115)
        self.assertEqual(report["source"]["active_rows"], 30974)
        self.assertEqual(report["status_counts"]["draft"], 30974)
        self.assertEqual(report["status_counts"]["published"], 0)
        self.assertEqual(
            report["gap_summary"]["level_theme_total_cells"],
            len(CANONICAL_LEVELS) * len(THEME_TITLES),
        )
        self.assertEqual(len(report["level_theme_matrix"]), 108)
        self.assertGreater(len(report["coverage_cells"]), 0)
        self.assertEqual(set(report["coverage_cells"][0]), COVERAGE_CELL_FIELDS)

    def test_selection_smoke_report_is_current(self) -> None:
        before = file_texts(["reports/delivery/control_selection_report.json"])
        run_command(sys.executable, "tools/quizbank_selection_smoke.py")
        self.assertEqual(file_texts(["reports/delivery/control_selection_report.json"]), before)

        report = json.loads((ROOT / "reports/delivery/control_selection_report.json").read_text())
        self.assertEqual(report["report_type"], "selection_smoke")
        self.assertEqual(
            report["selection_request"]["normal_delivery_statuses"],
            list(NORMAL_DELIVERY_STATUSES),
        )
        self.assertEqual(report["diagnostics"]["candidate_count"], 2)
        self.assertEqual(report["diagnostics"]["eligible_count"], 0)
        self.assertEqual(report["diagnostics"]["rejected_by_status"], {"draft": 2})
        self.assertEqual(report["problem_details"]["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")

    def test_approved_selection_report_is_current(self) -> None:
        before = file_texts(["reports/delivery/control_approved_selection_report.json"])
        run_command(
            sys.executable,
            "tools/quizbank_selection_smoke.py",
            "--canonical-input",
            "tests/fixtures/selection/approved_traceable_items.jsonl",
            "--report-out",
            "reports/delivery/control_approved_selection_report.json",
        )
        self.assertEqual(file_texts(["reports/delivery/control_approved_selection_report.json"]), before)
        self.assert_approved_selection_payload()

    def assert_approved_selection_payload(self) -> None:
        report = json.loads(
            (ROOT / "reports/delivery/control_approved_selection_report.json").read_text()
        )
        self.assertEqual(report["diagnostics"]["eligible_count"], 1)
        self.assertEqual(report["diagnostics"]["rejected_by_status"], {})
        self.assertEqual(report["diagnostics"]["traceability_violations"], [])
        self.assertTrue(report["delivery_created"])
        self.assertEqual(report["selected_item"]["item_id"], "approved_traceable_001")
        self.assertNotIn("answer_key", report["selected_item"])
        self.assertNotIn("explanation", report["selected_item"])
        self.assertEqual(report["delivery_log"]["item_status"], "approved")

    def test_repeat_policy_report_is_current(self) -> None:
        before = file_texts(["reports/delivery/control_repeat_policy_report.json"])
        run_command(
            sys.executable,
            "tools/quizbank_selection_smoke.py",
            "--canonical-input",
            "tests/fixtures/selection/approved_traceable_items.jsonl",
            "--delivery-history",
            "reports/delivery/control_approved_selection_report.json",
            "--report-out",
            "reports/delivery/control_repeat_policy_report.json",
        )
        self.assertEqual(file_texts(["reports/delivery/control_repeat_policy_report.json"]), before)
        self.assert_repeat_policy_payload()

    def assert_repeat_policy_payload(self) -> None:
        report = json.loads((ROOT / "reports/delivery/control_repeat_policy_report.json").read_text())
        self.assertEqual(report["diagnostics"]["candidate_count"], 1)
        self.assertEqual(report["diagnostics"]["eligible_count"], 0)
        self.assertEqual(report["diagnostics"]["excluded_by_repeat_count"], 1)
        self.assertEqual(
            report["diagnostics"]["excluded_by_repeat_item_ids"],
            ["approved_traceable_001"],
        )
        self.assertTrue(report["selection_request"]["repeat_policy"]["applied"])
        self.assertIsNone(report["selected_item"])
        self.assertFalse(report["delivery_created"])
        self.assertIsNone(report["delivery_log"])
        self.assertEqual(report["problem_details"]["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertIn(
            "repeat_policy",
            report["problem_details"]["selection_context"]["filters_applied"],
        )


if __name__ == "__main__":
    unittest.main()
