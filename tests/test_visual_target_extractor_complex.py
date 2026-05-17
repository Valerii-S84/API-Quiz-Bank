from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_target_extractor import extract_visual_target  # noqa: E402


class VisualTargetExtractorComplexTests(unittest.TestCase):
    def test_article_and_preposition_cloze_targets_near_blank(self) -> None:
        examples = [
            ("Für das Team ist ___ Auftrag bis Freitag zu erledigen.", "der", "Auftrag"),
            ("Ich fülle ___ Formular aus.", "das", "Formular"),
            ("Der Mieter unterschreibt ___ Vertrag.", "den", "Vertrag"),
            ("Sie wartet an ___ Haltestelle.", "der", "Haltestelle"),
            ("Wir sprechen mit ___ Vermieter.", "dem", "Vermieter"),
        ]
        for question, answer, expected in examples:
            with self.subTest(question=question):
                result = extract_visual_target(question, answer, "context_only", [answer])

                self.assertEqual(result.visual_target, expected)
                self.assertNotEqual(result.visual_target.lower(), answer.lower())
                self.assertFalse(result.is_answer_directly_visualizable)

    def test_action_targets_keep_verb_phrase(self) -> None:
        actions = [
            "die Spülmaschine ausräumen",
            "das Fenster öffnen",
            "den Bus nehmen",
            "einen Termin vereinbaren",
            "eine E-Mail schreiben",
            "das Formular ausfüllen",
        ]
        for action in actions:
            with self.subTest(action=action):
                result = extract_visual_target("Was passt?", action, "target_action", [action])

                self.assertEqual(result.visual_target, action)
                self.assertTrue(result.is_answer_directly_visualizable)

    def test_document_form_extracts_document_noun(self) -> None:
        examples = [
            ("das Formular", "Formular"),
            ("der Antrag", "Antrag"),
            ("die Kündigung", "Kündigung"),
            ("der Vertrag", "Vertrag"),
            ("die Rechnung", "Rechnung"),
            ("die E-Mail", "E-Mail"),
        ]
        for answer, expected in examples:
            with self.subTest(answer=answer):
                result = extract_visual_target("Dokument im Büro.", answer, "document_form", [answer])

                self.assertEqual(result.visual_target, expected)
                self.assertEqual(result.reason_code, "document_form_anchor")


if __name__ == "__main__":
    unittest.main()
