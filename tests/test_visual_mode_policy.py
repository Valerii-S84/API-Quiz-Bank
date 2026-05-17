from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_mode_policy import resolve_visual_mode  # noqa: E402


class VisualModePolicyTests(unittest.TestCase):
    def test_household_visible_action_uses_target_action(self) -> None:
        mode = resolve_visual_mode(
            "action_001",
            "T03",
            "A2",
            "Was passt? Ich muss die Spuelmaschine ___.",
            "die Spülmaschine ausräumen",
            ["die Spülmaschine ausräumen", "das Formular"],
        )

        self.assertEqual(mode, "target_action")

    def test_concrete_object_answer_uses_target_object(self) -> None:
        mode = resolve_visual_mode(
            "object_001",
            "T02",
            "A1",
            "Was ist wichtig?",
            "der Auftrag",
            ["der Auftrag", "laufen"],
        )

        self.assertEqual(mode, "target_object")

    def test_article_answer_uses_context_only(self) -> None:
        mode = resolve_visual_mode(
            "article_001",
            "T06",
            "A1",
            "Für das Team ist ___ Auftrag bis Freitag zu erledigen.",
            "der",
            ["den", "die", "der", "das"],
        )

        self.assertEqual(mode, "context_only")

    def test_adjective_ending_cloze_uses_context_only(self) -> None:
        mode = resolve_visual_mode(
            "adjective_001",
            "T09",
            "A2",
            "Sogar bei kritischen Kommentaren bleibt eine ___ Nachricht sachlich.",
            "ehrliche",
            ["ehrliche", "ehrlichen", "ehrlicher"],
        )

        self.assertEqual(mode, "context_only")

    def test_preposition_answer_uses_context_only(self) -> None:
        mode = resolve_visual_mode(
            "prep_001",
            "T01",
            "A1",
            "Das Kind kommt ___ Schule.",
            "aus",
            ["aus", "bei", "mit", "ohne"],
        )

        self.assertEqual(mode, "context_only")

    def test_form_contract_authority_question_uses_document_form(self) -> None:
        mode = resolve_visual_mode(
            "document_001",
            "T10",
            "B1",
            "Im Bürgeramt muss Lena ein Formular abgeben.",
            "das Formular",
            ["das Formular", "der Schlüssel"],
        )

        self.assertEqual(mode, "document_form")

    def test_abstract_theme_uses_symbolic_abstract(self) -> None:
        mode = resolve_visual_mode(
            "abstract_001",
            "T17",
            "C1",
            "Welche Folgerung passt in der öffentlichen Debatte?",
            "die Debatte einordnen",
            ["die Debatte einordnen", "den Bus nehmen"],
        )

        self.assertEqual(mode, "symbolic_abstract")

    def test_abstract_theme_grammar_answer_stays_context_only(self) -> None:
        mode = resolve_visual_mode(
            "abstract_context_001",
            "T18",
            "C1",
            "In der Analyse geht es ___ Argumentation.",
            "um",
            ["um", "bei", "nach"],
        )

        self.assertEqual(mode, "context_only")


if __name__ == "__main__":
    unittest.main()
