from __future__ import annotations

import sys
import unittest

from tests.repository_test_support import run_command


class DemoPackageTests(unittest.TestCase):
    def test_mvp_demo_prints_live_and_artifact_backed_proof_steps(self) -> None:
        result = run_command(sys.executable, "tools/run_mvp_demo.py")

        for step_name in [
            "source_governance",
            "canonical_validation",
            "analytics_snapshot",
            "billing_plan_catalog",
            "next_item",
            "learner_safe_projection",
            "selection_decision_metadata",
            "delivery_log",
            "telegram_payload",
            "runtime_analytics_snapshot",
            "repeat_denial",
            "quota_denial",
            "negative_controls",
            "billing_usage_audit",
        ]:
            self.assertIn(step_name, result.stdout)


if __name__ == "__main__":
    unittest.main()
