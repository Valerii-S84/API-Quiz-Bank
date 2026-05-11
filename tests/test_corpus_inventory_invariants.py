from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import (
    PARSER_PROFILE_ID,
    ROOT,
    parse_import_manifest_sources,
    read_csv_dicts,
    run_command,
)


class CorpusInventoryInvariantTests(unittest.TestCase):
    def test_constitution_check_passes(self) -> None:
        result = run_command(
            sys.executable,
            "tools/quizbank_constitution_check.py",
            "--quizbank-dir",
            "QuizBank",
            "--format",
            "json",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["active_bank_files"], 115)
        self.assertEqual(payload["active_rows"], 30974)
        self.assertEqual(payload["violations"], 0)
        self.assertEqual(payload["breakdown"], {})

    def test_inventory_artifacts_match_current_corpus(self) -> None:
        inventory_rows = read_csv_dicts("data/manifests/file_inventory.csv")
        checksum_rows = read_csv_dicts("data/manifests/source_checksums.csv")

        active_rows = [row for row in inventory_rows if row["source_state"] == "active"]
        template_rows = [row for row in inventory_rows if row["source_state"] == "template"]
        self.assertEqual(len(active_rows), 115)
        self.assertEqual(len(template_rows), 1)
        self.assertEqual(sum(int(row["row_count_detected"]) for row in active_rows), 30974)
        self.assertEqual(len(checksum_rows), len(inventory_rows))

    def test_import_manifest_matches_active_inventory(self) -> None:
        inventory_rows = read_csv_dicts("data/manifests/file_inventory.csv")
        checksum_rows = read_csv_dicts("data/manifests/source_checksums.csv")
        manifest_sources = parse_import_manifest_sources()

        active_inventory = {
            row["source_id"]: row
            for row in inventory_rows
            if row["source_state"] == "active"
        }
        checksums = {row["source_id"]: row for row in checksum_rows}
        self.assertEqual(len(manifest_sources), len(active_inventory))

        for source in manifest_sources:
            inventory_row = active_inventory[source["source_id"]]
            checksum_row = checksums[source["source_id"]]
            self.assertEqual(source["path"], inventory_row["path"])
            self.assertEqual(source["parser_profile_id"], PARSER_PROFILE_ID)
            self.assertEqual(source["source_state"], "active")
            self.assertEqual(source["default_status"], "published")
            self.assertEqual(source["checksum_sha256"], checksum_row["checksum"])
            self.assertEqual(source["checksum_sha256"], inventory_row["checksum_sha256"])
            self.assertEqual(source["row_count_detected"], inventory_row["row_count_detected"])

    def test_documented_baseline_has_no_stale_counts(self) -> None:
        paths = [ROOT / "CONSTITUTION.md", *sorted((ROOT / "docs").glob("*.md"))]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        self.assertNotIn("84 active bank files", combined)
        self.assertNotIn("21,674", combined)
        self.assertIn("115 active bank files", combined)
        self.assertIn("30,974 active rows/items", combined)


if __name__ == "__main__":
    unittest.main()
