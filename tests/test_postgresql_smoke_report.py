from __future__ import annotations

import json
import unittest

from tests.repository_test_support import ROOT


SMOKE_REPORT_PATH = ROOT / "reports" / "imports" / "control_sample_postgresql_smoke.json"


class PostgreSQLSmokeReportTests(unittest.TestCase):
    def test_smoke_report_proves_schema_and_load_plan_execution(self) -> None:
        report = json.loads(SMOKE_REPORT_PATH.read_text(encoding="utf-8"))
        checks = report["checks"]

        self.assertEqual(report["report_type"], "postgresql_contract_smoke")
        self.assertEqual(report["docker_image"], "postgres:16-alpine")
        self.assertTrue(checks["schema_applied"])
        self.assertTrue(checks["load_plan_applied"])
        self.assertTrue(checks["source_checksum_match"])
        self.assertEqual(checks["lineage_join_count"], 2)
        self.assertEqual(
            checks["counts"],
            {
                "import_batch_items": 2,
                "import_batches": 1,
                "import_validation_results": 0,
                "quiz_items": 2,
                "sources": 1,
            },
        )

    def test_smoke_report_points_to_committed_contract_artifacts(self) -> None:
        report = json.loads(SMOKE_REPORT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(
            report["schema_files"],
            [
                "database/postgresql/001_create_runtime.sql",
                "database/postgresql/002_add_import_contract.sql",
                "database/postgresql/003_add_runtime_delivery_evidence.sql",
            ],
        )
        self.assertEqual(
            report["source_artifacts"],
            {
                "canonical_input_path": "data/imports/control_sample_items.jsonl",
                "load_plan_path": "reports/imports/control_sample_postgresql_load_plan.json",
            },
        )


if __name__ == "__main__":
    unittest.main()
