from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_provider import (
    FakeImageProvider,
    ImageGenerationError,
    ImageGenerationRequest,
)
from quizbank_mvp.visual_provider_openai import (  # noqa: E402
    OpenAIImageProvider,
    OpenAIProviderConfigurationError,
)


class VisualProviderTests(unittest.TestCase):
    def test_fake_provider_returns_deterministic_image_bytes(self) -> None:
        provider = FakeImageProvider()
        request = ImageGenerationRequest(prompt="draw a classroom", negative_prompt="no text")

        first = provider.generate(request)
        second = provider.generate(request)

        self.assertEqual(first.image_bytes, second.image_bytes)
        self.assertEqual(first.provider_name, "fake")
        self.assertEqual(len(provider.calls), 2)

    def test_fake_provider_failure_maps_to_structured_exception(self) -> None:
        provider = FakeImageProvider(should_fail=True)

        with self.assertRaises(ImageGenerationError):
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))

    def test_fake_provider_can_emit_unsupported_mime_for_qa_tests(self) -> None:
        provider = FakeImageProvider(mime_type="image/gif")

        result = provider.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))

        self.assertEqual(result.mime_type, "image/gif")
        self.assertTrue(result.image_bytes)

    def test_openai_provider_requires_explicit_config_and_approval(self) -> None:
        env = {
            "VISUAL_IMAGE_PROVIDER": "openai",
            "VISUAL_OPENAI_API_KEY": "test-key",
            "VISUAL_OPENAI_IMAGE_MODEL": "gpt-image-2",
        }

        with self.assertRaises(OpenAIProviderConfigurationError):
            OpenAIImageProvider("test-key", "gpt-image-2", approve_real_generation=False)
        with self.assertRaises(OpenAIProviderConfigurationError):
            OpenAIImageProvider.from_environment(False, env)
        with self.assertRaises(OpenAIProviderConfigurationError):
            OpenAIImageProvider.from_environment(True, {"VISUAL_IMAGE_PROVIDER": "fake"})

    def test_openai_provider_uses_mocked_http_client_only(self) -> None:
        spy = UrlopenSpy(openai_response())
        provider = OpenAIImageProvider.from_environment(
            True,
            openai_env(),
            urlopen=spy,
        )

        result = provider.generate(
            ImageGenerationRequest(
                prompt="draw a classroom",
                negative_prompt="no text",
                size="512x512",
                output_format="webp",
            )
        )

        payload = json.loads(spy.request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "gpt-image-2")
        self.assertEqual(payload["prompt"], "draw a classroom")
        self.assertEqual(payload["quality"], "auto")
        self.assertEqual(spy.request.get_method(), "POST")
        self.assertEqual(spy.timeout, 7)
        self.assertEqual(result.provider_name, "openai")
        self.assertEqual(result.provider_response_id, "req_visual_test")
        self.assertEqual(result.image_bytes, b"visual-image")
        self.assertEqual(result.mime_type, "image/webp")
        self.assertEqual((result.width, result.height), (512, 512))

    def test_openai_provider_loads_secret_from_file_without_printing_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "openai.key"
            key_file.write_text("file-loaded-key", encoding="utf-8")
            env = {
                "VISUAL_IMAGE_PROVIDER": "openai",
                "VISUAL_OPENAI_API_KEY_FILE": str(key_file),
                "VISUAL_OPENAI_IMAGE_MODEL": "gpt-image-2",
            }

            provider = OpenAIImageProvider.from_environment(True, env, urlopen=UrlopenSpy(openai_response()))

        self.assertEqual(provider.model, "gpt-image-2")

    def test_openai_provider_timeout_error_is_secret_safe(self) -> None:
        def timeout_urlopen(_request, timeout: int):
            raise urllib.error.URLError("timeout test-key")

        provider = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=timeout_urlopen)

        with self.assertRaises(ImageGenerationError) as problem:
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))

        self.assertIn("openai_image_request_failed", str(problem.exception))
        self.assertNotIn("test-key", str(problem.exception))

    def test_openai_provider_invalid_payload_is_secret_safe(self) -> None:
        provider = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=UrlopenSpy({"data": [{}]}))

        with self.assertRaises(ImageGenerationError) as problem:
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))

        self.assertEqual(str(problem.exception), "openai_image_payload_missing_b64")

    def test_openai_provider_rejects_quality_outside_gpt_image_2_enum(self) -> None:
        provider = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=UrlopenSpy(openai_response()))

        with self.assertRaises(ImageGenerationError) as problem:
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt="", quality="standard"))

        self.assertEqual(str(problem.exception), "openai_image_quality_invalid")


class UrlopenSpy:
    def __init__(self, body: dict[str, object]) -> None:
        self.body = body
        self.request = None
        self.timeout = None

    def __call__(self, request, timeout: int) -> "OpenAIStubResponse":
        self.request = request
        self.timeout = timeout
        return OpenAIStubResponse(self.body)


class OpenAIStubResponse:
    headers = {"x-request-id": "req_visual_test"}

    def __init__(self, body: dict[str, object]) -> None:
        self.body = body

    def __enter__(self) -> "OpenAIStubResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")


def openai_env() -> dict[str, str]:
    return {
        "VISUAL_IMAGE_PROVIDER": "openai",
        "VISUAL_OPENAI_API_KEY": "test-key",
        "VISUAL_OPENAI_IMAGE_MODEL": "gpt-image-2",
        "VISUAL_OPENAI_TIMEOUT_SECONDS": "7",
    }


def openai_response() -> dict[str, object]:
    return {
        "data": [
            {
                "b64_json": base64.b64encode(b"visual-image").decode("ascii"),
                "revised_prompt": "safe classroom illustration",
            }
        ],
        "usage": {"total_tokens": 0},
    }


if __name__ == "__main__":
    unittest.main()
