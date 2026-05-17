"""Deterministic QA gates for generated visual assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .visual_models import VisualDeliveryMode, VisualSettings
from .visual_prompt_builder import VisualPrompt, answer_text
from .visual_provider import ImageGenerationResult


SUPPORTED_MIME_TYPES = {"image/png", "image/webp", "image/jpeg"}


@dataclass(frozen=True)
class VisualQADecision:
    qa_status: str
    reason_code: str
    detail: str


def evaluate_visual_qa(
    prompt: VisualPrompt,
    result: ImageGenerationResult,
    quiz_item: dict[str, Any],
    settings: VisualSettings,
) -> VisualQADecision:
    if not result.image_bytes:
        return rejected("EMPTY_IMAGE_BYTES", "Provider returned no image bytes.")
    if result.mime_type not in SUPPORTED_MIME_TYPES:
        return rejected("UNSUPPORTED_MIME_TYPE", "Provider returned unsupported mime type.")
    if result.width < 256 or result.height < 256:
        return rejected("IMAGE_TOO_SMALL", "Generated image dimensions are too small.")
    if contains_forbidden_answer_text(prompt, result, quiz_item):
        return rejected("ANSWER_LEAK_RISK", "Prompt or revised prompt contains the exact answer.")
    if branded_marker_missing(prompt, settings):
        return rejected("BRANDING_PRESET_MISSING", "Branded mode lacks a branding preset marker.")
    if prompt.fallback_recommendation == "text_only":
        return needs_review("UNSUPPORTED_VISUALIZATION", "Prompt policy recommends text-only fallback.")
    if prompt.visualization_type == "neutral_learning":
        return needs_review("UNCERTAIN_VISUALIZATION", "Visualization type is too uncertain.")
    return VisualQADecision("approved", "QA_APPROVED", "Deterministic QA passed.")


def contains_forbidden_answer_text(
    prompt: VisualPrompt,
    result: ImageGenerationResult,
    quiz_item: dict[str, Any],
) -> bool:
    if prompt.answer_leak_risk != "avoid_exact_answer":
        return False
    answer = answer_text(quiz_item).strip().lower()
    if len(answer) < 2:
        return False
    haystack = f"{prompt.generated_prompt} {result.revised_prompt}".lower()
    return answer in haystack


def branded_marker_missing(prompt: VisualPrompt, settings: VisualSettings) -> bool:
    if settings.delivery_mode != VisualDeliveryMode.IMAGE_BRANDED:
        return False
    return settings.branding_preset not in prompt.generated_prompt


def rejected(reason_code: str, detail: str) -> VisualQADecision:
    return VisualQADecision("rejected", reason_code, detail)


def needs_review(reason_code: str, detail: str) -> VisualQADecision:
    return VisualQADecision("needs_review", reason_code, detail)
