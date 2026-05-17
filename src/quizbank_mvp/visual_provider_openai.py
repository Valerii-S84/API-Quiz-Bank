"""OpenAI Image API provider behind explicit real-generation approval."""

from __future__ import annotations

import base64
import binascii
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .visual_provider import ImageGenerationError, ImageGenerationRequest, ImageGenerationResult


OPENAI_IMAGE_ENDPOINT = "https://api.openai.com/v1/images/generations"


class OpenAIProviderConfigurationError(RuntimeError):
    """Raised when OpenAI provider config is incomplete or not approved."""


class OpenAIImageProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        approve_real_generation: bool,
        endpoint: str = OPENAI_IMAGE_ENDPOINT,
        timeout_seconds: int = 60,
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        if not approve_real_generation:
            raise OpenAIProviderConfigurationError("real OpenAI generation requires explicit approval")
        if not api_key.strip():
            raise OpenAIProviderConfigurationError("OpenAI API key is required")
        if not model.strip():
            raise OpenAIProviderConfigurationError("OpenAI image model is required")
        if not endpoint.strip():
            raise OpenAIProviderConfigurationError("OpenAI image endpoint is required")
        if timeout_seconds <= 0:
            raise OpenAIProviderConfigurationError("OpenAI image timeout must be positive")
        self._api_key = api_key.strip()
        self.model = model.strip()
        self.endpoint = endpoint.strip()
        self.timeout_seconds = timeout_seconds
        self._urlopen = urlopen or urllib.request.urlopen

    @classmethod
    def from_environment(
        cls,
        approve_real_generation: bool,
        environ: Mapping[str, str] | None = None,
        urlopen: Callable[..., Any] | None = None,
    ) -> "OpenAIImageProvider":
        env = os.environ if environ is None else environ
        if env.get("VISUAL_IMAGE_PROVIDER") != "openai":
            raise OpenAIProviderConfigurationError("VISUAL_IMAGE_PROVIDER must be openai")
        api_key = openai_api_key_from_environment(env)
        model = env.get("VISUAL_OPENAI_IMAGE_MODEL", "").strip()
        endpoint = env.get("VISUAL_OPENAI_IMAGES_ENDPOINT", OPENAI_IMAGE_ENDPOINT).strip()
        timeout = timeout_from_environment(env)
        return cls(api_key, model, approve_real_generation, endpoint, timeout, urlopen)

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        http_request = self.http_request(request)
        try:
            with self._urlopen(http_request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
                request_id = str(response.headers.get("x-request-id", ""))
        except urllib.error.HTTPError as error:
            raise ImageGenerationError(f"openai_image_http_error:{error.code}") from error
        except urllib.error.URLError as error:
            raise ImageGenerationError(f"openai_image_request_failed:{type(error.reason).__name__}") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ImageGenerationError("openai_image_response_invalid") from error
        return self.result_from_body(body, request, request_id)

    def http_request(self, request: ImageGenerationRequest) -> urllib.request.Request:
        payload = {
            "model": self.model,
            "prompt": request.prompt,
            "n": 1,
            "size": request.size,
            "quality": request.quality,
            "output_format": request.output_format,
        }
        return urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

    def result_from_body(
        self,
        body: dict[str, Any],
        request: ImageGenerationRequest,
        request_id: str,
    ) -> ImageGenerationResult:
        try:
            image = body["data"][0]
            image_bytes = base64.b64decode(str(image["b64_json"]), validate=True)
            width, height = parse_size(str(body.get("size") or request.size))
        except (KeyError, IndexError, TypeError, ValueError, binascii.Error) as error:
            raise ImageGenerationError("openai_image_payload_missing_b64") from error
        output_format = str(body.get("output_format") or request.output_format)
        return ImageGenerationResult(
            provider_name="openai",
            provider_model=self.model,
            provider_response_id=request_id or f"openai_created_{body.get('created', '')}",
            revised_prompt=str(image.get("revised_prompt", "")),
            image_bytes=image_bytes,
            mime_type=mime_type_for_output(output_format),
            width=width,
            height=height,
            usage=dict(body.get("usage") or {}),
        )


def openai_api_key_from_environment(env: Mapping[str, str]) -> str:
    if env.get("VISUAL_OPENAI_API_KEY", "").strip():
        return str(env["VISUAL_OPENAI_API_KEY"]).strip()
    if env.get("OPENAI_API_KEY", "").strip():
        return str(env["OPENAI_API_KEY"]).strip()
    key_file = env.get("VISUAL_OPENAI_API_KEY_FILE", "").strip()
    if key_file:
        return Path(key_file).read_text(encoding="utf-8").strip()
    raise OpenAIProviderConfigurationError("OpenAI API key config is required")


def timeout_from_environment(env: Mapping[str, str]) -> int:
    raw_timeout = env.get("VISUAL_OPENAI_TIMEOUT_SECONDS", "60").strip()
    try:
        timeout = int(raw_timeout)
    except ValueError as error:
        raise OpenAIProviderConfigurationError("VISUAL_OPENAI_TIMEOUT_SECONDS must be an integer") from error
    if timeout <= 0:
        raise OpenAIProviderConfigurationError("VISUAL_OPENAI_TIMEOUT_SECONDS must be positive")
    return timeout


def parse_size(size: str) -> tuple[int, int]:
    if "x" not in size:
        return (1024, 1024)
    width, height = size.split("x", 1)
    return (int(width), int(height))


def mime_type_for_output(output_format: str) -> str:
    return {
        "png": "image/png",
        "webp": "image/webp",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
    }.get(output_format, "image/png")
