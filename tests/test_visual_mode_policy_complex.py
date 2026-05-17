from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_mode_policy import resolve_visual_mode  # noqa: E402
from quizbank_mvp.visual_target_extractor import extract_visual_target  # noqa: E402


GRAMMAR_TOKENS = [
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einen",
    "einem",
    "einer",
    "in",
    "an",
    "auf",
    "zu",
    "mit",
    "für",
    "von",
    "bei",
    "nach",
    "ich",
    "du",
    "er",
    "sie",
    "es",
    "wir",
    "ihr",
    "weil",
    "dass",
    "obwohl",
    "wenn",
    "aber",
    "oder",
    "nicht",
    "kein",
    "keine",
    "keinen",
]


class VisualModePolicyComplexTests(unittest.TestCase):
    def test_grammar_tokens_do_not_become_visual_targets(self) -> None:
        question = "Heute ist ___ Auftrag im Team wichtig."
        for token in GRAMMAR_TOKENS:
            with self.subTest(token=token):
                mode = resolve_visual_mode("grammar", "T06", "A1", question, token, GRAMMAR_TOKENS)
                target = extract_visual_target(question, token, mode, GRAMMAR_TOKENS)

                self.assertIn(mode, {"context_only", "document_form"})
                self.assertNotEqual(target.visual_target.lower(), token.lower())

    def test_visible_actions_route_to_target_action(self) -> None:
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
                mode = resolve_visual_mode("action", "T02", "A2", "Was passt?", action, [action])

                self.assertEqual(mode, "target_action")

    def test_concrete_objects_route_to_target_object(self) -> None:
        objects = ["der Schlüssel", "die Rechnung", "das Ticket", "die Tasche", "der Ausweis", "das Handy"]
        for answer in objects:
            with self.subTest(answer=answer):
                mode = resolve_visual_mode("object", "T02", "A1", "Was ist im Alltag wichtig?", answer, [answer])

                self.assertEqual(mode, "target_object")

    def test_document_theme_keywords_route_to_document_form(self) -> None:
        examples = [
            ("T03", "der Vertrag"),
            ("T09", "die E-Mail"),
            ("T10", "das Formular"),
            ("T15", "die Rechnung"),
            ("T10", "der Antrag"),
            ("T03", "die Kündigung"),
        ]
        for theme_id, answer in examples:
            with self.subTest(theme_id=theme_id, answer=answer):
                mode = resolve_visual_mode("document", theme_id, "B1", "Was passt zum Dokument?", answer, [answer])

                self.assertEqual(mode, "document_form")

    def test_abstract_themes_avoid_unjustified_action_mode(self) -> None:
        examples = [
            ("T13", "Integration bewerten"),
            ("T16", "die Forschung einordnen"),
            ("T17", "die Debatte analysieren"),
            ("T18", "das Argument interpretieren"),
        ]
        allowed = {"symbolic_abstract", "context_only", "document_form"}
        for theme_id, answer in examples:
            with self.subTest(theme_id=theme_id):
                mode = resolve_visual_mode("abstract", theme_id, "C1", "Welche Folgerung passt?", answer, [answer])

                self.assertIn(mode, allowed)
                self.assertNotEqual(mode, "target_action")


if __name__ == "__main__":
    unittest.main()
