from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import cli
from quizbank_mvp.app import create_app, next_quiz_response
from quizbank_mvp.database import (
    connect,
    database_is_ready,
    initialize_database,
    seed_control_fixture,
    seed_demo_state,
    transition_consumer_status,
    transition_item_status,
)
from quizbank_mvp.telegram_delivery import (
    TelegramBotApiAdapter,
    TelegramDeliveryError,
    TelegramDeliveryResult,
    build_telegram_poll_payload,
    handle_telegram_send,
    load_delivery_item,
    poll_id_from_result,
    read_http_error_description,
    redact_telegram_target,
    telegram_api_payload,
    validate_correct_option_ids,
    validate_delivery_mode,
    validate_telegram_poll,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class MvpCoverageBranchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *args: str) -> str:
        stdout = io.StringIO()
        with patch.object(sys, "argv", ["quizbank-mvp", "--db-path", str(self.db_path), *args]):
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(cli.main(), 0)
        return stdout.getvalue()

    def test_cli_database_lifecycle_commands(self) -> None:
        self.assertIn("initialized database", self.run_cli("init-db"))
        self.assertIn(
            "seeded quiz items: 1",
            self.run_cli("seed-items", "--fixture", str(APPROVED_FIXTURE), "--status", "draft"),
        )
        self.assertIn(
            "seeded consumer: cli_consumer",
            self.run_cli(
                "seed-consumer",
                "--consumer-id",
                "cli_consumer",
                "--cefr-level",
                "A2",
                "--theme-id",
                "T10",
                "--with-entitlement",
                "--api-key",
                "cli_api_key",
            ),
        )
        transition_output = self.run_cli(
            "transition-status",
            "--item-id",
            "approved_traceable_001",
            "--to-status",
            "approved",
            "--reason",
            "coverage",
        )
        self.assertIn("transitioned approved_traceable_001 to approved", transition_output)
        self.assertIn("candidate pools: 1 total, 1 rebuilt, 0 unchanged", transition_output)
        self.assertIn(
            "transitioned consumer cli_consumer to suspended",
            self.run_cli(
                "transition-consumer-status",
                "--consumer-id",
                "cli_consumer",
                "--to-status",
                "suspended",
                "--reason",
                "coverage",
            ),
        )
        self.assertIn(
            "seeded protected beta consumers: telegram_channel_deutsch_ist_einfach_quiz",
            self.run_cli("seed-protected-beta"),
        )
        self.assertIn('"action": "entitlement_grant"', self.run_cli("show-audit-log"))

    def test_cli_rebuild_candidate_pools_command_reports_idempotent_summary(self) -> None:
        self.run_cli("init-db")
        self.run_cli("seed-items", "--fixture", str(APPROVED_FIXTURE), "--status", "approved")

        summary = json.loads(
            self.run_cli(
                "rebuild-candidate-pools",
                "--bank-version-id",
                "german-core:2026-06-12-baseline",
            )
        )

        self.assertEqual(summary["pool_count"], 1)
        self.assertEqual(summary["unchanged_pool_count"], 1)

    def test_cli_seed_demo_covers_demo_reset_path(self) -> None:
        initialize_database(self.db_path)

        self.assertIn("seeded MVP demo state", self.run_cli("seed-demo"))
        seed_demo_state(self.db_path, APPROVED_FIXTURE)

        with connect(self.db_path) as connection:
            consumers = connection.execute("SELECT COUNT(*) FROM consumers").fetchone()[0]
        self.assertGreaterEqual(consumers, 3)

    def test_database_error_branches_are_explicit(self) -> None:
        self.assertFalse(database_is_ready(self.db_path))
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

        with self.assertRaisesRegex(ValueError, "unknown item_id"):
            transition_item_status(self.db_path, "missing_item", "approved", "tester", "coverage")
        with self.assertRaisesRegex(ValueError, "invalid status transition"):
            transition_item_status(
                self.db_path,
                "approved_traceable_001",
                "approved",
                "tester",
                "coverage",
            )
        with self.assertRaisesRegex(ValueError, "unknown consumer_id"):
            transition_consumer_status(self.db_path, "missing_consumer", "blocked", "tester", "coverage")

    def test_app_ready_and_response_type_guards(self) -> None:
        client = TestClient(create_app(self.db_path))
        self.assertEqual(client.get("/ready").status_code, 503)
        with self.assertRaisesRegex(TypeError, "delivery result must be a dictionary"):
            next_quiz_response("consumer", {"delivery": object(), "quiz_item": {}})

    def test_telegram_adapter_success_and_error_branches(self) -> None:
        payload = self.telegram_payload()
        adapter = TelegramBotApiAdapter(" token ", api_base="https://telegram.test/")
        ok_body = {"ok": True, "result": {"message_id": 42, "poll": {"id": "poll42"}}}
        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeHttpResponse(ok_body)
            result = adapter.send_quiz_poll(payload)
        self.assertEqual(result.message_id, "42")
        self.assertEqual(result.poll_id, "poll42")
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            TelegramBotApiAdapter(" ")
        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.URLError("network")
            with self.assertRaisesRegex(TelegramDeliveryError, "telegram_request_failed"):
                adapter.send_quiz_poll(payload)
        with patch("quizbank_mvp.telegram_bot_api.urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeHttpResponse({"ok": False, "description": "rejected"})
            with self.assertRaisesRegex(TelegramDeliveryError, "rejected"):
                adapter.send_quiz_poll(payload)

    def test_telegram_validation_and_helper_error_branches(self) -> None:
        with self.assertRaisesRegex(ValueError, "mode must"):
            validate_delivery_mode("bad")
        with self.assertRaisesRegex(TelegramDeliveryError, "requires_adapter"):
            handle_telegram_send("real", self.telegram_payload(), None)
        initialize_database(self.db_path)
        with self.assertRaisesRegex(TelegramDeliveryError, "delivery_item_not_found"):
            load_delivery_item(self.db_path, "missing", "consumer")
        for question, options, correct, explanation, expected in [
            ("x" * 301, ["a", "b"], [0], "ok", "question_too_long"),
            ("ok", ["a", "b"], [0], "x" * 201, "explanation_too_long"),
            ("ok", ["a"], [0], "ok", "option_count_invalid"),
            ("ok", ["", "b"], [0], "ok", "option_invalid"),
        ]:
            with self.assertRaisesRegex(TelegramDeliveryError, expected):
                validate_telegram_poll(question, options, correct, explanation)
        for correct_ids in ([], [1, 1], [-1], [2]):
            with self.assertRaises(TelegramDeliveryError):
                validate_correct_option_ids(list(correct_ids), 2)
        api_payload = telegram_api_payload({**self.telegram_payload(), "correct_option_ids": [0, 1]})
        self.assertEqual(api_payload["correct_option_ids"], [0, 1])
        self.assertEqual(poll_id_from_result({}), None)
        self.assertEqual(poll_id_from_result({"poll": {}}), None)
        self.assertEqual(redact_telegram_target("1234"), "***")
        public = TelegramDeliveryResult("d", "c", "i", "real", "sent", "***").to_public_dict()
        self.assertEqual(public["delivery_id"], "d")

    def test_telegram_http_error_description_branches(self) -> None:
        error = urllib.error.HTTPError(
            "https://telegram.test",
            400,
            "bad",
            {},
            io.BytesIO(b'{"description":"Bad Request"}'),
        )
        self.assertEqual(read_http_error_description(error), "Bad Request")
        invalid = urllib.error.HTTPError("https://telegram.test", 500, "bad", {}, io.BytesIO(b"{"))
        self.assertEqual(read_http_error_description(invalid), "telegram_http_error:500")

    def telegram_payload(self) -> dict[str, object]:
        item = {
            "delivery_id": "deliv_test",
            "consumer_id": "consumer_test",
            "item_id": "item_test",
            "prompt": "Welche Antwort passt?",
            "stem_text": "Lena will ___.",
            "options_json": "[\"antworten\", \"schlafen\"]",
            "answer_key": "0",
            "explanation": "Die Antwort passt zum Kontext.",
        }
        return build_telegram_poll_payload("@channel", item)


if __name__ == "__main__":
    unittest.main()
