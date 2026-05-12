from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import (
    CANONICAL_LEVELS,
    ITEM_STATUSES,
    NORMAL_DELIVERY_STATUSES,
    ROOT,
    THEME_TITLES,
    file_texts,
    run_command,
)


REPORT_PATH = "reports/publication/production_corpus_gate_2026-05-11.json"


class ProductionCorpusGateTests(unittest.TestCase):
    def test_production_corpus_gate_report_is_current(self) -> None:
        before = file_texts([REPORT_PATH])

        run_command(
            sys.executable,
            "tools/quizbank_production_corpus_gate.py",
            "--quizbank-dir",
            "QuizBank",
            "--write-artifacts",
        )

        self.assertEqual(before, file_texts([REPORT_PATH]))
        self.assert_production_corpus_gate_payload()

    def assert_production_corpus_gate_payload(self) -> None:
        report = json.loads((ROOT / REPORT_PATH).read_text(encoding="utf-8"))
        snapshot = report["approved_published_snapshot"]

        self.assertEqual(report["report_type"], "production_corpus_gate")
        self.assertEqual(report["decision"], "GO production corpus volume")
        self.assertEqual(report["source"]["active_bank_files"], 115)
        self.assertEqual(report["source"]["active_rows"], 30974)
        self.assertEqual(report["status_counts"]["draft"], 0)
        self.assertEqual(report["status_counts"]["published"], 30974)
        self.assertEqual(set(report["status_counts"]), set(ITEM_STATUSES))
        self.assertEqual(snapshot["statuses"], list(NORMAL_DELIVERY_STATUSES))
        self.assertEqual(snapshot["item_count"], 30974)
        self.assertEqual(set(snapshot["level_counts"]), set(CANONICAL_LEVELS))
        self.assertEqual(set(snapshot["theme_counts"]), set(THEME_TITLES))
        self.assertGreater(len(snapshot["coverage_cells"]), 0)
        self.assertEqual(report["production_content_blockers"], [])
        self.assertTrue(report["owner_approval"]["valid_for_current_row_count"])
        self.assertTrue(report["postgresql_content_proof"]["valid_for_deliverable_count"])
        self.assertEqual(
            report["negative_controls"]["non_deliverable_statuses"],
            ["draft", "blocked", "retired"],
        )


if __name__ == "__main__":
    unittest.main()
