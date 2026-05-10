from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import ROOT, file_texts, run_command


REPORT_PATH = "reports/compliance/legal_privacy_gate_2026-05-10.json"


class LegalPrivacyGateTests(unittest.TestCase):
    def test_legal_privacy_gate_report_is_current(self) -> None:
        before = file_texts([REPORT_PATH])
        run_command(sys.executable, "tools/quizbank_legal_privacy_gate.py")
        self.assertEqual(before, file_texts([REPORT_PATH]))

        report = json.loads((ROOT / REPORT_PATH).read_text(encoding="utf-8"))
        self.assertEqual(report["report_type"], "legal_privacy_gate")
        self.assertEqual(report["approved_scope"], "owner-operated protected production API runtime")
        self.assertIn("school deployment", report["blocked_scopes"])
        self.assertGreaterEqual(report["evidence"]["retention_data_families"], 10)
        self.assertIn("vendor_backup", report["evidence"]["pending_vendor_ids"])
        self.assertTrue(report["checks"]["deletion_export_workflow_exists"])
        self.assertIn(
            "exact public customer legal entity and jurisdiction are not finalized",
            report["production_legal_privacy_blockers"],
        )


if __name__ == "__main__":
    unittest.main()
