from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings
from quizbank_mvp.visual_prompt_builder import build_visual_prompt


class VisualPromptBuilderTests(unittest.TestCase):
    def test_direct_vocabulary_prompt_does_not_include_option_labels(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(pattern_id="vocab_noun"), self.settings())

        self.assertIn("direct_vocabulary", prompt.generated_prompt)
        self.assertNotIn("A)", prompt.generated_prompt)
        self.assertNotIn("Option", prompt.generated_prompt)

    def test_grammar_prompt_avoids_exact_answer_text(self) -> None:
        item = self.quiz_item(pattern_id="grammar_gap", stem_text="Ich muss morgen einen Termin ___.")

        prompt = build_visual_prompt(item, self.settings())

        self.assertIn("context_scene", prompt.generated_prompt)
        self.assertNotIn("buchen", prompt.generated_prompt.lower())
        self.assertEqual(prompt.answer_leak_risk, "avoid_exact_answer")

    def test_branded_prompt_includes_preset_marker_without_private_payload(self) -> None:
        settings = self.settings(
            mode=VisualDeliveryMode.IMAGE_BRANDED,
            branding_preset="brand_alpha",
        )

        prompt = build_visual_prompt(self.quiz_item(), settings)

        self.assertIn("brand_alpha", prompt.generated_prompt)
        self.assertNotIn("secret", prompt.generated_prompt.lower())

    def test_unsupported_abstract_prompt_recommends_text_fallback(self) -> None:
        item = self.quiz_item(pattern_id="abstract_reasoning")

        prompt = build_visual_prompt(item, self.settings())

        self.assertEqual(prompt.visualization_type, "unsupported_abstract")
        self.assertEqual(prompt.fallback_recommendation, "text_only")

    def test_prompt_builder_is_deterministic_for_same_inputs(self) -> None:
        item = self.quiz_item()
        settings = self.settings()

        first = build_visual_prompt(item, settings)
        second = build_visual_prompt(item, settings)

        self.assertEqual(first, second)
        self.assertEqual(first.prompt_policy_version, "visual_prompt_policy_v1")

    def settings(
        self,
        mode: VisualDeliveryMode = VisualDeliveryMode.IMAGE_STANDARD,
        branding_preset: str = "none",
    ) -> VisualSettings:
        return VisualSettings(
            consumer_id="consumer_visual",
            delivery_mode=mode,
            visual_style="standard_illustration",
            branding_preset=branding_preset,
            fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
            daily_visual_delivery_limit=3,
            daily_generation_limit=3,
            monthly_generation_limit=10,
            is_active=True,
        )

    def quiz_item(self, pattern_id: str = "vocab_noun", stem_text: str = "Was ist das?") -> dict[str, str]:
        return {
            "item_id": "quiz_visual_001",
            "language": "de",
            "sublevel": "A2",
            "theme_id": "T10",
            "pattern_id": pattern_id,
            "prompt": "Choose the correct word",
            "stem_text": stem_text,
            "options_json": "[\"buchen\", \"trinken\", \"lesen\", \"oeffnen\"]",
            "answer_key": "0",
        }


if __name__ == "__main__":
    unittest.main()
