"""Deterministic prompt construction for Visual Quiz Delivery."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .visual_models import VisualDeliveryMode, VisualSettings


PROMPT_POLICY_VERSION = "visual_prompt_policy_v2_answer_grounded"


@dataclass(frozen=True)
class VisualPrompt:
    generated_prompt: str
    negative_prompt: str
    visualization_type: str
    answer_leak_risk: str
    prompt_policy_version: str
    fallback_recommendation: str


def build_visual_prompt(quiz_item: dict[str, Any], settings: VisualSettings) -> VisualPrompt:
    visualization_type = classify_visualization(quiz_item)
    answer_leak_risk = classify_answer_leak_risk(quiz_item, visualization_type)
    grounding = visual_grounding_text(quiz_item, visualization_type)
    prompt_parts = [
        "Create one 16:9 clean educational illustration for a German language quiz.",
        "The image must be wordless: no letters, numbers, captions, labels, signs, screens, worksheets, speech bubbles, subtitles, or UI.",
        "Use the quiz context only as semantic grounding; never render any quiz text or answer text inside the image.",
        f"CEFR level: {quiz_item.get('sublevel') or quiz_item.get('cefr_level', '')}.",
        f"Theme: {quiz_item.get('theme_id', '')}.",
        f"Visualization type: {visualization_type}.",
        f"Semantic visual brief: {grounding}.",
        "Do not copy any word from the semantic brief into the image.",
        "Show only the concrete scene, object, action, person, place, or relationship implied by the correct answer.",
        f"Visual style: {settings.visual_style}.",
    ]
    if settings.delivery_mode == VisualDeliveryMode.IMAGE_BRANDED:
        prompt_parts.append(f"Branding preset marker: {settings.branding_preset}.")
    prompt_parts.append("The final image should contain no readable text at all.")
    return VisualPrompt(
        generated_prompt=" ".join(part for part in prompt_parts if part.strip()),
        negative_prompt=(
            "No embedded text, no letters, no numbers, no captions, no labels, no signs, "
            "no screens with text, no books with readable text, no worksheets, no answer labels, "
            "no option letters, no watermark, no quiz UI."
        ),
        visualization_type=visualization_type,
        answer_leak_risk=answer_leak_risk,
        prompt_policy_version=PROMPT_POLICY_VERSION,
        fallback_recommendation=fallback_recommendation(visualization_type, answer_leak_risk),
    )


def classify_visualization(quiz_item: dict[str, Any]) -> str:
    prompt = str(quiz_item.get("prompt", "")).lower()
    stem = str(quiz_item.get("stem_text", "")).lower()
    pattern_id = str(quiz_item.get("pattern_id", "")).lower()
    if "___" in stem or "ergänzung" in prompt or "grammar" in pattern_id:
        return "context_scene"
    if "meaning" in prompt or "bedeutet" in stem or "vocab" in pattern_id or "word" in prompt:
        return "answer_concept"
    return "resolved_quiz_scene"


def classify_answer_leak_risk(quiz_item: dict[str, Any], visualization_type: str) -> str:
    return "answer_grounded_no_text_rendering"


def fallback_recommendation(visualization_type: str, answer_leak_risk: str) -> str:
    return "none"


def question_context(quiz_item: dict[str, Any]) -> str:
    prompt = str(quiz_item.get("prompt", "")).strip()
    stem = str(quiz_item.get("stem_text", "")).strip()
    return " ".join(part for part in [prompt, stem] if part)


def visual_grounding_text(quiz_item: dict[str, Any], visualization_type: str) -> str:
    answer = answer_text(quiz_item).strip()
    resolved = resolved_question_text(quiz_item)
    if visualization_type == "answer_concept":
        return f"Depict the meaning of the correct answer as a concrete visual concept: {answer}"
    if visualization_type == "context_scene":
        return f"Depict the completed sentence as a natural scene without text: {resolved}"
    return f"Depict the situation implied by the solved quiz answer without text: {resolved}"


def resolved_question_text(quiz_item: dict[str, Any]) -> str:
    answer = answer_text(quiz_item).strip()
    stem = str(quiz_item.get("stem_text", "")).strip()
    prompt = str(quiz_item.get("prompt", "")).strip()
    if stem:
        resolved_stem = replace_blank_with_answer(stem, answer)
        if resolved_stem != stem:
            return resolved_stem
        return " ".join(part for part in [stem, f"Correct answer: {answer}"] if part)
    return " ".join(part for part in [prompt, f"Correct answer: {answer}"] if part)


def replace_blank_with_answer(text: str, answer: str) -> str:
    if not answer:
        return text
    return re.sub(r"_{3,}", answer, text)


def answer_text(quiz_item: dict[str, Any]) -> str:
    raw_options = quiz_item.get("options_json") or quiz_item.get("options") or []
    options = raw_options if isinstance(raw_options, list) else json.loads(str(raw_options))
    answer_key = int(str(quiz_item.get("answer_key", "0")))
    return str(options[answer_key])
