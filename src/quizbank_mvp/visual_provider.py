"""Image provider boundary for Visual Quiz Delivery."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field
from typing import Any, Protocol

from PIL import Image


class ImageGenerationProvider(Protocol):
    def generate(self, request: "ImageGenerationRequest") -> "ImageGenerationResult":
        raise NotImplementedError


class ImageGenerationError(RuntimeError):
    """Structured provider failure that contains no secrets."""


DEFAULT_IMAGE_GENERATION_SIZE = "1536x1024"
DEFAULT_IMAGE_GENERATION_QUALITY = "medium"


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str
    size: str = DEFAULT_IMAGE_GENERATION_SIZE
    quality: str = DEFAULT_IMAGE_GENERATION_QUALITY
    output_format: str = "png"
    style_context: str = ""
    idempotency_key: str = ""


@dataclass(frozen=True)
class ImageGenerationResult:
    provider_name: str
    provider_model: str
    provider_response_id: str
    revised_prompt: str
    image_bytes: bytes
    mime_type: str
    width: int
    height: int
    usage: dict[str, Any] = field(default_factory=dict)


class FakeImageProvider:
    def __init__(self, should_fail: bool = False, mime_type: str = "image/png") -> None:
        self.should_fail = should_fail
        self.mime_type = mime_type
        self.calls: list[ImageGenerationRequest] = []

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        self.calls.append(request)
        if self.should_fail:
            raise ImageGenerationError("fake image provider failure")
        width, height = parse_image_size(request.size)
        digest = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()
        return ImageGenerationResult(
            provider_name="fake",
            provider_model="fake-image-v1",
            provider_response_id=f"fake_{digest[:16]}",
            revised_prompt=request.prompt,
            image_bytes=fake_image_bytes(width, height, digest),
            mime_type=self.mime_type,
            width=width,
            height=height,
            usage={"estimated_cost_minor": 0},
        )


def parse_image_size(size: str) -> tuple[int, int]:
    if "x" not in size:
        raise ImageGenerationError("image_size_invalid")
    width_text, height_text = size.split("x", 1)
    try:
        width = int(width_text)
        height = int(height_text)
    except ValueError as error:
        raise ImageGenerationError("image_size_invalid") from error
    if width <= 0 or height <= 0:
        raise ImageGenerationError("image_size_invalid")
    return width, height


def fake_image_bytes(width: int, height: int, digest: str) -> bytes:
    color = tuple(int(digest[index : index + 2], 16) for index in (0, 2, 4))
    image = Image.new("RGB", (width, height), color)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
