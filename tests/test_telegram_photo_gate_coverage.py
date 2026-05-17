from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.telegram_bot_api import (  # noqa: E402
    TelegramBotApiAdapter,
    TelegramDeliveryError,
    execute_telegram_request,
    multipart_form_data,
    telegram_photo_multipart_payload,
)
from quizbank_mvp.telegram_delivery import (  # noqa: E402
    TelegramDeliveryRequest,
    blocked_visual_delivery_result,
    build_telegram_image_payload,
    send_visual_image,
    visual_result_after_poll,
)
from quizbank_mvp.visual_delivery import VisualDeliveryResolution  # noqa: E402
from quizbank_mvp.visual_models import VisualDeliveryMode  # noqa: E402


class TelegramPhotoGateCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.image_path = Path(self.temp_directory.name) / "photo.png"
        self.image_path.write_bytes(b"\x89PNG\r\n\x1a\nphoto")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_send_photo_uses_multipart_bot_api_request(self) -> None:
        adapter = TelegramBotApiAdapter(" token ", api_base="https://telegram.test")

        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeHttpResponse({"ok": True, "result": {"message_id": 42}})
            result = adapter.send_photo({"chat_id": "@channel", "photo_path": str(self.image_path)})

        request = urlopen.call_args.args[0]
        self.assertEqual(result.message_id, "42")
        self.assertIn("/bottoken/sendPhoto", request.full_url)
        self.assertIn("multipart/form-data", request.headers["Content-type"])
        self.assertIn(b'name="photo"', request.data)
        self.assertIn(b"photo.png", request.data)

    def test_photo_payload_rejects_missing_file_and_builds_parts(self) -> None:
        with self.assertRaisesRegex(TelegramDeliveryError, "telegram_photo_file_not_found"):
            telegram_photo_multipart_payload({"chat_id": "@channel", "photo_path": "missing.png"})

        content_type, body = multipart_form_data({"chat_id": "@channel"}, {"photo": ("x.png", b"x", "image/png")})

        self.assertIn("multipart/form-data", content_type)
        self.assertIn(b'name="chat_id"', body)
        self.assertIn(b"Content-Type: image/png", body)

    def test_execute_request_reports_http_and_url_errors(self) -> None:
        http_error = urllib.error.HTTPError(
            "https://telegram.test",
            400,
            "bad",
            {},
            io.BytesIO(b'{"description":"Bad Request: photo"}'),
        )
        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen", side_effect=http_error):
            with self.assertRaisesRegex(TelegramDeliveryError, "Bad Request: photo"):
                execute_telegram_request(object())

        url_error = urllib.error.URLError("offline")
        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen", side_effect=url_error):
            with self.assertRaisesRegex(TelegramDeliveryError, "telegram_request_failed:offline"):
                execute_telegram_request(object())

    def test_visual_delivery_helpers_cover_image_and_failure_paths(self) -> None:
        resolution = VisualDeliveryResolution(
            "generated_approved",
            VisualDeliveryMode.IMAGE_STANDARD,
            VisualDeliveryMode.IMAGE_STANDARD,
            False,
            asset_id="vasset",
            image_path=str(self.image_path),
        )
        item = {"delivery_id": "delivery", "consumer_id": "consumer", "item_id": "item"}

        payload = build_telegram_image_payload("@channel", item, resolution)
        dry_run = send_visual_image("dry_run", payload, None)

        self.assertEqual(payload["photo_path"], str(self.image_path))
        self.assertEqual(dry_run.visual_status, "skipped")
        with self.assertRaisesRegex(TelegramDeliveryError, "real_image_send_requires_adapter"):
            send_visual_image("real", payload, None)

    def test_blocked_visual_result_and_poll_failure_are_explicit(self) -> None:
        request = TelegramDeliveryRequest("consumer", "@channel", mode="real", cefr_level="A2", theme_ids=("T10",))
        item = {"delivery_id": "delivery", "item_id": "item"}
        resolution = VisualDeliveryResolution(
            "blocked",
            VisualDeliveryMode.IMAGE_STANDARD,
            VisualDeliveryMode.IMAGE_STANDARD,
            False,
            "VISUAL_ENTITLEMENT_MISSING",
        )

        blocked = blocked_visual_delivery_result(request, item, resolution)
        updated = visual_result_after_poll(
            dry_run_visual_result(),
            blocked,
        )

        self.assertEqual(blocked.status, "failed")
        self.assertEqual(blocked.failure_reason, "visual_delivery_blocked:VISUAL_ENTITLEMENT_MISSING")
        self.assertEqual(updated.visual_status, "failed")
        self.assertIn("poll_send_failed", updated.fallback_reason)


def dry_run_visual_result():
    resolution = VisualDeliveryResolution(
        "text_only",
        VisualDeliveryMode.TEXT_ONLY,
        VisualDeliveryMode.TEXT_ONLY,
        False,
    )
    return send_visual_image("dry_run", {"photo_path": ""}, FakePhotoAdapter(resolution))


class FakePhotoAdapter:
    def __init__(self, _resolution: VisualDeliveryResolution) -> None:
        pass

    def send_photo(self, _payload):
        raise AssertionError("dry_run must not call adapter")


class FakeHttpResponse:
    def __init__(self, body: dict[str, object]) -> None:
        self.body = body

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
