from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import image_quality_policy as policy  # noqa: E402
from quizbank_mvp.image_quality_repository import upsert_quiz_item_image_quality_policy  # noqa: E402
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings
from quizbank_mvp.visual_prompt_builder import build_visual_prompt, visual_target_text


class VisualPromptBuilderTests(unittest.TestCase):
    def test_visual_mode_prompt_does_not_include_option_labels(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(pattern_id="vocab_noun", stem_text="Was bedeutet buchen?"), self.settings())

        self.assertIn("Visual mode: target_action", prompt.generated_prompt)
        self.assertNotIn("A)", prompt.generated_prompt)
        self.assertNotIn("Option", prompt.generated_prompt)

    def test_context_only_prompt_uses_anchor_without_resolved_grammar_answer(self) -> None:
        item = self.quiz_item(
            pattern_id="artikel_gap",
            stem_text="Für das Team ist ___ Auftrag bis Freitag zu erledigen.",
            options_json="[\"den\", \"die\", \"der\", \"das\"]",
            answer_key="2",
        )

        prompt = build_visual_prompt(item, self.settings())

        self.assertIn("Visual mode: context_only", prompt.generated_prompt)
        self.assertIn("Visual target: Auftrag", prompt.generated_prompt)
        self.assertNotIn("der Auftrag", prompt.generated_prompt)
        self.assertEqual(prompt.answer_leak_risk, "answer_grounded_no_text_rendering")

    def test_prompt_strongly_forbids_rendering_text_inside_image(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(), self.settings())

        self.assertIn("The image must be wordless", prompt.generated_prompt)
        self.assertIn("Do not copy any word from the target", prompt.generated_prompt)
        self.assertIn("no readable text", prompt.generated_prompt)
        self.assertIn("No embedded text", prompt.negative_prompt)
        self.assertIn("no signs", prompt.negative_prompt)

    def test_prompt_requires_simple_focused_target_composition(self) -> None:
        prompt = build_visual_prompt(self.quiz_item(), self.settings())

        self.assertIn("Visual target: buchen", prompt.generated_prompt)
        self.assertIn("exactly one clear focal object or one clear focal action", prompt.generated_prompt)
        self.assertIn("A1/A2 scene limits", prompt.generated_prompt)
        self.assertIn("max three allowed", prompt.generated_prompt)
        self.assertIn("uncluttered", prompt.generated_prompt)
        self.assertIn("no calendars with numbers", prompt.generated_prompt)
        self.assertIn("no clutter", prompt.negative_prompt)
        self.assertIn("no more than three people", prompt.negative_prompt)

    def test_article_cloze_uses_noun_near_blank_as_visual_target(self) -> None:
        item = self.quiz_item(
            pattern_id="artikel_gap",
            stem_text="Für das Team ist ___ Auftrag bis Freitag zu erledigen.",
            options_json="[\"den\", \"die\", \"der\", \"das\"]",
            answer_key="2",
        )

        prompt = build_visual_prompt(item, self.settings())

        self.assertEqual(visual_target_text(item), "Auftrag")
        self.assertEqual(prompt.visual_mode, "context_only")
        self.assertIn("Visual target: Auftrag", prompt.generated_prompt)
        self.assertIn("Focal object/action: one clear blank work order or task document", prompt.generated_prompt)
        self.assertIn("object-only composition", prompt.generated_prompt)
        self.assertIn("no office room", prompt.generated_prompt)
        self.assertIn("no desk accessories", prompt.generated_prompt)
        self.assertIn("not the grammar token", prompt.generated_prompt)
        self.assertIn("no calendar wall", prompt.negative_prompt)
        self.assertIn("no pseudo-text", prompt.negative_prompt)
        self.assertIn("no desk clutter", prompt.negative_prompt)
        self.assertNotIn("Visual target: der", prompt.generated_prompt)

    def test_preposition_cloze_uses_connected_noun_as_visual_target(self) -> None:
        item = self.quiz_item(
            pattern_id="preposition_gap",
            stem_text="Das Kind kommt ___ Schule.",
            options_json="[\"aus\", \"bei\", \"mit\", \"ohne\"]",
            answer_key="0",
        )

        self.assertEqual(visual_target_text(item), "Schule")

    def test_visual_action_answer_stays_visual_target(self) -> None:
        item = self.quiz_item(pattern_id="grammar_gap", stem_text="Ich muss morgen einen Termin ___.")

        self.assertEqual(visual_target_text(item), "buchen")

    def test_document_form_prompt_uses_blank_document_constraints(self) -> None:
        item = self.quiz_item(
            pattern_id="document_context",
            stem_text="Im Bürgeramt liegt das Formular auf dem Tisch.",
            options_json="[\"das Formular\", \"der Schlüssel\"]",
            answer_key="0",
        )

        prompt = build_visual_prompt(item, self.settings())

        self.assertEqual(prompt.visual_mode, "document_form")
        self.assertEqual(prompt.visual_target, "Formular")
        self.assertIn("Prompt route document_form", prompt.generated_prompt)
        self.assertIn("blank or use only non-text placeholder lines", prompt.generated_prompt)
        self.assertIn("No readable text, numbers", prompt.generated_prompt)

    def test_branded_prompt_includes_preset_marker_without_private_payload(self) -> None:
        settings = self.settings(
            mode=VisualDeliveryMode.IMAGE_BRANDED,
            branding_preset="brand_alpha",
        )

        prompt = build_visual_prompt(self.quiz_item(), settings)

        self.assertIn("brand_alpha", prompt.generated_prompt)
        self.assertNotIn("secret", prompt.generated_prompt.lower())

    def test_abstract_prompt_still_gets_answer_grounded_visualization(self) -> None:
        item = self.quiz_item(pattern_id="abstract_reasoning", theme_id="T17")

        prompt = build_visual_prompt(item, self.settings())

        self.assertEqual(prompt.visualization_type, "symbolic_abstract")
        self.assertEqual(prompt.fallback_recommendation, "none")

    def test_prompt_builder_is_deterministic_for_same_inputs(self) -> None:
        item = self.quiz_item()
        settings = self.settings()

        first = build_visual_prompt(item, settings)
        second = build_visual_prompt(item, settings)

        self.assertEqual(first, second)
        self.assertEqual(first.prompt_policy_version, "visual_prompt_policy_v4_visual_modes")
        self.assertEqual(first.visual_prompt_policy_version, "visual_prompt_policy_v4_visual_modes")

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

    def quiz_item(
        self,
        pattern_id: str = "vocab_noun",
        stem_text: str = "Was ist das?",
        options_json: str = "[\"buchen\", \"trinken\", \"lesen\", \"oeffnen\"]",
        answer_key: str = "0",
        theme_id: str = "T10",
    ) -> dict[str, str]:
        return {
            "item_id": "quiz_visual_001",
            "language": "de",
            "sublevel": "A2",
            "theme_id": theme_id,
            "pattern_id": pattern_id,
            "prompt": "Choose the correct word",
            "stem_text": stem_text,
            "options_json": options_json,
            "answer_key": answer_key,
        }


class ImageQualityPolicyCoverageTests(unittest.TestCase):
    theme_groups = {"T01": "simple_visual", "T02": "situational", "T03": "abstract_complex"}

    def test_policy_fields_cover_override_and_level_normalization(self) -> None:
        fields = policy.enriched_image_quality_fields(
            {
                "item_id": "quiz_visual_001",
                "sublevel": "B2.1",
                "theme_id": "T03",
                "image_quality_override": "medium",
            },
            self.theme_groups,
        )

        self.assertEqual(fields["theme_group"], "abstract_complex")
        self.assertEqual(fields["image_quality_policy_share"], 40)
        self.assertEqual(fields["image_quality_recommended"], "medium")
        self.assertEqual(fields["image_quality_source"], "override")
        self.assertEqual(policy.medium_share_for("A1.2", "simple_visual"), 0)
        self.assertEqual(policy.medium_share_for("C2", "abstract_complex"), 60)
        policy.validate_policy_fields({"theme_id": "T03", **fields})

    def test_policy_validation_rejects_invalid_runtime_values(self) -> None:
        invalid_calls = [
            lambda: policy.resolve_image_quality_decision("quiz", "D1", "T01", theme_groups=self.theme_groups),
            lambda: policy.resolve_image_quality_decision("quiz", "A1", "T99", theme_groups=self.theme_groups),
            lambda: policy.resolve_image_quality_decision("quiz", "A1", "T01", "auto", self.theme_groups),
            lambda: policy.policy_quality_for("", 5),
            lambda: policy.policy_quality_for("quiz", 101),
            lambda: policy.validate_theme_group_coverage({"T01", "T02"}, {"T01": "simple_visual"}),
            lambda: policy.validate_theme_group_coverage({"T01"}, {"T01": "invalid"}),
            lambda: policy.validate_policy_fields(
                {
                    "theme_id": "T01",
                    "theme_group": "simple_visual",
                    "image_quality_recommended": "high",
                    "image_quality_source": "policy",
                    "image_quality_policy_share": 10,
                    "image_quality_override": None,
                }
            ),
        ]

        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(policy.ImageQualityPolicyError):
                    call()

    def test_theme_group_config_parser_is_strict(self) -> None:
        config = "theme_groups:\n  T01: simple_visual\n  T02: situational\n  T03: abstract_complex\n"

        self.assertEqual(policy.parse_theme_group_config(config), self.theme_groups)
        with self.assertRaises(policy.ImageQualityPolicyError):
            policy.parse_theme_group_config("theme_groups:\n  T01: simple_visual\n  T01: situational\n")
        with self.assertRaises(policy.ImageQualityPolicyError):
            policy.parse_theme_group_config("other:\n  T01: simple_visual\n")


class ImageQualityRepositoryCoverageTests(unittest.TestCase):
    def test_upsert_skips_absent_policy_and_writes_complete_policy(self) -> None:
        connection = RecordingConnection()

        upsert_quiz_item_image_quality_policy(connection, {"item_id": "quiz_visual_001"})
        self.assertEqual(connection.executed, [])

        upsert_quiz_item_image_quality_policy(
            connection,
            {
                "item_id": "quiz_visual_001",
                "theme_group": "situational",
                "image_quality_recommended": "low",
                "image_quality_source": "policy",
                "image_quality_policy_share": "20",
                "image_quality_override": "",
            },
        )

        self.assertEqual(len(connection.executed), 1)
        parameters = connection.executed[0][1]
        self.assertEqual(parameters["image_quality_policy_share"], 20)
        self.assertIsNone(parameters["image_quality_override"])
        self.assertIn("INSERT INTO quiz_item_image_quality_policy", connection.executed[0][0])

    def test_upsert_rejects_partial_policy_fields(self) -> None:
        with self.assertRaises(ValueError):
            upsert_quiz_item_image_quality_policy(
                RecordingConnection(),
                {"item_id": "quiz_visual_001", "theme_group": "situational"},
            )


class RecordingConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, parameters: dict[str, object]) -> None:
        self.executed.append((sql, parameters))
