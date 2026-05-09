from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.projections import admin_quiz_projection, learner_quiz_projection


TRACEABLE_ITEM = {
    "item_id": "approved_traceable_001",
    "language": "de",
    "sublevel": "A2",
    "theme_id": "T10",
    "objective_id": "O02",
    "pattern_id": "P01",
    "status": "approved",
    "prompt": "Welche Ergänzung passt hier am besten?",
    "stem_text": "Ich muss morgen einen Termin ___.",
    "options_json": '["buchen", "trinken"]',
    "source_id": "src_control_mvp",
    "resolved_source_type": "fixture_approved_source",
    "resolved_provenance_note": "control_selection_fixture:approved_traceable",
}


class MvpProjectionTests(unittest.TestCase):
    def test_learner_quiz_projection_is_display_ready_and_public_safe(self) -> None:
        projection = learner_quiz_projection(TRACEABLE_ITEM)

        self.assertEqual(projection["id"], "approved_traceable_001")
        self.assertEqual(
            projection["question"]["text"],
            "Welche Ergänzung passt hier am besten?\nIch muss morgen einen Termin ___.",
        )
        self.assertEqual(
            projection["options"][0],
            {"id": "option_1", "position": 1, "text": "buchen"},
        )
        self.assertEqual(projection["theme"]["title"], "Termine / Formulare / Behörden / Recht")
        hidden_fields = {"source_traceability", "theme_id", "objective_id", "pattern_id"}
        self.assertFalse(hidden_fields & projection.keys())

    def test_admin_quiz_projection_keeps_traceability_fields(self) -> None:
        projection = admin_quiz_projection(TRACEABLE_ITEM)

        self.assertEqual(projection["theme_id"], "T10")
        self.assertEqual(projection["source_traceability"]["source_id"], "src_control_mvp")


if __name__ == "__main__":
    unittest.main()
