"""Image provider boundary for Visual Quiz Delivery."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol


class ImageGenerationProvider(Protocol):
    def generate(self, request: "ImageGenerationRequest") -> "ImageGenerationResult":
        raise NotImplementedError


class ImageGenerationError(RuntimeError):
    """Structured provider failure that contains no secrets."""


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
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
        digest = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()
        return ImageGenerationResult(
            provider_name="fake",
            provider_model="fake-image-v1",
            provider_response_id=f"fake_{digest[:16]}",
            revised_prompt=request.prompt,
            image_bytes=b"\x89PNG\r\n\x1a\n" + digest.encode("ascii"),
            mime_type=self.mime_type,
            width=1024,
            height=1024,
            usage={"estimated_cost_minor": 0},
        )
