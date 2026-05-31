from __future__ import annotations

import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    utc_now,
)
from quizbank_mvp.selection import QuizBankProblem  # noqa: E402
from quizbank_mvp.telegram_delivery import (  # noqa: E402
    TelegramDeliveryError,
    TelegramDeliveryRequest,
    TelegramBotApiAdapter,
    TelegramImageSendResult,
    TelegramSendResult,
    run_telegram_delivery,
)
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_provider import FakeImageProvider  # noqa: E402
from quizbank_mvp.visual_settings import save_visual_settings  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class FakeVisualTelegramAdapter:
    def __init__(self, fail_poll: bool = False) -> None:
        self.fail_poll = fail_poll
        self.events: list[str] = []
        self.photo_payloads: list[dict[str, object]] = []
        self.poll_payloads: list[dict[str, object]] = []

    def send_photo(self, payload: dict[str, object]) -> TelegramImageSendResult:
        self.events.append("photo")
        self.photo_payloads.append(payload)
        if self.fail_photo:
            raise TelegramDeliveryError("photo_adapter_failure")
        return TelegramImageSendResult(message_id="photo_123")

    def send_quiz_poll(self, payload: dict[str, object]) -> TelegramSendResult:
        self.events.append("poll")
        self.poll_payloads.append(payload)
        if self.fail_poll:
            raise TelegramDeliveryError("poll_adapter_failure")
        return TelegramSendResult(message_id="poll_123", poll_id="poll_abc")


class VisualTelegramDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        self.asset_root = Path(self.temp_directory.name) / "visual-assets"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_image_quality_policy(self)
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_visual", ["A2"], ["T10"])

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_text_only_delivery_keeps_existing_poll_path(self) -> None:
        result = run_telegram_delivery(self.db_path, request(), asset_root=self.asset_root)

        self.assertEqual(result.status, "skipped")
        self.assertIsNone(visual_result_row(self, result.delivery_id))

    def test_image_standard_dry_run_records_skipped_visual_result(self) -> None:
        enable_visual(self, "consumer_visual")

        result = run_telegram_delivery(self.db_path, request(), asset_root=self.asset_root)
        visual = visual_result_row(self, result.delivery_id)

        self.assertEqual(result.status, "skipped")
        self.assertEqual(visual["requested_delivery_mode"], "image_standard")
        self.assertEqual(visual["visual_status"], "skipped")
        self.assertEqual(visual["fallback_used"], 0)
        self.assertIsNotNone(visual["asset_id"])

    def test_approved_visual_asset_is_attached_to_single_poll_message(self) -> None:
        enable_visual(self, "consumer_visual")
        adapter = FakeVisualTelegramAdapter()

        result = run_telegram_delivery(
            self.db_path,
            request(mode="real"),
            adapter=adapter,
            image_provider=FakeImageProvider(),
            asset_root=self.asset_root,
        )
        visual = visual_result_row(self, result.delivery_id)

        self.assertEqual(result.status, "sent")
        self.assertEqual(adapter.events, ["poll"])
        self.assertEqual(visual["telegram_image_message_id"], "poll_123")
        self.assertEqual(visual["visual_status"], "sent")
        self.assertEqual(adapter.photo_payloads, [])
        self.assertIn("poll_media_path", adapter.poll_payloads[0])
        self.assertNotIn("photo_path", adapter.poll_payloads[0])

    def test_poll_media_send_failure_marks_delivery_failed(self) -> None:
        enable_visual(self, "consumer_visual")
        adapter = FakeVisualTelegramAdapter(fail_poll=True)

        result = run_telegram_delivery(
            self.db_path,
            request(mode="real"),
            adapter=adapter,
            image_provider=FakeImageProvider(),
            asset_root=self.asset_root,
        )
        visual = visual_result_row(self, result.delivery_id)

        self.assertEqual(result.status, "failed")
        self.assertEqual(adapter.events, ["poll"])
        self.assertEqual(visual["visual_status"], "failed")
        self.assertEqual(visual["fallback_used"], 1)
        self.assertIn("poll_send_failed", visual["fallback_reason"])

    def test_poll_failure_marks_visual_delivery_failed(self) -> None:
        enable_visual(self, "consumer_visual")
        adapter = FakeVisualTelegramAdapter(fail_poll=True)

        result = run_telegram_delivery(
            self.db_path,
            request(mode="real"),
            adapter=adapter,
            image_provider=FakeImageProvider(),
            asset_root=self.asset_root,
        )
        visual = visual_result_row(self, result.delivery_id)

        self.assertEqual(result.status, "failed")
        self.assertEqual(visual["visual_status"], "failed")
        self.assertIn("poll_send_failed", visual["fallback_reason"])

    def test_repeat_guard_still_blocks_same_target_after_visual_send(self) -> None:
        enable_visual(self, "consumer_visual")
        seed_consumer(self.db_path, "consumer_second", 5, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_second", ["A2"], ["T10"])
        enable_visual(self, "consumer_second")
        adapter = FakeVisualTelegramAdapter()

        first = run_telegram_delivery(
            self.db_path,
            request(mode="real"),
            adapter=adapter,
            image_provider=FakeImageProvider(),
            asset_root=self.asset_root,
        )
        with self.assertRaises(QuizBankProblem) as repeat_error:
            run_telegram_delivery(
                self.db_path,
                request(consumer_id="consumer_second", mode="real"),
                adapter=adapter,
                image_provider=FakeImageProvider(),
                asset_root=self.asset_root,
            )

        self.assertEqual(first.status, "sent")
        self.assertEqual(repeat_error.exception.reason_code, "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(adapter.events, ["poll"])

    def test_real_visual_delivery_defaults_to_openai_environment_provider(self) -> None:
        enable_visual(self, "consumer_visual")
        adapter = FakeVisualTelegramAdapter()
        provider = FakeImageProvider()

        with patch(
            "quizbank_mvp.visual_provider_openai.OpenAIImageProvider.from_environment",
            return_value=provider,
        ) as from_environment:
            result = run_telegram_delivery(
                self.db_path,
                request(mode="real"),
                adapter=adapter,
                asset_root=self.asset_root,
            )

        self.assertEqual(result.status, "sent")
        self.assertEqual(adapter.events, ["poll"])
        self.assertEqual(len(provider.calls), 1)
        from_environment.assert_called_once()

    def test_block_visual_delivery_policy_stops_telegram_poll_fallback(self) -> None:
        save_blocking_visual_settings(self, "consumer_visual")
        adapter = FakeVisualTelegramAdapter()

        result = run_telegram_delivery(
            self.db_path,
            request(mode="real"),
            adapter=adapter,
            asset_root=self.asset_root,
        )
        visual = visual_result_row(self, result.delivery_id)

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.failure_reason, "visual_delivery_blocked:VISUAL_ENTITLEMENT_MISSING")
        self.assertEqual(adapter.events, [])
        self.assertEqual(visual["visual_status"], "failed")
        self.assertEqual(visual["fallback_used"], 0)

    def test_real_telegram_adapter_send_photo_uses_bot_api_multipart_upload(self) -> None:
        image_path = Path(self.temp_directory.name) / "photo.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nphoto")
        adapter = TelegramBotApiAdapter(" token ", api_base="https://telegram.test")

        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeHttpResponse({"ok": True, "result": {"message_id": 77}})
            result = adapter.send_photo({"chat_id": "@controlled_channel", "photo_path": str(image_path)})

        request_payload = urlopen.call_args.args[0]
        self.assertEqual(result.message_id, "77")
        self.assertIn("/bottoken/sendPhoto", request_payload.full_url)
        self.assertEqual(request_payload.get_method(), "POST")
        self.assertIn("multipart/form-data", request_payload.headers["Content-type"])
        self.assertIn(b'name="chat_id"', request_payload.data)
        self.assertIn(b"photo.png", request_payload.data)
        self.assertIn(b"Content-Type: image/png", request_payload.data)
        self.assertIn(b"\x89PNG\r\n\x1a\nphoto", request_payload.data)

    def test_real_telegram_adapter_attaches_visual_media_to_single_poll_message(self) -> None:
        image_path = Path(self.temp_directory.name) / "poll.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\npoll")
        adapter = TelegramBotApiAdapter(" token ", api_base="https://telegram.test")
        payload = {
            "chat_id": "@controlled_channel",
            "question": "Welche Antwort passt?",
            "options": ["buchen", "lesen"],
            "type": "quiz",
            "correct_option_ids": [0],
            "explanation": "Hier passt buchen.",
            "is_anonymous": True,
            "poll_media_path": str(image_path),
        }

        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeHttpResponse(
                {"ok": True, "result": {"message_id": 88, "poll": {"id": "poll_media"}}}
            )
            result = adapter.send_quiz_poll(payload)

        request_payload = urlopen.call_args.args[0]
        self.assertEqual(result.message_id, "88")
        self.assertEqual(result.poll_id, "poll_media")
        self.assertIn("/bottoken/sendPoll", request_payload.full_url)
        self.assertIn("multipart/form-data", request_payload.headers["Content-type"])
        self.assertIn(b'name="media"', request_payload.data)
        self.assertIn(b"attach://poll_media", request_payload.data)
        self.assertIn(b'name="poll_media"', request_payload.data)
        self.assertIn(b"Content-Type: image/png", request_payload.data)
        self.assertIn(b"poll.png", request_payload.data)


def request(consumer_id: str = "consumer_visual", mode: str = "dry_run") -> TelegramDeliveryRequest:
    return TelegramDeliveryRequest(
        consumer_id=consumer_id,
        chat_id="@controlled_channel",
        mode=mode,
        cefr_level="A2",
        theme_ids=("T10",),
    )


def enable_visual(case: VisualTelegramDeliveryTests, consumer_id: str) -> None:
    save_visual_settings(
        case.db_path,
        VisualSettings(
            consumer_id=consumer_id,
            delivery_mode=VisualDeliveryMode.IMAGE_STANDARD,
            visual_style="standard_illustration",
            branding_preset="none",
            fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
            daily_visual_delivery_limit=5,
            daily_generation_limit=5,
            monthly_generation_limit=20,
            is_active=True,
        ),
    )
    grant_feature(case, consumer_id, "visual_delivery.standard")
    grant_feature(case, consumer_id, "visual_generation.standard")


def save_blocking_visual_settings(case: VisualTelegramDeliveryTests, consumer_id: str) -> None:
    save_visual_settings(
        case.db_path,
        VisualSettings(
            consumer_id=consumer_id,
            delivery_mode=VisualDeliveryMode.IMAGE_STANDARD,
            visual_style="standard_illustration",
            branding_preset="none",
            fallback_policy=VisualFallbackPolicy.BLOCK_VISUAL_DELIVERY,
            daily_visual_delivery_limit=5,
            daily_generation_limit=5,
            monthly_generation_limit=20,
            is_active=True,
        ),
    )


def grant_feature(case: VisualTelegramDeliveryTests, consumer_id: str, feature: str) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status,
                allowed_cefr_levels_json, allowed_theme_ids_json,
                valid_until, created_at
            ) VALUES (?, ?, ?, 'active', ?, ?, NULL, ?)
            """,
            (
                f"ent_{consumer_id}_{feature}",
                consumer_id,
                feature,
                json.dumps(["A2"]),
                json.dumps(["T10"]),
                utc_now(),
            ),
        )


def seed_image_quality_policy(case: VisualTelegramDeliveryTests) -> None:
    now = utc_now()
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO quiz_item_image_quality_policy (
                item_id, theme_group, image_quality_recommended,
                image_quality_source, image_quality_policy_share,
                image_quality_override, created_at, updated_at
            ) VALUES (
                'approved_traceable_001', 'simple_visual', 'low',
                'policy', 0, NULL, ?, ?
            )
            """,
            (now, now),
        )


def visual_result_row(case: VisualTelegramDeliveryTests, delivery_id: str):
    with connect(case.db_path) as connection:
        return connection.execute(
            "SELECT * FROM visual_delivery_results WHERE delivery_id = ?",
            (delivery_id,),
        ).fetchone()


class FakeHttpResponse:
    def __init__(self, body: dict[str, object]) -> None:
        self.body = body

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
