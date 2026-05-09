from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.projections import (
    build_admin_quiz_projection,
    build_learner_quiz_projection,
    build_telegram_quiz_projection,
    public_prompt,
)


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
    "explanation": "Internal answer explanation is retained in canonical data only.",
    "source_id": "src_control_mvp",
    "resolved_source_type": "fixture_approved_source",
    "resolved_provenance_note": "control_selection_fixture:approved_traceable",
}


class MvpProjectionTests(unittest.TestCase):
    def test_learner_quiz_projection_is_display_ready_and_public_safe(self) -> None:
        projection = build_learner_quiz_projection(TRACEABLE_ITEM)

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
        self.assertEqual(projection["theme"]["slug"], "termine-formulare-behoerden-recht")
        self.assertEqual(projection["objective"]["title"], "Objective O02")
        self.assertEqual(projection["pattern"]["title"], "Pattern P01")
        self.assertEqual(
            projection["metadata"]["display"],
            {
                "cefr_level": "A2",
                "theme_title": "Termine / Formulare / Behörden / Recht",
                "theme_slug": "termine-formulare-behoerden-recht",
                "objective_title": "Objective O02",
                "pattern_title": "Pattern P01",
            },
        )
        hidden_fields = {"source_traceability", "theme_id", "objective_id", "pattern_id"}
        self.assertFalse(hidden_fields & projection.keys())

    def test_telegram_quiz_projection_omits_technical_taxonomy_ids(self) -> None:
        projection = build_telegram_quiz_projection(TRACEABLE_ITEM)

        self.assertEqual(
            projection["question"],
            "Welche Ergänzung passt hier am besten?\nIch muss morgen einen Termin ___.",
        )
        hidden_fields = {"theme_id", "objective_id", "pattern_id", "metadata"}
        self.assertFalse(hidden_fields & projection.keys())

    def test_public_prompt_redacts_wrapped_internal_prompt_keys(self) -> None:
        cases = [
            "a1_klein_kommentar_nom_def_1",
            "a1_klein_kommentar_nom_def_1?",
            "`a1_klein_kommentar_nom_def_1`",
            "*a1_klein_kommentar_nom_def_1*",
        ]

        for prompt in cases:
            self.assertEqual(public_prompt(prompt), "")

    def test_public_prompt_keeps_human_text_with_underscores(self) -> None:
        prompt = "Setze _bitte_ passend ein."

        self.assertEqual(public_prompt(prompt), prompt)

    def test_unknown_taxonomy_ids_fall_back_to_public_safe_labels(self) -> None:
        projection = build_learner_quiz_projection(
            {
                **TRACEABLE_ITEM,
                "theme_id": "T99",
                "objective_id": "O99",
                "pattern_id": "P99",
            }
        )

        self.assertEqual(projection["theme"]["title"], "Unknown theme")
        self.assertEqual(projection["theme"]["slug"], "unknown-theme")
        self.assertEqual(projection["objective"]["title"], "Unknown objective")
        self.assertEqual(projection["pattern"]["title"], "Unknown pattern")

    def test_admin_quiz_projection_keeps_traceability_fields(self) -> None:
        projection = build_admin_quiz_projection(TRACEABLE_ITEM)

        self.assertEqual(projection["theme_id"], "T10")
        self.assertEqual(projection["source_traceability"]["source_id"], "src_control_mvp")


if __name__ == "__main__":
    unittest.main()
