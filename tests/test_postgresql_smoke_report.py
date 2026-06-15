from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import ROOT

sys.path.insert(0, str(ROOT))

from tools.run_postgresql_contract_smoke import quiz_item_insert_sql  # noqa: E402


SMOKE_REPORT_PATH = ROOT / "reports" / "imports" / "control_sample_postgresql_smoke.json"
POSTGRESQL_SCHEMA_DIRECTORY = ROOT / "database" / "postgresql"
PRECOMPUTED_SELECTION_TABLES = [
    "candidate_pools",
    "candidate_pool_items",
    "consumer_delivery_state",
    "selection_queues",
    "selection_queue_items",
    "selection_diagnostic_events",
    "selection_diagnostic_outbox",
]


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
        self.assertEqual(
            checks["precomputed_selection_counts"],
            {table_name: 0 for table_name in PRECOMPUTED_SELECTION_TABLES},
        )

    def test_smoke_report_points_to_committed_contract_artifacts(self) -> None:
        report = json.loads(SMOKE_REPORT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(
            report["schema_files"],
            expected_schema_files(),
        )
        self.assertEqual(
            report["source_artifacts"],
            {
                "canonical_input_path": "data/imports/control_sample_items.jsonl",
                "load_plan_path": "reports/imports/control_sample_postgresql_load_plan.json",
            },
        )

    def test_smoke_loader_renders_options_as_jsonb_literal(self) -> None:
        sql = quiz_item_insert_sql("source_fixture", minimal_quiz_item())

        self.assertIn("'[\"a\", \"b\"]'::jsonb", sql)
        self.assertNotIn("'''[", sql)


def expected_schema_files() -> list[str]:
    return [
        f"database/postgresql/{path.name}"
        for path in sorted(POSTGRESQL_SCHEMA_DIRECTORY.glob("*.sql"))
    ]


def minimal_quiz_item() -> dict[str, str]:
    return {
        "item_id": "item_fixture",
        "language": "de",
        "language_code": "de",
        "content_bank_id": "german-core",
        "bank_version_id": "german-core:control-sample-draft",
        "level_band": "A",
        "sublevel": "A2",
        "theme_id": "T10",
        "subtheme_id": "ST01",
        "objective_id": "O02",
        "pattern_id": "P01",
        "difficulty_band": "easy",
        "register": "neutral",
        "prompt": "prompt",
        "stem_text": "stem",
        "options": "[\"a\", \"b\"]",
        "answer_key": "a",
        "explanation": "because",
        "tags": "fixture",
        "coverage_cell_id": "A2::T10::O02::P01",
        "status": "draft",
        "version": "1",
        "created_at": "2026-05-07T00:00:00+00:00",
        "updated_at": "2026-05-07T00:00:00+00:00",
        "reviewed_at": "",
        "level_locked": "false",
        "locked_at": "",
    }


if __name__ == "__main__":
    unittest.main()
