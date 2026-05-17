from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_target_extractor import (  # noqa: E402
    extract_visual_target,
    non_visual_answer_token,
)


class VisualTargetExtractorTests(unittest.TestCase):
    def test_article_answer_extracts_noun_anchor_instead_of_article(self) -> None:
        result = extract_visual_target(
            "Für das Team ist ___ Auftrag bis Freitag zu erledigen.",
            "der",
            "context_only",
            ["den", "die", "der", "das"],
        )

        self.assertEqual(result.visual_target, "Auftrag")
        self.assertFalse(result.is_answer_directly_visualizable)
        self.assertEqual(result.reason_code, "non_visual_answer_context_anchor")

    def test_preposition_answer_extracts_connected_noun_anchor(self) -> None:
        result = extract_visual_target(
            "Das Kind kommt ___ Schule.",
            "aus",
            "context_only",
            ["aus", "bei", "mit", "ohne"],
        )

        self.assertEqual(result.visual_target, "Schule")
        self.assertFalse(result.is_answer_directly_visualizable)

    def test_visible_action_answer_remains_direct_visual_target(self) -> None:
        result = extract_visual_target(
            "Ich muss die Spülmaschine ___.",
            "die Spülmaschine ausräumen",
            "target_action",
            ["die Spülmaschine ausräumen"],
        )

        self.assertEqual(result.visual_target, "die Spülmaschine ausräumen")
        self.assertTrue(result.is_answer_directly_visualizable)

    def test_document_form_extracts_document_anchor_from_action_answer(self) -> None:
        result = extract_visual_target(
            "Im Portal ist der Antrag fertig.",
            "den Antrag abgeben",
            "document_form",
            ["den Antrag abgeben"],
        )

        self.assertEqual(result.visual_target, "Antrag")
        self.assertEqual(result.reason_code, "document_form_anchor")

    def test_non_visual_answer_dictionary_covers_core_grammar_tokens(self) -> None:
        for answer in ["der", "die", "das", "in", "auf", "an", "und", "nicht", "ich"]:
            with self.subTest(answer=answer):
                self.assertTrue(non_visual_answer_token(answer))


if __name__ == "__main__":
    unittest.main()
