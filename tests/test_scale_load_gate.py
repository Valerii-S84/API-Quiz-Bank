from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import ROOT, file_texts, run_command


REPORT_PATH = "reports/scale/protected_runtime_load_smoke_2026-05-10.json"


class ScaleLoadGateTests(unittest.TestCase):
    def test_scale_load_smoke_report_is_current(self) -> None:
        before = file_texts([REPORT_PATH])
        run_command(sys.executable, "tools/run_mvp_load_smoke.py")
        self.assertEqual(before, file_texts([REPORT_PATH]))

        report = json.loads((ROOT / REPORT_PATH).read_text(encoding="utf-8"))
        self.assertEqual(report["report_type"], "protected_runtime_load_smoke")
        self.assertEqual(report["concurrent_consumers"], 8)
        self.assertEqual(report["status_counts"], {"200": 8})
        self.assertEqual(report["ready_status"], 200)
        self.assertEqual(report["auth_no_key_status"], 401)
        self.assertEqual(report["repeat_selection_status"], 404)
        self.assertEqual(report["quota_denial_status"], 429)
        self.assertTrue(all(report["resource_limits"].values()))
        self.assertIn("external concurrent traffic test is not executed", report["scale_blockers"])


if __name__ == "__main__":
    unittest.main()
