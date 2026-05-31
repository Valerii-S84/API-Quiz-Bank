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
    ImageGenerationProvider,
    ImageGenerationError,
    ImageGenerationRequest,
    parse_image_size,
)
from quizbank_mvp.visual_provider_openai import (  # noqa: E402
    OPENAI_IMAGE_URL_ALLOWED_HOSTS,
    OpenAIEnvironmentImageProvider,
    OpenAIImageProvider,
    OpenAIProviderConfigurationError,
    mime_type_for_output,
    openai_api_key_from_environment,
    parse_size,
    timeout_from_environment,
)


class VisualProviderTests(unittest.TestCase):
    def test_fake_provider_returns_deterministic_image_bytes(self) -> None:
        provider = FakeImageProvider()
        request = ImageGenerationRequest(prompt="draw a classroom", negative_prompt="no text")

        first = provider.generate(request)
        second = provider.generate(request)

        self.assertEqual(first.image_bytes, second.image_bytes)
        self.assertEqual(first.provider_name, "fake")
        self.assertEqual((first.width, first.height), (1536, 1024))
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

    def test_image_provider_contract_and_size_parser_reject_invalid_sizes(self) -> None:
        class BareProvider(ImageGenerationProvider):
            pass

        with self.assertRaises(NotImplementedError):
            BareProvider().generate(ImageGenerationRequest(prompt="x", negative_prompt=""))
        for size in ("1024", "widextall", "0x1024", "1024x-1"):
            with self.subTest(size=size):
                with self.assertRaises(ImageGenerationError):
                    parse_image_size(size)

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
        for kwargs in (
            {"api_key": "", "model": "gpt-image-2", "endpoint": "https://api.test", "timeout_seconds": 60},
            {"api_key": "test-key", "model": "", "endpoint": "https://api.test", "timeout_seconds": 60},
            {"api_key": "test-key", "model": "gpt-image-2", "endpoint": "", "timeout_seconds": 60},
            {"api_key": "test-key", "model": "gpt-image-2", "endpoint": "https://api.test", "timeout_seconds": 0},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(OpenAIProviderConfigurationError):
                    OpenAIImageProvider(approve_real_generation=True, **kwargs)

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
        self.assertEqual(payload["quality"], "low")
        self.assertEqual(spy.request.get_method(), "POST")
        self.assertEqual(spy.timeout, 7)
        self.assertEqual(result.provider_name, "openai")
        self.assertEqual(result.provider_response_id, "req_visual_test")
        self.assertEqual(result.image_bytes, b"visual-image")
        self.assertEqual(result.mime_type, "image/webp")
        self.assertEqual((result.width, result.height), (512, 512))

    def test_openai_provider_requests_base64_for_dalle_models(self) -> None:
        provider = OpenAIImageProvider("test-key", "dall-e-3", True, urlopen=UrlopenSpy(openai_response()))

        request = provider.http_request(ImageGenerationRequest(prompt="x", negative_prompt=""))
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["response_format"], "b64_json")

    def test_openai_provider_fetches_url_image_payloads(self) -> None:
        image_url = openai_image_url("generated.png")
        urlopen = UrlopenSequence(
            [
                {"data": [{"url": image_url, "revised_prompt": "safe prompt"}]},
                b"\x89PNG\r\n\x1a\nurl-image",
            ]
        )
        provider = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=urlopen)

        result = provider.generate(ImageGenerationRequest(prompt="draw a classroom", negative_prompt=""))

        self.assertEqual(result.image_bytes, b"\x89PNG\r\n\x1a\nurl-image")
        self.assertEqual(urlopen.calls[1].full_url, image_url)

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

    def test_openai_provider_invalid_json_and_http_errors_are_structured(self) -> None:
        invalid_json = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=UrlopenBytes(b"{not-json"))
        http_failure = OpenAIImageProvider(
            "test-key",
            "gpt-image-2",
            True,
            urlopen=lambda _request, timeout: (_ for _ in ()).throw(
                urllib.error.HTTPError("https://api.test", 429, "rate limited", {}, None)
            ),
        )

        with self.assertRaisesRegex(ImageGenerationError, "openai_image_response_invalid"):
            invalid_json.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))
        with self.assertRaisesRegex(ImageGenerationError, "openai_image_http_error:429"):
            http_failure.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))

    def test_openai_environment_provider_maps_configuration_errors_to_generation_errors(self) -> None:
        provider = OpenAIEnvironmentImageProvider({"VISUAL_IMAGE_PROVIDER": "openai"}, urlopen=UrlopenSpy(openai_response()))

        with self.assertRaisesRegex(ImageGenerationError, "openai_image_provider_unconfigured"):
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt=""))

    def test_openai_environment_helpers_validate_key_timeout_size_and_mime(self) -> None:
        self.assertEqual(openai_api_key_from_environment({"OPENAI_API_KEY": " fallback-key "}), "fallback-key")
        self.assertEqual(timeout_from_environment({}), 60)
        self.assertEqual(parse_size("not-a-size"), (1024, 1024))
        self.assertEqual(mime_type_for_output("jpg"), "image/jpeg")
        self.assertEqual(mime_type_for_output("unknown"), "image/png")

        for env in ({"VISUAL_OPENAI_TIMEOUT_SECONDS": "abc"}, {"VISUAL_OPENAI_TIMEOUT_SECONDS": "0"}):
            with self.subTest(env=env):
                with self.assertRaises(OpenAIProviderConfigurationError):
                    timeout_from_environment(env)

    def test_openai_provider_rejects_quality_outside_low_medium_enum(self) -> None:
        provider = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=UrlopenSpy(openai_response()))

        with self.assertRaises(ImageGenerationError) as problem:
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt="", quality="standard"))

        self.assertEqual(str(problem.exception), "openai_image_quality_invalid")

        with self.assertRaises(ImageGenerationError):
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt="", quality="high"))
        with self.assertRaises(ImageGenerationError):
            provider.generate(ImageGenerationRequest(prompt="x", negative_prompt="", quality="auto"))


class OpenAIProviderUrlBoundaryTests(unittest.TestCase):
    def test_openai_provider_rejects_non_positive_url_byte_limit(self) -> None:
        with self.assertRaisesRegex(OpenAIProviderConfigurationError, "URL byte limit"):
            OpenAIImageProvider(
                "test-key",
                "gpt-image-2",
                True,
                max_url_image_bytes=0,
            )

    def test_openai_provider_rejects_non_object_image_payload(self) -> None:
        provider = OpenAIImageProvider("test-key", "gpt-image-2", True)

        with self.assertRaisesRegex(ImageGenerationError, "openai_image_payload_missing_b64"):
            provider.result_from_body(
                {"data": [[]]},
                ImageGenerationRequest(prompt="x", negative_prompt=""),
                "req_bad_payload",
            )

    def test_openai_provider_url_payload_failures_are_structured(self) -> None:
        provider = OpenAIImageProvider("test-key", "gpt-image-2", True, urlopen=UrlopenBytes(b""))
        http_provider = OpenAIImageProvider(
            "test-key",
            "gpt-image-2",
            True,
            urlopen=lambda _request, timeout: (_ for _ in ()).throw(
                urllib.error.HTTPError("https://images.test/generated.png", 404, "missing", {}, None)
            ),
        )
        url_provider = OpenAIImageProvider(
            "test-key",
            "gpt-image-2",
            True,
            urlopen=lambda _request, timeout: (_ for _ in ()).throw(urllib.error.URLError("offline")),
        )

        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_invalid"):
            provider.fetch_image_url(openai_image_url("generated.png").replace("https://", "http://", 1))
        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_host_not_allowed"):
            provider.fetch_image_url("https://images.test/generated.png")
        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_empty"):
            provider.fetch_image_url(openai_image_url("generated.png"))
        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_http_error:404"):
            http_provider.fetch_image_url(openai_image_url("generated.png"))
        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_request_failed:str"):
            url_provider.fetch_image_url(openai_image_url("generated.png"))

    def test_openai_provider_rejects_oversized_url_image_payloads(self) -> None:
        provider = OpenAIImageProvider(
            "test-key",
            "gpt-image-2",
            True,
            urlopen=UrlopenBytes(b"12345"),
            max_url_image_bytes=4,
        )

        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_too_large"):
            provider.fetch_image_url(openai_image_url("generated.png"))

    def test_openai_provider_rejects_redirect_to_untrusted_url_host(self) -> None:
        provider = OpenAIImageProvider(
            "test-key",
            "gpt-image-2",
            True,
            urlopen=UrlopenRedirect("https://images.test/generated.png"),
        )

        with self.assertRaisesRegex(ImageGenerationError, "openai_image_url_host_not_allowed"):
            provider.fetch_image_url(openai_image_url("generated.png"))


class UrlopenSpy:
    def __init__(self, body: dict[str, object]) -> None:
        self.body = body
        self.request = None
        self.timeout = None

    def __call__(self, request, timeout: int) -> "OpenAIStubResponse":
        self.request = request
        self.timeout = timeout
        return OpenAIStubResponse(self.body)


class UrlopenSequence:
    def __init__(self, bodies: list[dict[str, object] | bytes]) -> None:
        self.bodies = list(bodies)
        self.calls = []

    def __call__(self, request, timeout: int) -> "OpenAIStubResponse":
        self.calls.append(request)
        return OpenAIStubResponse(self.bodies.pop(0))


class UrlopenBytes:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __call__(self, request, timeout: int) -> "OpenAIStubResponse":
        return OpenAIStubResponse(self.body)


class UrlopenRedirect:
    def __init__(self, final_url: str) -> None:
        self.final_url = final_url

    def __call__(self, request, timeout: int) -> "OpenAIStubResponse":
        return OpenAIRedirectResponse(b"redirected-image", self.final_url)


class OpenAIStubResponse:
    headers = {"x-request-id": "req_visual_test"}

    def __init__(self, body: dict[str, object] | bytes) -> None:
        self.body = body

    def __enter__(self) -> "OpenAIStubResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if isinstance(self.body, bytes):
            return self.body if size < 0 else self.body[:size]
        encoded = json.dumps(self.body).encode("utf-8")
        return encoded if size < 0 else encoded[:size]


class OpenAIRedirectResponse(OpenAIStubResponse):
    def __init__(self, body: bytes, final_url: str) -> None:
        super().__init__(body)
        self.final_url = final_url

    def geturl(self) -> str:
        return self.final_url


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


def openai_image_url(filename: str) -> str:
    host = sorted(OPENAI_IMAGE_URL_ALLOWED_HOSTS)[0]
    return f"https://{host}/{filename}"


if __name__ == "__main__":
    unittest.main()
