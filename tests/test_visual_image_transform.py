from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.visual_image_transform import normalize_visual_image  # noqa: E402
from quizbank_mvp.visual_provider import ImageGenerationResult  # noqa: E402


class VisualImageTransformTests(unittest.TestCase):
    def test_landscape_image_is_center_cropped_to_16x9(self) -> None:
        result = self.result(1536, 1024)

        normalized = normalize_visual_image(result)

        self.assertEqual((normalized.width, normalized.height), (1536, 864))
        with Image.open(io.BytesIO(normalized.image_bytes)) as image:
            self.assertEqual(image.size, (1536, 864))

    def test_existing_16x9_image_keeps_dimensions(self) -> None:
        result = self.result(1536, 864)

        normalized = normalize_visual_image(result)

        self.assertEqual((normalized.width, normalized.height), (1536, 864))

    def result(self, width: int, height: int) -> ImageGenerationResult:
        output = io.BytesIO()
        Image.new("RGB", (width, height), (32, 96, 160)).save(output, format="PNG")
        return ImageGenerationResult(
            provider_name="fake",
            provider_model="fake-image-v1",
            provider_response_id="fake",
            revised_prompt="",
            image_bytes=output.getvalue(),
            mime_type="image/png",
            width=width,
            height=height,
        )


if __name__ == "__main__":
    unittest.main()
