from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import (
    EXPECTED_HEADER,
    PARSER_PROFILE_ID,
    ROOT,
    file_sha256,
    file_texts,
    read_csv_dicts,
    run_command,
)
from quizbank_readme import build_readme  # noqa: E402


class GeneratedArtifactsInvariantTests(unittest.TestCase):
    def test_generated_readme_is_current(self) -> None:
        before = (ROOT / "QuizBank" / "README.md").read_text(encoding="utf-8")
        run_command(sys.executable, "tools/quizbank_readme.py")
        after = (ROOT / "QuizBank" / "README.md").read_text(encoding="utf-8")
        self.assertEqual(after, before)

    def test_generated_readme_snapshot_date_can_be_controlled(self) -> None:
        readme = build_readme(ROOT / "QuizBank", snapshot_date="2099-01-02")

        self.assertIn("- Snapshot date: `2099-01-02`", readme)

    def test_generated_inventory_artifacts_are_current(self) -> None:
        artifact_paths = [
            "data/manifests/file_inventory.csv",
            "data/manifests/source_checksums.csv",
            "data/manifests/import_manifest.yml",
            "data/parser_profiles/parser_profiles.yml",
        ]
        before = file_texts(artifact_paths)
        run_command(
            sys.executable,
            "tools/quizbank_inventory.py",
            "--quizbank-dir",
            "QuizBank",
            "--write-artifacts",
        )
        self.assertEqual(file_texts(artifact_paths), before)

    def test_generated_contract_artifacts_are_current(self) -> None:
        artifact_paths = [
            "api/openapi.yaml",
            "schemas/canonical_quiz_item.schema.json",
            "data/taxonomy/cefr_levels.csv",
            "data/taxonomy/themes.csv",
            "data/taxonomy/objectives.csv",
            "data/taxonomy/patterns.csv",
        ]
        before = file_texts(artifact_paths)
        run_command(sys.executable, "tools/quizbank_emit_standards.py")
        self.assertEqual(file_texts(artifact_paths), before)

    def test_control_sample_import_pipeline_is_current(self) -> None:
        artifact_paths = [
            "data/imports/control_sample_items.jsonl",
            "data/registry/source_registry.csv",
            "reports/imports/control_sample_import.json",
        ]
        before = file_texts(artifact_paths)
        run_command(sys.executable, "tools/quizbank_import_sample.py")
        self.assertEqual(file_texts(artifact_paths), before)
        self.assert_control_sample_registry()
        self.assert_control_sample_report()
        self.assert_control_sample_jsonl()

    def test_postgresql_load_plan_is_current(self) -> None:
        artifact_paths = ["reports/imports/control_sample_postgresql_load_plan.json"]
        before = file_texts(artifact_paths)
        run_command(sys.executable, "tools/quizbank_postgresql_load_plan.py")
        self.assertEqual(file_texts(artifact_paths), before)

    def assert_control_sample_registry(self) -> None:
        registry_rows = read_csv_dicts("data/registry/source_registry.csv")
        self.assertEqual(len(registry_rows), 1)
        self.assertEqual(registry_rows[0]["source_state"], "dry_run_passed")
        self.assertEqual(registry_rows[0]["parser_profile_id"], PARSER_PROFILE_ID)
        self.assertEqual(registry_rows[0]["row_count_detected"], "2")
        self.assertEqual(
            registry_rows[0]["checksum_sha256"],
            file_sha256(ROOT / "tests/fixtures/control_source/control_sample.csv"),
        )

    def assert_control_sample_report(self) -> None:
        report = json.loads((ROOT / "reports/imports/control_sample_import.json").read_text())
        self.assertEqual(report["import_mode"], "dry_run")
        self.assertEqual(
            report["content_scope"],
            {
                "language_code": "de",
                "content_bank_id": "german-core",
                "bank_version_id": "german-core:control-sample-draft",
                "bank_version": "control-sample-draft",
                "bank_version_status": "draft",
            },
        )
        self.assertEqual(report["row_count_detected"], 2)
        self.assertEqual(report["canonical_output_path"], "data/imports/control_sample_items.jsonl")
        self.assertEqual(report["validation_summary"]["canonical_item_count"], 2)
        self.assertEqual(report["validation_summary"]["accepted_candidate_count"], 2)
        self.assertEqual(report["validation_summary"]["rejected_candidate_count"], 0)
        self.assertEqual(report["validation_summary"]["publishable_item_count"], 0)
        self.assertEqual(report["validation_summary"]["validation_errors"], [])
        self.assertEqual(len(report["imported_items"]), 2)
        self.assertEqual(report["imported_items"][0]["language_code"], "de")
        self.assertEqual(report["imported_items"][0]["bank_version_id"], "german-core:control-sample-draft")
        self.assertNotIn("answer_key", report["imported_items"][0])

    def assert_control_sample_jsonl(self) -> None:
        canonical_lines = (ROOT / "data/imports/control_sample_items.jsonl").read_text().splitlines()
        canonical_items = [json.loads(line) for line in canonical_lines]
        self.assertEqual(len(canonical_items), 2)
        self.assertTrue(all(item["status"] == "draft" for item in canonical_items))
        self.assertTrue(all(set(item) == set(EXPECTED_HEADER) for item in canonical_items))


if __name__ == "__main__":
    unittest.main()
