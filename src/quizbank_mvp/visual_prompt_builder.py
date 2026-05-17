"""Deterministic prompt construction for Visual Quiz Delivery."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .visual_models import VisualDeliveryMode, VisualSettings


PROMPT_POLICY_VERSION = "visual_prompt_policy_v3_focused_target"

NON_VISUAL_GRAMMAR_TOKENS = frozenset(
    {
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
        "eines",
        "kein",
        "keine",
        "keinen",
        "keinem",
        "keiner",
        "keines",
        "ich",
        "du",
        "er",
        "sie",
        "es",
        "wir",
        "ihr",
        "mich",
        "dich",
        "ihn",
        "uns",
        "euch",
        "mir",
        "dir",
        "ihm",
        "ihnen",
        "mein",
        "dein",
        "sein",
        "ihr",
        "unser",
        "euer",
        "ja",
        "doch",
        "mal",
        "denn",
        "wohl",
        "nur",
        "eben",
        "halt",
        "nicht",
        "aus",
        "bei",
        "mit",
        "nach",
        "seit",
        "von",
        "zu",
        "zum",
        "zur",
        "durch",
        "für",
        "fuer",
        "gegen",
        "ohne",
        "um",
        "bis",
        "in",
        "im",
        "ins",
        "an",
        "am",
        "auf",
        "über",
        "ueber",
        "unter",
        "vor",
        "hinter",
        "neben",
        "zwischen",
        "während",
        "waehrend",
        "wegen",
        "trotz",
    }
)
NOUN_TARGET_SKIP_TOKENS = NON_VISUAL_GRAMMAR_TOKENS | frozenset({"ist", "sind", "war", "waren", "wird", "werden"})
VISUAL_TARGET_DESCRIPTIONS = {
    "auftrag": "one clear blank work order / task document as the only main object on a plain background",
}
VISUAL_TARGET_CONSTRAINTS = {
    "auftrag": (
        "For this target, use an object-only composition: one blank work order or task document, "
        "no people, no office room, no desk accessories, no calendars, no clocks, no plants, no phone, no cup."
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


def build_visual_prompt(quiz_item: dict[str, Any], settings: VisualSettings) -> VisualPrompt:
    visualization_type = classify_visualization(quiz_item)
    answer_leak_risk = classify_answer_leak_risk(quiz_item, visualization_type)
    grounding = visual_grounding_text(quiz_item, visualization_type)
    visual_target = visual_target_text(quiz_item)
    target_description = visual_target_description(visual_target)
    prompt_parts = [
        "Create one 16:9 clean educational illustration for a German language quiz.",
        "The image must be wordless: no letters, numbers, captions, labels, signs, screens, worksheets, speech bubbles, subtitles, or UI.",
        "Use the quiz context only as semantic grounding; never render any quiz text or answer text inside the image.",
        f"CEFR level: {quiz_item.get('sublevel') or quiz_item.get('cefr_level', '')}.",
        f"Theme: {quiz_item.get('theme_id', '')}.",
        f"Visualization type: {visualization_type}.",
        f"Target noun/action: {visual_target}.",
        f"Focal object/action: {target_description}.",
        target_specific_constraints(visual_target),
        f"Semantic visual brief: {grounding}.",
        "Do not copy any word from the target noun/action or semantic brief into the image.",
        "Center one clear focal object or one clear focal action.",
        "Use a simple A1/A2-style composition with a plain background and only a few necessary props.",
        "Prefer zero to two people; never show more than three people.",
        "Keep the image uncluttered, with no decorative extras or competing focal points.",
        "Do not add calendar walls, calendar grids, clocks, deadline symbols, meeting scenes, or office story details unless they are the target.",
        "If a document appears, it must be blank or use only non-text placeholder lines.",
        "Support only the target noun/action, not the grammar answer token; do not decorate the whole story.",
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
            "no option letters, no watermark, no quiz UI, no clutter, no crowded scene, "
            "no more than three people, no decorative story details, no competing focal points, "
            "no calendar wall, no calendar grid, no clock, no pseudo-text, no fake letters, "
            "no desk clutter, no phone, no cup, no plants."
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


def visual_target_text(quiz_item: dict[str, Any]) -> str:
    answer = answer_text(quiz_item).strip()
    blank_target = blank_connected_target(str(quiz_item.get("stem_text", "")))
    if blank_target and non_visual_answer_token(answer):
        return blank_target
    return answer


def non_visual_answer_token(answer: str) -> bool:
    normalized = normalize_token(answer)
    return normalized in NON_VISUAL_GRAMMAR_TOKENS


def blank_connected_target(stem_text: str) -> str:
    blank = re.search(r"_{3,}", stem_text)
    if blank is None:
        return ""
    right_target = first_noun_like_token(stem_text[blank.end() :])
    if right_target:
        return right_target
    return last_noun_like_token(stem_text[: blank.start()])


def first_noun_like_token(text: str) -> str:
    for token in text_tokens(text):
        if is_noun_target_candidate(token):
            return token
    return ""


def last_noun_like_token(text: str) -> str:
    for token in reversed(text_tokens(text)):
        if is_noun_target_candidate(token):
            return token
    return ""


def text_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß-]*", text)


def is_noun_target_candidate(token: str) -> bool:
    if normalize_token(token) in NOUN_TARGET_SKIP_TOKENS:
        return False
    return token[:1].isupper() and len(token) > 1


def normalize_token(token: str) -> str:
    return token.strip().strip(".,;:!?()[]{}\"'„“”").lower()


def visual_target_description(visual_target: str) -> str:
    normalized = normalize_token(visual_target)
    return VISUAL_TARGET_DESCRIPTIONS.get(normalized, f"one clear visual representation of {visual_target}")


def target_specific_constraints(visual_target: str) -> str:
    normalized = normalize_token(visual_target)
    return VISUAL_TARGET_CONSTRAINTS.get(normalized, "")


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
