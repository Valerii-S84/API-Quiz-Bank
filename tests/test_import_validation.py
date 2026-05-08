from __future__ import annotations

import copy
import unittest

from tests.repository_test_support import EXPECTED_HEADER
from quizbank_import_sample import validate_source


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
    "provenance_note": "negative import validation control",
    "coverage_cell_id": "A2_T10_O02_P01",
    "status": "draft",
}


def valid_row(**overrides: str) -> dict[str, str]:
    row = copy.deepcopy(VALID_ROW)
    row.update(overrides)
    return row


class ImportValidationTests(unittest.TestCase):
    def test_rejects_header_mismatch(self) -> None:
        errors = validate_source(EXPECTED_HEADER[:-1], [valid_row()])

        self.assertIn("header_mismatch", errors)

    def test_rejects_duplicate_item_id_and_non_draft_status(self) -> None:
        rows = [valid_row(status="approved"), valid_row(status="draft")]

        errors = validate_source(EXPECTED_HEADER, rows)

        self.assertIn("non_draft_sample_item:2:approved", errors)
        self.assertIn("duplicate_item_id:sample_control_valid", errors)

    def test_rejects_invalid_options_and_answer_key(self) -> None:
        rows = [
            valid_row(item_id="invalid_options", options='["one"]'),
            valid_row(item_id="invalid_answer", answer_key="99"),
        ]

        errors = validate_source(EXPECTED_HEADER, rows)

        self.assertIn("invalid_options_shape:2", errors)
        self.assertIn("answer_key_out_of_bounds:3:99", errors)


if __name__ == "__main__":
    unittest.main()
