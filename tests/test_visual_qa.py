from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings
from quizbank_mvp.visual_prompt_builder import build_visual_prompt
from quizbank_mvp.visual_provider import ImageGenerationResult
from quizbank_mvp.visual_qa import evaluate_visual_qa


class VisualQATests(unittest.TestCase):
    def test_approved_image_passes_deterministic_checks(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(pattern_id="vocab_noun"), self.settings())

        decision = evaluate_visual_qa(prompt, self.result(), self.quiz_item(pattern_id="vocab_noun"), self.settings())

        self.assertEqual(decision.qa_status, "approved")
        self.assertEqual(decision.reason_code, "QA_APPROVED")

    def test_empty_image_bytes_are_rejected(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(), self.settings())
        result = self.result(image_bytes=b"")

        decision = evaluate_visual_qa(prompt, result, self.quiz_item(), self.settings())

        self.assertEqual(decision.qa_status, "rejected")
        self.assertEqual(decision.reason_code, "EMPTY_IMAGE_BYTES")

    def test_wrong_mime_type_is_rejected(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(), self.settings())
        result = self.result(mime_type="image/gif")

        decision = evaluate_visual_qa(prompt, result, self.quiz_item(), self.settings())

        self.assertEqual(decision.reason_code, "UNSUPPORTED_MIME_TYPE")

    def test_answer_grounded_prompt_is_allowed_when_image_has_no_text_surface(self) -> None:
        item = self.quiz_item(pattern_id="grammar_gap", stem_text="Ich muss ___.")
        prompt = build_visual_prompt(item, self.settings())

        decision = evaluate_visual_qa(prompt, self.result(), item, self.settings())

        self.assertEqual(decision.reason_code, "QA_APPROVED")

    def test_non_16x9_image_is_rejected(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(), self.settings())

        decision = evaluate_visual_qa(prompt, self.result(width=1024, height=1024), self.quiz_item(), self.settings())

        self.assertEqual(decision.reason_code, "IMAGE_ASPECT_RATIO_INVALID")

    def test_resolved_scene_visualization_is_approved(self) -> None:
        item = self.quiz_item(pattern_id="dialogue", prompt="Respond to this situation")
        prompt = build_visual_prompt(item, self.settings())

        decision = evaluate_visual_qa(prompt, self.result(), item, self.settings())

        self.assertEqual(decision.qa_status, "approved")
        self.assertEqual(decision.reason_code, "QA_APPROVED")

    def test_abstract_item_is_approved_after_answer_grounded_prompting(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(pattern_id="abstract_reasoning"), self.settings())

        decision = evaluate_visual_qa(prompt, self.result(), self.quiz_item(), self.settings())

        self.assertEqual(decision.qa_status, "approved")
        self.assertEqual(decision.reason_code, "QA_APPROVED")

    def settings(self) -> VisualSettings:
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

    def quiz_item(
        self,
        pattern_id: str = "vocab_noun",
        stem_text: str = "Was ist das?",
        prompt: str = "Choose the correct word",
    ) -> dict[str, str]:
        return {
            "item_id": "quiz_visual_001",
            "language": "de",
            "sublevel": "A2",
            "theme_id": "T10",
            "pattern_id": pattern_id,
            "prompt": prompt,
            "stem_text": stem_text,
            "options_json": "[\"buchen\", \"trinken\", \"lesen\", \"oeffnen\"]",
            "answer_key": "0",
        }

    def result(self, **overrides: object) -> ImageGenerationResult:
        values = {
            "provider_name": "fake",
            "provider_model": "fake-image-v1",
            "provider_response_id": "fake_response",
            "revised_prompt": "",
            "image_bytes": b"\x89PNG\r\n\x1a\nfake",
            "mime_type": "image/png",
            "width": 1536,
            "height": 864,
            "usage": {},
        }
        values.update(overrides)
        return ImageGenerationResult(**values)


if __name__ == "__main__":
    unittest.main()
