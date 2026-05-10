from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import ROOT, file_texts, run_command


REPORT_PATH = "reports/release/release_governance_gate_2026-05-10.json"


class ReleaseGovernanceGateTests(unittest.TestCase):
    def test_release_governance_gate_report_is_current(self) -> None:
        before = file_texts([REPORT_PATH])
        run_command(sys.executable, "tools/quizbank_release_governance_gate.py")
        self.assertEqual(before, file_texts([REPORT_PATH]))

        report = json.loads((ROOT / REPORT_PATH).read_text(encoding="utf-8"))
        checks = report["checks"]
        self.assertEqual(report["protected_branch"], "main")
        self.assertEqual(report["required_ci_check"], "repository-invariants")
        self.assertTrue(checks["branch_protection_config_present"])
        self.assertTrue(checks["direct_push_blocked_in_desired_config"])
        self.assertTrue(checks["ci_runs_on_pull_request"])
        self.assertTrue(checks["pr_template_has_release_notes_prompt"])
        self.assertIn(
            "actual GitHub branch protection enforcement must be verified on remote",
            report["release_governance_blockers"],
        )


if __name__ == "__main__":
    unittest.main()
