"""Image post-processing for Visual Quiz Delivery assets."""

from __future__ import annotations

import io
from dataclasses import replace

from PIL import Image, UnidentifiedImageError

from .visual_provider import ImageGenerationError, ImageGenerationResult


TARGET_ASPECT_WIDTH = 16
TARGET_ASPECT_HEIGHT = 9


def normalize_visual_image(result: ImageGenerationResult) -> ImageGenerationResult:
    if result.mime_type not in {"image/png", "image/jpeg", "image/webp"}:
        return result
    try:
        with Image.open(io.BytesIO(result.image_bytes)) as image:
            image.load()
            cropped = center_crop_to_aspect(image, TARGET_ASPECT_WIDTH, TARGET_ASPECT_HEIGHT)
            image_bytes = encode_image(cropped, result.mime_type)
    except (OSError, UnidentifiedImageError) as error:
        raise ImageGenerationError("image_postprocess_failed") from error
    return replace(
        result,
        image_bytes=image_bytes,
        width=cropped.width,
        height=cropped.height,
    )


def center_crop_to_aspect(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    source = image.convert("RGB") if image.mode not in {"RGB", "RGBA"} else image
    current_width, current_height = source.size
    if current_width <= 0 or current_height <= 0:
        raise ImageGenerationError("image_postprocess_invalid_dimensions")
    target_ratio = target_width / target_height
    current_ratio = current_width / current_height
    if abs(current_ratio - target_ratio) < 0.001:
        return source.copy()
    if current_ratio > target_ratio:
        new_width = round(current_height * target_ratio)
        left = (current_width - new_width) // 2
        return source.crop((left, 0, left + new_width, current_height))
    new_height = round(current_width / target_ratio)
    top = (current_height - new_height) // 2
    return source.crop((0, top, current_width, top + new_height))


def encode_image(image: Image.Image, mime_type: str) -> bytes:
    output = io.BytesIO()
    if mime_type == "image/jpeg":
        image.convert("RGB").save(output, format="JPEG", quality=95)
    elif mime_type == "image/webp":
        image.save(output, format="WEBP", quality=95)
    else:
        image.save(output, format="PNG")
    return output.getvalue()


def is_target_aspect_ratio(width: int, height: int) -> bool:
    if height <= 0:
        return False
    return abs((width / height) - (TARGET_ASPECT_WIDTH / TARGET_ASPECT_HEIGHT)) < 0.001
