from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests.repository_test_support import EXPECTED_HEADER, ROOT
from quizbank_import_sample import ImportContentScope, validate_source
from quizbank_postgresql_load_plan import (
    LoadPlanError,
    build_load_plan,
    runtime_item_id,
    validate_content_scope,
)


VALID_ROW = {
    "item_id": "sample_control_valid",
    "language": "de",
    "level_band": "A2",
    "sublevel": "A2",
    "theme_id": "T10",
    "subtheme_id": "T10_admin_docs",
    "objective_id": "O02",
    "pattern_id": "P01",
    "difficulty_band": "core",
    "register": "neutral",
    "prompt": "Welche Ergänzung passt hier am besten?",
    "stem_text": "Ich muss morgen einen Termin ___.",
    "options": '["buchen","trinken","lesen","öffnen"]',
    "answer_key": "0",
    "explanation": "buchen passt zu Termin.",
    "tags": "fixture",
    "source_type": "fixture_control_source",
    "provenance_note": "import scope control",
    "coverage_cell_id": "A2_T10_O02_P01",
    "status": "draft",
    "version": "1.0",
    "created_at": "2026-05-07T00:00:00Z",
    "updated_at": "2026-05-07T00:00:00Z",
    "reviewed_at": "",
    "level_locked": "false",
    "locked_at": "",
}


class MultilingualBankImportFlowTests(unittest.TestCase):
    def test_non_production_english_load_plan_targets_draft_version(self) -> None:
        row = valid_row(item_id="stage6_en_001", language="en")
        with tempfile.TemporaryDirectory() as directory:
            report_path, canonical_path = write_import_artifacts(
                Path(directory),
                [row],
                ImportContentScope(
                    language_code="en",
                    content_bank_id="english-core",
                    bank_version_id="english-core:stage6-draft",
                    bank_version="stage6-draft",
                    bank_version_status="draft",
                ),
            )

            plan = build_load_plan(report_path, canonical_path)

        batch = plan["tables"]["import_batches"][0]
        version = plan["tables"]["content_bank_versions"][0]
        self.assertEqual(plan["content_scope"]["language_code"], "en")
        self.assertEqual(batch["content_bank_id"], "english-core")
        self.assertEqual(batch["bank_version_id"], "english-core:stage6-draft")
        self.assertEqual(version["status"], "draft")
        self.assertIsNone(version["activated_at"])

    def test_import_batch_requires_language_code(self) -> None:
        scope = ImportContentScope().as_report()
        del scope["language_code"]

        with self.assertRaises(LoadPlanError) as error:
            validate_content_scope(scope, [valid_row()])

        self.assertIn("missing_content_scope_fields:language_code", str(error.exception))

    def test_import_batch_language_must_match_content_bank_language(self) -> None:
        scope = ImportContentScope(
            language_code="en",
            content_bank_id="german-core",
        ).as_report()

        with self.assertRaises(LoadPlanError) as error:
            validate_content_scope(scope, [valid_row(language="en")])

        self.assertIn("content_bank_language_mismatch:german-core:de!=en", str(error.exception))

    def test_import_source_rejects_mixed_language_batch(self) -> None:
        rows = [
            valid_row(item_id="stage6_en_001", language="en"),
            valid_row(item_id="stage6_de_001", language="de"),
        ]

        errors = validate_source(EXPECTED_HEADER, rows, language_code="en")

        self.assertIn("language_scope_mismatch:3:de!=en", errors)

    def test_import_source_rejects_rows_outside_batch_language(self) -> None:
        row = valid_row(language="en")

        errors = validate_source(EXPECTED_HEADER, [row], language_code="de")

        self.assertIn("language_scope_mismatch:2:en!=de", errors)

    def test_import_content_scope_rejects_active_target_versions(self) -> None:
        scope = ImportContentScope(bank_version_status="active").as_report()

        with self.assertRaises(LoadPlanError) as error:
            validate_content_scope(scope, [valid_row()])

        self.assertIn("invalid_import_bank_version_status:active", str(error.exception))

    def test_control_sample_load_plan_carries_batch_scope(self) -> None:
        plan = build_load_plan(
            ROOT / "reports/imports/control_sample_import.json",
            ROOT / "data/imports/control_sample_items.jsonl",
        )
        batch = plan["tables"]["import_batches"][0]
        batch_item = plan["tables"]["import_batch_items"][0]
        version = plan["tables"]["content_bank_versions"][0]

        self.assertEqual(plan["content_scope"]["language_code"], "de")
        self.assertEqual(batch["content_bank_id"], "german-core")
        self.assertEqual(batch["bank_version_id"], "german-core:control-sample-draft")
        self.assertEqual(version["status"], "draft")
        self.assertEqual(batch_item["language_code"], "de")
        self.assertEqual(batch_item["source_item_id"], "control_sample_001")
        self.assertEqual(
            batch_item["item_id"],
            runtime_item_id("german-core:control-sample-draft", "control_sample_001"),
        )


def valid_row(**overrides: str) -> dict[str, str]:
    row = copy.deepcopy(VALID_ROW)
    row.update(overrides)
    return row


def write_import_artifacts(
    directory: Path,
    rows: list[dict[str, str]],
    content_scope: ImportContentScope,
) -> tuple[Path, Path]:
    report_path = directory / "stage6_import.json"
    canonical_path = directory / "stage6_items.jsonl"
    report_path.write_text(
        json.dumps(import_report(rows, canonical_path, content_scope), ensure_ascii=False),
        encoding="utf-8",
    )
    canonical_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    return report_path, canonical_path


def import_report(
    rows: list[dict[str, str]],
    canonical_path: Path,
    content_scope: ImportContentScope,
) -> dict[str, object]:
    return {
        "import_mode": "dry_run",
        "source_id": "stage6_english_sample",
        "source_path": "tests/fixtures/control_source/stage6_english_sample.csv",
        "parser_profile_id": "csv_quiz_bank_v1",
        "checksum_sha256": "0" * 64,
        "content_scope": content_scope.as_report(),
        "row_count_detected": len(rows),
        "canonical_output_path": canonical_path.as_posix(),
        "validation_summary": {
            "canonical_item_count": len(rows),
            "accepted_candidate_count": len(rows),
            "rejected_candidate_count": 0,
            "validation_errors": [],
        },
        "generated_at": "2026-06-13T00:00:00Z",
    }


if __name__ == "__main__":
    unittest.main()
