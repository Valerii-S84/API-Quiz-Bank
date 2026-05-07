from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


class RepositoryInvariantTests(unittest.TestCase):
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
        inventory_path = ROOT / "data" / "manifests" / "file_inventory.csv"
        checksum_path = ROOT / "data" / "manifests" / "source_checksums.csv"
        self.assertTrue(inventory_path.exists())
        self.assertTrue(checksum_path.exists())

        with inventory_path.open(encoding="utf-8", newline="") as file:
            inventory_rows = list(csv.DictReader(file))
        with checksum_path.open(encoding="utf-8", newline="") as file:
            checksum_rows = list(csv.DictReader(file))

        active_rows = [row for row in inventory_rows if row["source_state"] == "active"]
        template_rows = [row for row in inventory_rows if row["source_state"] == "template"]
        self.assertEqual(len(active_rows), 115)
        self.assertEqual(len(template_rows), 1)
        self.assertEqual(sum(int(row["row_count_detected"]) for row in active_rows), 30974)
        self.assertEqual(len(checksum_rows), len(inventory_rows))

    def test_taxonomy_and_contract_artifacts_exist(self) -> None:
        required_paths = [
            "README.md",
            "LICENSE",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "CODEOWNERS",
            ".github/CODEOWNERS",
            "data/taxonomy/cefr_levels.csv",
            "data/taxonomy/themes.csv",
            "data/taxonomy/objectives.csv",
            "data/taxonomy/patterns.csv",
            "schemas/canonical_quiz_item.schema.json",
            "api/openapi.yaml",
            "data/parser_profiles/parser_profiles.yml",
            "data/manifests/import_manifest.yml",
        ]
        for relative_path in required_paths:
            self.assertTrue((ROOT / relative_path).exists(), relative_path)

        schema = json.loads((ROOT / "schemas/canonical_quiz_item.schema.json").read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("item_id", schema["required"])
        self.assertIn("/v1/quiz-items/next", (ROOT / "api/openapi.yaml").read_text())

    def test_documented_baseline_has_no_stale_counts(self) -> None:
        paths = [ROOT / "CONSTITUTION.md", *sorted((ROOT / "docs").glob("*.md"))]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        self.assertNotIn("84 active bank files", combined)
        self.assertNotIn("21,674", combined)
        self.assertIn("115 active bank files", combined)
        self.assertIn("30,974 active rows/items", combined)

    def test_generated_readme_is_current(self) -> None:
        before = (ROOT / "QuizBank" / "README.md").read_text(encoding="utf-8")
        run_command(sys.executable, "tools/quizbank_readme.py")
        after = (ROOT / "QuizBank" / "README.md").read_text(encoding="utf-8")
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
