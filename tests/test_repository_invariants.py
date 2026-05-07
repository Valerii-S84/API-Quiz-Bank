from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from quizbank_common import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    PARSER_PROFILE_ID,
    file_sha256,
)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def read_csv_dicts(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def parse_import_manifest_sources() -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    current_source: dict[str, str] | None = None
    manifest_path = ROOT / "data" / "manifests" / "import_manifest.yml"

    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - source_id: "):
            if current_source is not None:
                sources.append(current_source)
            current_source = {"source_id": line.split(": ", 1)[1]}
        elif current_source is not None and line.startswith("    "):
            key, value = line.strip().split(": ", 1)
            current_source[key] = value

    if current_source is not None:
        sources.append(current_source)
    return sources


def file_texts(relative_paths: list[str]) -> dict[str, str]:
    return {
        relative_path: (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in relative_paths
    }


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
            source_id = source["source_id"]
            inventory_row = active_inventory[source_id]
            checksum_row = checksums[source_id]
            self.assertEqual(source["path"], inventory_row["path"])
            self.assertEqual(source["parser_profile_id"], PARSER_PROFILE_ID)
            self.assertEqual(source["source_state"], "active")
            self.assertEqual(source["default_status"], "draft")
            self.assertEqual(source["checksum_sha256"], checksum_row["checksum"])
            self.assertEqual(source["checksum_sha256"], inventory_row["checksum_sha256"])
            self.assertEqual(source["row_count_detected"], inventory_row["row_count_detected"])

    def test_json_schema_matches_canonical_header_contract(self) -> None:
        schema = json.loads((ROOT / "schemas/canonical_quiz_item.schema.json").read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], EXPECTED_HEADER)
        self.assertEqual(list(schema["properties"].keys()), EXPECTED_HEADER)
        self.assertEqual(schema["properties"]["language"], {"type": "string", "const": "de"})
        self.assertEqual(schema["properties"]["sublevel"]["enum"], list(CANONICAL_LEVELS))
        self.assertEqual(schema["properties"]["status"]["enum"], list(ITEM_STATUSES))

    def test_openapi_seed_preserves_public_delivery_boundary(self) -> None:
        openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("openapi: 3.1.0", openapi)
        self.assertIn("/v1/quiz-items/next:", openapi)
        self.assertIn("NextQuizRequest:", openapi)
        self.assertIn("QuizItemPublicProjection:", openapi)
        self.assertIn("ProblemDetails:", openapi)

        public_projection = openapi.split("QuizItemPublicProjection:", 1)[1].split(
            "ProblemDetails:", 1
        )[0]
        self.assertIn("options:", public_projection)
        self.assertNotIn("answer_key", public_projection)
        self.assertNotIn("explanation", public_projection)

    def test_taxonomy_and_contract_artifacts_exist(self) -> None:
        required_paths = [
            "README.md",
            "LICENSE",
            "policies/license_policy.md",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "CODEOWNERS",
            ".github/CODEOWNERS",
            ".github/pull_request_template.md",
            ".github/ISSUE_TEMPLATE/docs_change.md",
            ".github/ISSUE_TEMPLATE/corpus_change.md",
            ".github/ISSUE_TEMPLATE/tooling_change.md",
            ".github/ISSUE_TEMPLATE/security_change.md",
            "data/taxonomy/cefr_levels.csv",
            "data/taxonomy/themes.csv",
            "data/taxonomy/objectives.csv",
            "data/taxonomy/patterns.csv",
            "schemas/canonical_quiz_item.schema.json",
            "api/openapi.yaml",
            "data/parser_profiles/parser_profiles.yml",
            "data/manifests/import_manifest.yml",
            "data/registry/source_registry.csv",
            "reports/imports/control_sample_import.json",
            "tests/fixtures/control_source/control_sample.csv",
            "tools/quizbank_import_sample.py",
        ]
        for relative_path in required_paths:
            self.assertTrue((ROOT / relative_path).exists(), relative_path)

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
            "data/registry/source_registry.csv",
            "reports/imports/control_sample_import.json",
        ]
        before = file_texts(artifact_paths)
        run_command(sys.executable, "tools/quizbank_import_sample.py")
        self.assertEqual(file_texts(artifact_paths), before)

        registry_rows = read_csv_dicts("data/registry/source_registry.csv")
        self.assertEqual(len(registry_rows), 1)
        self.assertEqual(registry_rows[0]["source_state"], "dry_run_passed")
        self.assertEqual(registry_rows[0]["parser_profile_id"], PARSER_PROFILE_ID)
        self.assertEqual(registry_rows[0]["row_count_detected"], "2")
        self.assertEqual(
            registry_rows[0]["checksum_sha256"],
            file_sha256(ROOT / "tests/fixtures/control_source/control_sample.csv"),
        )

        report = json.loads((ROOT / "reports/imports/control_sample_import.json").read_text())
        self.assertEqual(report["import_mode"], "dry_run")
        self.assertEqual(report["row_count_detected"], 2)
        self.assertEqual(len(report["imported_items"]), 2)
        self.assertNotIn("answer_key", report["imported_items"][0])


if __name__ == "__main__":
    unittest.main()
