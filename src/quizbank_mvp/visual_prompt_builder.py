"""Deterministic prompt construction for Visual Quiz Delivery."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any

from .visual_mode_policy import resolve_visual_mode
from .visual_models import VisualDeliveryMode, VisualSettings
from .visual_target_extractor import (
    VisualTargetResolution,
    extract_visual_target,
    non_visual_answer_token,
    normalize_token,
)


PROMPT_POLICY_VERSION = "visual_prompt_policy_v4_visual_modes"
VISUAL_TARGET_DESCRIPTIONS = {
    "auftrag": "one clear blank work order or task document as the only main object",
    "formular": "one blank form sheet or official form folder as the only main object",
    "rechnung": "one blank invoice-like document with no readable text or numbers",
    "vertrag": "one blank contract-like document or folder with no readable text",
}
VISUAL_TARGET_CONSTRAINTS = {
    "auftrag": (
        "For this target, use an object-only composition: one blank work order or task document, "
        "no office room, no desk accessories, no calendars, no clocks, no plants, no phone, no cup."
    ),
}


@dataclass(frozen=True)
class VisualPrompt:
    generated_prompt: str
    negative_prompt: str
    visualization_type: str
    answer_leak_risk: str
    prompt_policy_version: str
    fallback_recommendation: str
    visual_mode: str
    visual_target: str
    visual_context_hint: str
    visual_prompt_policy_version: str


def build_visual_prompt(quiz_item: dict[str, Any], settings: VisualSettings) -> VisualPrompt:
    options = options_from_item(quiz_item)
    answer = answer_text(quiz_item, options)
    context = question_context(quiz_item)
    visual_mode = resolve_visual_mode(
        str(quiz_item.get("item_id", "")),
        str(quiz_item.get("theme_id", "")),
        str(quiz_item.get("sublevel") or quiz_item.get("cefr_level", "")),
        context,
        answer,
        options,
    )
    target = extract_visual_target(context, answer, visual_mode, options)
    prompt_parts = common_prompt_parts(quiz_item, visual_mode, target)
    prompt_parts.extend(mode_prompt_parts(visual_mode, target, context, answer))
    prompt_parts.extend(
        [
            level_scene_constraints(str(quiz_item.get("sublevel") or quiz_item.get("cefr_level", ""))),
            target_specific_constraints(target.visual_target),
            f"Visual style: {settings.visual_style}.",
        ]
    )
    if settings.delivery_mode == VisualDeliveryMode.IMAGE_BRANDED:
        prompt_parts.append(f"Branding preset marker: {settings.branding_preset}.")
    prompt_parts.append("The final image should contain no readable text at all.")
    return VisualPrompt(
        generated_prompt=" ".join(part for part in prompt_parts if part.strip()),
        negative_prompt=negative_prompt(),
        visualization_type=visual_mode,
        answer_leak_risk=classify_answer_leak_risk(quiz_item, visual_mode),
        prompt_policy_version=PROMPT_POLICY_VERSION,
        fallback_recommendation=fallback_recommendation(visual_mode, "answer_grounded_no_text_rendering"),
        visual_mode=visual_mode,
        visual_target=target.visual_target,
        visual_context_hint=target.context_hint,
        visual_prompt_policy_version=PROMPT_POLICY_VERSION,
    )


def common_prompt_parts(
    quiz_item: dict[str, Any],
    visual_mode: str,
    target: VisualTargetResolution,
) -> list[str]:
    return [
        "Create one 16:9 clean educational illustration for a German language quiz.",
        "The image must be wordless: no letters, numbers, captions, labels, signs, screens, worksheets, speech bubbles, subtitles, or UI.",
        "Use the quiz context only as semantic grounding; never render any quiz text or answer text inside the image.",
        f"CEFR level: {quiz_item.get('sublevel') or quiz_item.get('cefr_level', '')}.",
        f"Theme: {quiz_item.get('theme_id', '')}.",
        f"Visual mode: {visual_mode}.",
        f"Visual target: {target.visual_target}.",
        f"Context hint: {target.context_hint}.",
        f"Focal object/action: {visual_target_description(target.visual_target)}.",
        "Center exactly one clear focal object or one clear focal action.",
        "Keep the image uncluttered, with no decorative extras or competing focal points.",
        "Do not copy any word from the target or semantic brief into the image.",
    ]


def mode_prompt_parts(
    visual_mode: str,
    target: VisualTargetResolution,
    context: str,
    answer: str,
) -> list[str]:
    if visual_mode == "target_action":
        return target_action_parts(target)
    if visual_mode == "target_object":
        return target_object_parts(target)
    if visual_mode == "context_only":
        return context_only_parts(target, context, answer)
    if visual_mode == "document_form":
        return document_form_parts(target)
    return symbolic_abstract_parts(target)


def target_action_parts(target: VisualTargetResolution) -> list[str]:
    return [
        "Prompt route target_action: show one visible action in progress.",
        f"Semantic visual brief: a simple scene where the main action is {target.visual_target}.",
        "Use one or two people when useful; never show more than three people.",
        "Avoid extra background story, side activities, and decorative props.",
    ]


def target_object_parts(target: VisualTargetResolution) -> list[str]:
    return [
        "Prompt route target_object: show one main concrete object.",
        f"Semantic visual brief: a clean object-focused image of {target.visual_target}.",
        "Use a plain background or a very light real-life context.",
        "Do not turn the object into a whole story scene.",
    ]


def context_only_parts(target: VisualTargetResolution, context: str, answer: str) -> list[str]:
    answer_guard = answer if non_visual_answer_token(answer) else "the grammar answer"
    return [
        "Prompt route context_only: show the extracted noun or context anchor, not the grammar token.",
        f"Semantic visual brief: depict the context around {target.visual_target}: {context_without_blank(context)}.",
        f"Never use '{answer_guard}' as the visual target and do not hint the correct grammatical form.",
        "Support only the noun/context anchor; do not decorate the whole sentence.",
    ]


def document_form_parts(target: VisualTargetResolution) -> list[str]:
    return [
        "Prompt route document_form: show a document, form, official letter, blank sheet, or folder.",
        f"Semantic visual brief: a clean document-focused composition for {target.visual_target}.",
        "The document must be blank or use only non-text placeholder lines.",
        "No readable text, numbers, paragraphs, signatures, stamps, calendar grids, or large office scenes.",
    ]


def symbolic_abstract_parts(target: VisualTargetResolution) -> list[str]:
    return [
        "Prompt route symbolic_abstract: show one symbolic scene with one semantic center.",
        f"Semantic visual brief: represent the idea behind {target.visual_target} with a clean, simple symbol or context.",
        "Avoid political campaigning, brands, flags, slogans, charts with labels, and busy detail.",
        "Prefer a clear metaphor over literal clutter.",
    ]


def level_scene_constraints(level: str) -> str:
    normalized = level.strip().upper()[:2]
    if normalized in {"A1", "A2"}:
        return (
            "A1/A2 scene limits: max two people preferred, max three allowed; one main object or one main action; "
            "max two secondary objects; no readable text; no calendars with numbers; no whiteboards with words; no clutter."
        )
    if normalized in {"B1", "B2"}:
        return "B1/B2 scene limits: allow light context, but keep one main focus and avoid a whole story."
    return "C1/C2 scene limits: allow semantic context, but keep it symbolic and clean instead of detail-heavy."


def negative_prompt() -> str:
    return (
        "No embedded text, no readable text, no letters, no numbers, no captions, no labels, no signs, "
        "no screens with text, no books with readable text, no worksheets, no answer labels, no option letters, "
        "no watermark, no quiz UI, no clutter, no crowded scene, no more than three people, "
        "no decorative story details, no competing focal points, no calendar wall, no calendar grid, "
        "no clock, no whiteboard words, no pseudo-text, no fake letters, no desk clutter, no phone, "
        "no cup, no plants, no political propaganda, no brand logos."
    )


def classify_visualization(quiz_item: dict[str, Any]) -> str:
    options = options_from_item(quiz_item)
    answer = answer_text(quiz_item, options)
    return resolve_visual_mode(
        str(quiz_item.get("item_id", "")),
        str(quiz_item.get("theme_id", "")),
        str(quiz_item.get("sublevel") or quiz_item.get("cefr_level", "")),
        question_context(quiz_item),
        answer,
        options,
    )


def classify_answer_leak_risk(quiz_item: dict[str, Any], visualization_type: str) -> str:
    del quiz_item, visualization_type
    return "answer_grounded_no_text_rendering"


def fallback_recommendation(visualization_type: str, answer_leak_risk: str) -> str:
    del visualization_type, answer_leak_risk
    return "none"


def question_context(quiz_item: dict[str, Any]) -> str:
    prompt = str(quiz_item.get("prompt", "")).strip()
    stem = str(quiz_item.get("stem_text", "")).strip()
    return " ".join(part for part in [prompt, stem] if part)


def visual_grounding_text(quiz_item: dict[str, Any], visualization_type: str) -> str:
    del visualization_type
    prompt = build_visual_prompt(quiz_item, VisualSettings.text_only("visual_grounding_preview"))
    return f"Depict {prompt.visual_mode} target {prompt.visual_target}: {prompt.visual_context_hint}"


def visual_target_text(quiz_item: dict[str, Any]) -> str:
    options = options_from_item(quiz_item)
    answer = answer_text(quiz_item, options)
    visual_mode = classify_visualization(quiz_item)
    target = extract_visual_target(question_context(quiz_item), answer, visual_mode, options)
    return target.visual_target


def context_without_blank(context: str) -> str:
    return re.sub(r"_{3,}", "the missing grammar slot", context).strip()


def visual_target_description(visual_target: str) -> str:
    normalized = normalize_token(visual_target)
    return VISUAL_TARGET_DESCRIPTIONS.get(normalized, f"one clear visual representation of {visual_target}")


def target_specific_constraints(visual_target: str) -> str:
    normalized = normalize_token(visual_target)
    return VISUAL_TARGET_CONSTRAINTS.get(normalized, "")


def resolved_question_text(quiz_item: dict[str, Any]) -> str:
    options = options_from_item(quiz_item)
    answer = answer_text(quiz_item, options).strip()
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


def answer_text(quiz_item: dict[str, Any], options: list[str] | None = None) -> str:
    resolved_options = options if options is not None else options_from_item(quiz_item)
    answer_key = int(str(quiz_item.get("answer_key", "0")))
    return str(resolved_options[answer_key])


def options_from_item(quiz_item: dict[str, Any]) -> list[str]:
    raw_options = quiz_item.get("options_json") or quiz_item.get("options") or []
    if isinstance(raw_options, list):
        return [str(option) for option in raw_options]
    return parse_options(str(raw_options))


def parse_options(raw_options: str) -> list[str]:
    try:
        parsed = json.loads(raw_options)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(raw_options)
    if not isinstance(parsed, list):
        raise ValueError("quiz item options must be a list")
    return [str(option) for option in parsed]
