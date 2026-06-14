from __future__ import annotations

import json
import re
import sys
import unittest

from tests.repository_test_support import ROOT, file_texts, run_command


PLAN_PATH = "reports/imports/control_sample_postgresql_load_plan.json"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class PostgreSQLLoadPlanTests(unittest.TestCase):
    def test_control_sample_postgresql_load_plan_is_current(self) -> None:
        before = file_texts([PLAN_PATH])

        run_command(sys.executable, "tools/quizbank_postgresql_load_plan.py")

        self.assertEqual(file_texts([PLAN_PATH]), before)

    def test_load_plan_preserves_source_batch_item_lineage(self) -> None:
        plan = self.read_plan()
        tables = plan["tables"]
        source = tables["sources"][0]
        batch = tables["import_batches"][0]
        batch_items = tables["import_batch_items"]

        self.assertEqual(plan["plan_type"], "postgresql_load_plan")
        self.assertEqual(
            plan["lineage"]["traceability_chain"],
            [
                "content_bank_versions",
                "sources",
                "import_batches",
                "import_batch_items",
                "quiz_items",
                "deliveries",
            ],
        )
        self.assertEqual(plan["content_scope"]["language_code"], "de")
        self.assertEqual(plan["content_scope"]["content_bank_id"], "german-core")
        self.assertEqual(plan["content_scope"]["bank_version_id"], "german-core:control-sample-draft")
        self.assertEqual(source["source_id"], batch["source_id"])
        self.assertEqual(source["bank_version_id"], batch["bank_version_id"])
        self.assertEqual(batch["import_status"], "dry_run_passed")
        self.assertEqual(batch["row_count_detected"], 2)
        self.assertEqual(batch["accepted_candidate_count"], 2)
        self.assertEqual(batch["rejected_candidate_count"], 0)
        self.assertEqual(batch["report_uri"], "reports/imports/control_sample_import.json")
        self.assertEqual(len(batch_items), 2)
        self.assertEqual(
            {item["import_batch_id"] for item in batch_items},
            {batch["import_batch_id"]},
        )
        self.assertEqual({item["source_id"] for item in batch_items}, {source["source_id"]})
        self.assertEqual(
            {item["bank_version_id"] for item in batch_items},
            {"german-core:control-sample-draft"},
        )

    def test_load_plan_hashes_and_validation_rows_match_contract_shape(self) -> None:
        plan = self.read_plan()
        tables = plan["tables"]
        source = tables["sources"][0]
        batch = tables["import_batches"][0]
        batch_items = tables["import_batch_items"]
        bank_version = tables["content_bank_versions"][0]

        self.assertRegex(source["checksum_sha256"], SHA256_PATTERN)
        self.assertRegex(batch["source_checksum_sha256"], SHA256_PATTERN)
        self.assertEqual(source["checksum_sha256"], batch["source_checksum_sha256"])
        self.assertEqual(bank_version["id"], batch["bank_version_id"])
        self.assertEqual(bank_version["status"], "draft")
        self.assertTrue(all(item["canonical_status"] == "draft" for item in batch_items))
        self.assertTrue(
            all(SHA256_PATTERN.fullmatch(item["content_hash_sha256"]) for item in batch_items)
        )
        self.assertEqual([item["source_row_number"] for item in batch_items], [2, 3])
        self.assertEqual(tables["import_validation_results"], [])

    def read_plan(self) -> dict[str, object]:
        return json.loads((ROOT / PLAN_PATH).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
