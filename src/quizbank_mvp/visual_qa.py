"""Deterministic QA gates for generated visual assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .visual_models import VisualDeliveryMode, VisualSettings
from .visual_image_transform import is_target_aspect_ratio
from .visual_prompt_builder import VisualPrompt
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
    if not is_target_aspect_ratio(result.width, result.height):
        return rejected("IMAGE_ASPECT_RATIO_INVALID", "Generated image must be 16:9.")
    if branded_marker_missing(prompt, settings):
        return rejected("BRANDING_PRESET_MISSING", "Branded mode lacks a branding preset marker.")
    return VisualQADecision("approved", "QA_APPROVED", "Deterministic QA passed.")


def branded_marker_missing(prompt: VisualPrompt, settings: VisualSettings) -> bool:
    if settings.delivery_mode != VisualDeliveryMode.IMAGE_BRANDED:
        return False
    return settings.branding_preset not in prompt.generated_prompt


def rejected(reason_code: str, detail: str) -> VisualQADecision:
    return VisualQADecision("rejected", reason_code, detail)
