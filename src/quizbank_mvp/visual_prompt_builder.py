"""Deterministic prompt construction for Visual Quiz Delivery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .visual_models import VisualDeliveryMode, VisualSettings


PROMPT_POLICY_VERSION = "visual_prompt_policy_v1"


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
    prompt_parts = [
        "Create a clean educational illustration for a German language quiz.",
        f"CEFR level: {quiz_item.get('sublevel') or quiz_item.get('cefr_level', '')}.",
        f"Theme: {quiz_item.get('theme_id', '')}.",
        f"Visualization type: {visualization_type}.",
        f"Question context: {question_context(quiz_item)}.",
        f"Visual style: {settings.visual_style}.",
    ]
    if settings.delivery_mode == VisualDeliveryMode.IMAGE_BRANDED:
        prompt_parts.append(f"Branding preset marker: {settings.branding_preset}.")
    prompt_parts.append("Do not render answer options, option letters, or UI labels.")
    return VisualPrompt(
        generated_prompt=" ".join(part for part in prompt_parts if part.strip()),
        negative_prompt="No embedded text, no answer labels, no option letters, no watermark.",
        visualization_type=visualization_type,
        answer_leak_risk=answer_leak_risk,
        prompt_policy_version=PROMPT_POLICY_VERSION,
        fallback_recommendation=fallback_recommendation(visualization_type, answer_leak_risk),
    )


def classify_visualization(quiz_item: dict[str, Any]) -> str:
    prompt = str(quiz_item.get("prompt", "")).lower()
    stem = str(quiz_item.get("stem_text", "")).lower()
    pattern_id = str(quiz_item.get("pattern_id", "")).lower()
    if "abstract" in pattern_id or "abstract" in prompt:
        return "unsupported_abstract"
    if "___" in stem or "ergänzung" in prompt or "grammar" in pattern_id:
        return "context_scene"
    if "vocab" in pattern_id or "word" in prompt:
        return "direct_vocabulary"
    return "neutral_learning"


def classify_answer_leak_risk(quiz_item: dict[str, Any], visualization_type: str) -> str:
    if visualization_type in {"context_scene", "unsupported_abstract"}:
        return "avoid_exact_answer"
    return "low"


def fallback_recommendation(visualization_type: str, answer_leak_risk: str) -> str:
    if visualization_type == "unsupported_abstract":
        return "text_only"
    if answer_leak_risk == "avoid_exact_answer":
        return "review_after_generation"
    return "none"


def question_context(quiz_item: dict[str, Any]) -> str:
    prompt = str(quiz_item.get("prompt", "")).strip()
    stem = str(quiz_item.get("stem_text", "")).strip()
    return " ".join(part for part in [prompt, stem] if part)


def answer_text(quiz_item: dict[str, Any]) -> str:
    raw_options = quiz_item.get("options_json") or quiz_item.get("options") or []
    options = raw_options if isinstance(raw_options, list) else json.loads(str(raw_options))
    answer_key = int(str(quiz_item.get("answer_key", "0")))
    return str(options[answer_key])
