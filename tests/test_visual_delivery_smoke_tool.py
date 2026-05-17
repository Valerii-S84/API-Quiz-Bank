from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_TOOL = ROOT / "tools" / "run_visual_delivery_smoke.py"


class VisualDeliverySmokeToolTests(unittest.TestCase):
    def test_cache_hit_scenario_reports_cache_metrics(self) -> None:
        report = run_smoke("--scenario", "cache-hit")

        self.assertEqual(report["scenario"], "cache-hit")
        self.assertEqual(report["resolution"]["state"], "cache_hit")
        self.assertEqual(report["metrics"]["event_counts"]["cache_hit"], 1)
        self.assertEqual(quota_used(report, "visual_delivery.standard"), 1)

    def test_provider_failure_scenario_reports_text_fallback(self) -> None:
        report = run_smoke("--scenario", "provider-failure")

        self.assertEqual(report["scenario"], "provider-failure")
        self.assertEqual(report["resolution"]["state"], "fallback_used")
        self.assertEqual(report["resolution"]["fallback_reason"], "GENERATION_FAILED")
        self.assertEqual(report["metrics"]["event_counts"]["generation_failed"], 1)
        self.assertEqual(quota_used(report, "visual_generation.standard"), 1)

    def test_text_only_scenario_preserves_text_only_resolution(self) -> None:
        report = run_smoke("--scenario", "text-only")

        self.assertEqual(report["scenario"], "text-only")
        self.assertEqual(report["resolution"]["state"], "text_only")
        self.assertEqual(report["metrics"]["event_counts"], {})
        self.assertEqual(report["quota_usage"], [])


def run_smoke(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SMOKE_TOOL), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=30,
    )
    return json.loads(result.stdout)


def quota_used(report: dict[str, object], feature: str) -> int:
    rows = [
        row for row in report["quota_usage"]
        if row["feature"] == feature and len(row["usage_date"]) == 10
    ]
    return 0 if not rows else int(rows[0]["used_count"])


if __name__ == "__main__":
    unittest.main()
