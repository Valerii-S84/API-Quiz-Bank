from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.run_pre_pilot_dry_run import run_dry_run


class PrePilotRuntimeInvariantTests(unittest.TestCase):
    def test_local_pre_pilot_dry_run_covers_required_controls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "pre_pilot_report.md"
            report = run_dry_run(report_path)
            report_text = report_path.read_text(encoding="utf-8")

        lifecycle = report["consumer_lifecycle"]
        self.assertEqual(lifecycle["states"], ["active", "suspended", "blocked", "active"])
        self.assertEqual(lifecycle["suspended_denial"]["reason_code"], "CONSUMER_NOT_ACTIVE")
        self.assertEqual(lifecycle["blocked_denial"]["reason_code"], "CONSUMER_NOT_ACTIVE")
        self.assertEqual(lifecycle["reactivated_allowed"]["status_code"], 200)
        self.assertTrue(lifecycle["reactivated_allowed"]["delivery_created"])
        self.assertEqual(report["repeat_behavior"]["reason_code"], "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(report["quota_behavior"]["reason_code"], "QUOTA_EXCEEDED")
        self.assertEqual(
            report["audit_summary"]["consumer_transitions"],
            ["active->suspended", "suspended->blocked", "blocked->active"],
        )
        self.assertEqual(report["audit_summary"]["delivery_count"], 1)
        self.assertIn("consumer_status_transition", report["observability_events"])
        self.assertTrue(report_text.startswith("# Local Pre-Pilot"))


if __name__ == "__main__":
    unittest.main()
