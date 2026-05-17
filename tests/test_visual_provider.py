from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_provider import (
    FakeImageProvider,
    ImageGenerationError,
    ImageGenerationRequest,
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


if __name__ == "__main__":
    unittest.main()
