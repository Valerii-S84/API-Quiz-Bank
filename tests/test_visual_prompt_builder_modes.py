from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_prompt_builder import build_visual_prompt  # noqa: E402


class VisualPromptBuilderModesTests(unittest.TestCase):
    def test_a1_prompt_contains_scene_limits(self) -> None:
        prompt = build_visual_prompt(
            quiz_item("T02", "A1", "Was passt?", "Ich muss ___.", ["das Fenster öffnen"]),
            settings(),
        )

        self.assertIn("one clear focal object or one clear focal action", prompt.generated_prompt)
        self.assertIn("max two people preferred", prompt.generated_prompt)
        self.assertIn("no readable text", prompt.generated_prompt)
        self.assertIn("no clutter", prompt.generated_prompt)
        self.assertIn("Avoid extra background story", prompt.generated_prompt)
        self.assertIn("decorative props", prompt.generated_prompt)

    def test_document_form_prompt_contains_document_guards(self) -> None:
        prompt = build_visual_prompt(
            quiz_item("T10", "A2", "Was passt?", "Im Amt liegt das Formular.", ["das Formular"]),
            settings(),
        )

        self.assertEqual(prompt.visual_mode, "document_form")
        self.assertIn("No readable text, numbers", prompt.generated_prompt)
        self.assertIn("calendar grids", prompt.generated_prompt)
        self.assertIn("no calendar wall", prompt.negative_prompt)
        self.assertIn("no whiteboard words", prompt.negative_prompt)

    def test_symbolic_abstract_prompt_contains_neutral_symbolic_guards(self) -> None:
        prompt = build_visual_prompt(
            quiz_item("T17", "C1", "Welche Folgerung passt?", "Die Debatte wird ___.", ["die Debatte analysieren"]),
            settings(),
        )

        self.assertEqual(prompt.visual_mode, "symbolic_abstract")
        self.assertIn("one symbolic scene with one semantic center", prompt.generated_prompt)
        self.assertIn("Avoid political campaigning", prompt.generated_prompt)
        self.assertIn("brands", prompt.generated_prompt)
        self.assertIn("no political propaganda", prompt.negative_prompt)
        self.assertIn("no brand logos", prompt.negative_prompt)


def settings() -> VisualSettings:
    return VisualSettings(
        consumer_id="consumer_visual",
        delivery_mode=VisualDeliveryMode.IMAGE_STANDARD,
        visual_style="standard_illustration",
        branding_preset="none",
        fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
        daily_visual_delivery_limit=3,
        daily_generation_limit=3,
        monthly_generation_limit=10,
        is_active=True,
    )


def quiz_item(theme_id: str, level: str, prompt: str, stem: str, options: list[str]) -> dict[str, str]:
    return {
        "item_id": "prompt_modes",
        "language": "de",
        "sublevel": level,
        "theme_id": theme_id,
        "pattern_id": "P01",
        "prompt": prompt,
        "stem_text": stem,
        "options_json": str(options).replace("'", '"'),
        "answer_key": "0",
    }


if __name__ == "__main__":
    unittest.main()
